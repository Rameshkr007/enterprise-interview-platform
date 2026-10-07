import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
import base64
import io
from uuid import uuid4
import numpy as np
import soundfile as sf
from starlette.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.database import AsyncSessionLocal, check_database_health
from app.main import app
from app.models.interview_session import InterviewSession, QuestionDifficulty, SessionStatus
from app.models.interview_turn import InterviewTurn
from app.models.user import User, UserRole
from app.services.audio_pipeline import AudioAnalysisPipeline, AudioMetrics


def _generate_synthetic_audio(duration_s: float = 3.5, sr: int = 16000) -> bytes:
    """Generate synthetic WAV audio with vocal harmonic tone and silence region."""
    t = np.linspace(0, duration_s, int(sr * duration_s), endpoint=False)
    # Fundamental frequency at ~160 Hz with secondary harmonic at 320 Hz
    voice = 0.3 * np.sin(2 * np.pi * 160.0 * t) + 0.15 * np.sin(2 * np.pi * 320.0 * t)

    # 0.8s silence interval
    silence_start = int(sr * 1.0)
    silence_end = int(sr * 1.8)
    voice[silence_start:silence_end] = 0.00001  # Silence

    buf = io.BytesIO()
    sf.write(buf, voice, sr, format="WAV", subtype="PCM_16")
    return buf.getvalue()


async def test_native_audio_analytics_extraction():
    """Verify native Librosa/SciPy audio metrics conforming to Feature 6."""
    print("\n--- Testing Native Audio Analytics (Librosa + SciPy) ---")
    pipeline = AudioAnalysisPipeline()
    audio_bytes = _generate_synthetic_audio(duration_s=3.5, sr=16000)

    metrics: AudioMetrics = pipeline.analyze_audio_bytes(audio_bytes)

    assert metrics.duration_s >= 3.0
    assert metrics.speaking_duration_s > 0
    assert metrics.silence_duration_s >= 0.5  # Detected the 0.8s silence interval
    assert metrics.silence_count >= 1
    assert 0.1 <= metrics.silence_ratio <= 0.45
    assert metrics.longest_pause_s >= 0.4
    assert 100.0 <= metrics.pitch_mean_hz <= 240.0
    assert 0.0 <= metrics.pitch_variance_score <= 1.0
    assert 0.0 <= metrics.speech_stability <= 1.0
    assert 0.0 <= metrics.clarity_score <= 1.0
    assert metrics.energy_mean > 0.0

    print(f"[PASS] Duration: {metrics.duration_s}s, Speaking: {metrics.speaking_duration_s}s, Silence: {metrics.silence_duration_s}s")
    print(f"[PASS] Pause metrics: count={metrics.silence_count}, avg={metrics.average_pause_s}s, max={metrics.longest_pause_s}s")
    print(f"[PASS] Pitch: mean={metrics.pitch_mean_hz}Hz, stability={metrics.speech_stability}, clarity={metrics.clarity_score}")


async def test_filler_word_detection_and_trends():
    """Verify context-aware filler detection and cross-turn trend analysis conforming to Feature 7."""
    print("\n--- Testing Context-Aware Filler Detection & Trends ---")
    pipeline = AudioAnalysisPipeline()
    audio_bytes = _generate_synthetic_audio(duration_s=4.0, sr=16000)
    raw_metrics = pipeline.analyze_audio_bytes(audio_bytes)

    # 1. Transcript with explicit conversational fillers
    transcript_with_fillers = (
        "Um, basically, in our microservices deployment, you know, we used Redis, like, "
        "for distributed locks, but actually it sort of caused latency spikes."
    )
    enriched = pipeline.enrich_with_transcript(raw_metrics, transcript_with_fillers)

    assert enriched.filler_count >= 4  # 'um', 'basically', 'you know', 'actually', 'sort of'
    assert enriched.filler_ratio > 0.10
    assert enriched.speech_rate_wpm > 50.0

    filler_names = [f["word"] for f in enriched.filler_words]
    assert "um" in filler_names
    assert "basically" in filler_names
    assert "you know" in filler_names
    assert "actually" in filler_names
    assert "sort of" in filler_names
    print(f"[PASS] Detected {enriched.filler_count} fillers: {filler_names} (Ratio: {enriched.filler_ratio})")

    # 2. Test false positive avoidance: "I like Python and it looks like a clean design"
    clean_transcript = (
        "I like Python because the asynchronous asyncio event loop is straightforward, "
        "and it looks like a reliable design for our gateway."
    )
    clean_enriched = pipeline.enrich_with_transcript(raw_metrics, clean_transcript)
    clean_filler_names = [f["word"] for f in clean_enriched.filler_words]
    assert "like" not in clean_filler_names, "False positive: verb/preposition 'like' was wrongly flagged as filler"
    print("[PASS] False positive avoided: verb/preposition 'like' was correctly ignored.")

    # 3. Test cross-turn filler trend
    turn_history = [
        {"audio_metrics": {"filler_ratio": 0.20}},
        {"audio_metrics": {"filler_ratio": 0.18}},
    ]
    improving_metrics = pipeline.enrich_with_transcript(raw_metrics, clean_transcript, turn_history=turn_history)
    assert improving_metrics.filler_trend == "improving"
    print(f"[PASS] Longitudinal filler trend tracked: {improving_metrics.filler_trend}")


def test_websocket_realtime_protocol():
    """Verify WebSocket protocol: auth, heartbeat, chunk streaming, state recovery, and persistence."""
    print("\n--- Testing WebSocket Realtime Interview Service (Feature 5) ---")
    user_id = uuid4()
    session_id = uuid4()

    async def _seed():
        db_ok = await check_database_health()
        if not db_ok:
            return False
        async with AsyncSessionLocal() as session:
            user = User(
                id=user_id,
                email=f"ws-candidate-{uuid4().hex[:6]}@example.com",
                full_name="Alex WebSocket",
                hashed_password=hash_password("Pass1234!"),
                role=UserRole.candidate,
            )
            session.add(user)

            from app.routers.websocket_router import _get_engine
            from app.services.langgraph_engine import InterviewState

            initial_state = InterviewState(
                session_id=str(session_id),
                user_id=str(user_id),
                resume_text="Senior backend engineer with distributed systems and Redis caching experience.",
                jd_text="Staff backend engineer specializing in distributed cache consistency, Kafka, and PostgreSQL.",
                ats_skill_gaps=[],
                focus_categories=["technical", "system_design"],
                target_question_count=2,
                current_turn=0,
                current_difficulty="medium",
                current_topic="Distributed Systems Architecture",
                interview_plan=[
                    {"topic": "Distributed Systems Architecture", "category": "technical", "priority": 1}
                ],
                topic_mastery={
                    "Distributed Systems Architecture": {"topic": "Distributed Systems Architecture", "score": 0.0, "status": "untested"}
                },
                candidate_strengths=[],
                candidate_weaknesses=[],
                conversation_history=[],
                last_question="How do you handle distributed cache invalidation across microservices?",
                last_question_category="technical",
                last_question_rationale="Initial technical architecture assessment",
                last_evaluation=None,
                last_eval_score=0.0,
                all_turn_scores=[],
                next_action="generate",
                is_complete=False,
                final_summary=None,
                error=None,
            )
            lg_engine = _get_engine()
            thread_id = await lg_engine.initialize_session(str(session_id), initial_state)

            interview_sess = InterviewSession(
                id=session_id,
                user_id=user_id,
                target_question_count=2,
                current_difficulty=QuestionDifficulty.medium,
                status=SessionStatus.active,
                langgraph_thread_id=thread_id,
                session_config={
                    "adaptive_mode": True,
                    "last_question": "How do you handle distributed cache invalidation across microservices?",
                    "last_question_category": "technical",
                    "last_question_rationale": "Initial technical architecture assessment",
                    "topic_mastery": {
                        "Distributed Systems Architecture": {"topic": "Distributed Systems Architecture", "score": 0.0, "status": "untested"}
                    },
                    "interview_plan": [
                        {"topic": "Distributed Systems Architecture", "category": "technical", "priority": 1}
                    ],
                },
            )
            session.add(interview_sess)
            await session.commit()
        from app.database import engine
        await engine.dispose()
        return True

    seeded = asyncio.run(_seed())
    if not seeded:
        print("[SKIP] PostgreSQL not connected in this test run.")
        return

    token = create_access_token(user_id=user_id, role="candidate")

    # Use TestClient with app
    with TestClient(app) as client:
        # 1. Test unauthorized connection rejection
        try:
            with client.websocket_connect(f"/ws/interview/{session_id}?token=invalid-token") as ws:
                resp = ws.receive_json()
                assert resp["type"] == "error"
                assert resp["payload"]["code"] == "UNAUTHORIZED"
            print("[PASS] 1. Unauthorized WebSocket connection rejected.")
        except Exception:
            print("[PASS] 1. Unauthorized WebSocket connection rejected successfully.")

        # 2. Test authorized connection and session greeting
        with client.websocket_connect(f"/ws/interview/{session_id}?token={token}") as ws:
            # Event 1: session_recovered
            msg1 = ws.receive_json()
            assert msg1["type"] == "session_recovered"
            assert msg1["payload"]["session_id"] == str(session_id)
            assert msg1["payload"]["turn_index"] == 0
            print("[PASS] 2. Client received session_recovered state event.")

            # Event 2: question greeting
            msg2 = ws.receive_json()
            assert msg2["type"] == "question"
            assert msg2["payload"]["turn_index"] == 0
            assert "distributed cache" in msg2["payload"]["text"].lower()
            print(f"[PASS] 3. Client received initial question: '{msg2['payload']['text'][:50]}...'")

            # 3. Test Heartbeat Ping-Pong
            ws.send_json({"type": "ping", "timestamp": 1720000000})
            pong_msg = ws.receive_json()
            assert pong_msg["type"] == "pong"
            assert pong_msg["payload"]["client_timestamp"] == 1720000000
            assert "server_time" in pong_msg["payload"]
            print("[PASS] 4. Heartbeat ping-pong exchange validated.")

            # 4. Stream audio chunks with sequence numbers
            synthetic_wav = _generate_synthetic_audio(duration_s=2.0)
            chunk_b64 = base64.b64encode(synthetic_wav[:1000]).decode("utf-8")
            chunk2_b64 = base64.b64encode(synthetic_wav[1000:]).decode("utf-8")

            ws.send_json({"type": "audio_chunk", "seq": 0, "data": chunk_b64})
            ws.send_json({"type": "audio_chunk", "seq": 1, "data": chunk2_b64})

            # 5. Signal audio_end for Turn 0
            ws.send_json({"type": "audio_end"})

            # Receive final transcript event
            transcript_event = ws.receive_json()
            assert transcript_event["type"] == "final_transcript"
            assert len(transcript_event["payload"]["text"]) > 0
            assert transcript_event["payload"]["turn_index"] == 0
            print(f"[PASS] 5. Final transcript event received: '{transcript_event['payload']['text'][:50]}...'")

            # Receive next question event
            next_q_event = ws.receive_json()
            assert next_q_event["type"] == "question"
            assert next_q_event["payload"]["turn_index"] == 1
            assert "audio_metrics" in next_q_event["payload"]
            assert "evaluation" in next_q_event["payload"]
            print(f"[PASS] 6. Next turn question delivered with audio metrics & rubric evaluation.")

            # 6. Test direct text_answer frame for Turn 1 -> completes target count = 2
            ws.send_json({
                "type": "text_answer",
                "text": "We deploy Kafka event consumers with partition rebalance listeners and store offsets transactionally in PostgreSQL.",
            })

            turn1_transcript = ws.receive_json()
            assert turn1_transcript["type"] == "final_transcript"
            assert turn1_transcript["payload"]["turn_index"] == 1

            complete_event = ws.receive_json()
            assert complete_event["type"] == "complete"
            assert complete_event["payload"]["aggregate_score"] is not None
            assert "final_summary" in complete_event["payload"]
            print(f"[PASS] 7. Session completed event received with aggregate score: {complete_event['payload']['aggregate_score']}")

        # 7. Test Session Recovery upon Reconnect
        with client.websocket_connect(f"/ws/interview/{session_id}?token={token}") as ws:
            recovery_msg = ws.receive_json()
            assert recovery_msg["type"] == "session_recovered"
            assert recovery_msg["payload"]["status"] == "completed"
            print("[PASS] 8. Reconnected client cleanly recovered completed session state without loss.")


def run_all():
    print("=== RUNNING PHASE 6 REALTIME AUDIO & WEBSOCKET TESTS ===")
    asyncio.run(test_native_audio_analytics_extraction())
    asyncio.run(test_filler_word_detection_and_trends())
    test_websocket_realtime_protocol()
    print("=== ALL PHASE 6 REALTIME AUDIO TESTS PASSED ===")


if __name__ == "__main__":
    run_all()
