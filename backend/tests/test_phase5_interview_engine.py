import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from uuid import uuid4
import httpx
from sqlalchemy import select

from app.database import AsyncSessionLocal, check_database_health
from app.main import app
from app.models.interview_session import InterviewSession, QuestionDifficulty, SessionStatus
from app.models.interview_turn import InterviewTurn
from app.models.user import User, UserRole
from app.models.audit_log import AuditLog
from app.services.langgraph_engine import InterviewEngine, InterviewState
from app.services.llm_service import LLMService


async def test_langgraph_state_machine_core():
    """Unit test for the full 9-node LangGraph state machine lifecycle."""
    print("\n--- Testing LangGraph Adaptive State Machine Core ---")
    llm = LLMService()
    engine = InterviewEngine(llm)

    session_id = f"test-lg-{uuid4().hex[:8]}"
    initial_state = InterviewState(
        session_id=session_id,
        user_id=str(uuid4()),
        resume_text=(
            "Senior Distributed Systems Engineer with 6 years experience in Python, FastAPI, "
            "PostgreSQL, Redis caching, microservices, and event-driven architecture."
        ),
        jd_text=(
            "Staff Platform Engineer. Requirements: Kubernetes orchestration, high-throughput Kafka "
            "event streams, distributed consensus, and zero-downtime database migrations."
        ),
        ats_skill_gaps=[
            {"skill_name": "Kubernetes", "gap_type": "missing", "jd_importance": 0.85},
            {"skill_name": "Kafka", "gap_type": "partial", "jd_importance": 0.80},
        ],
        focus_categories=["technical", "system_design"],
        target_question_count=2,
        current_turn=0,
        current_difficulty="medium",
        current_topic="Distributed Systems Architecture",
        interview_plan=[],
        topic_mastery={},
        candidate_strengths=[],
        candidate_weaknesses=[],
        conversation_history=[],
        last_question="",
        last_question_category="technical",
        last_question_rationale="",
        last_evaluation=None,
        last_eval_score=0.0,
        all_turn_scores=[],
        next_action="generate",
        is_complete=False,
        final_summary=None,
        error=None,
    )

    # 1. Initialize session and run through initial plan + question generation
    thread_id = await engine.initialize_session(session_id, initial_state)
    assert thread_id == f"session:{session_id}"
    print(f"[PASS] Session initialized with thread_id: {thread_id}")

    init_state = await engine.get_state(thread_id)
    assert len(init_state["interview_plan"]) >= 3
    assert len(init_state["topic_mastery"]) >= 3
    assert len(init_state["last_question"]) > 10
    assert init_state["current_turn"] == 0
    print(f"[PASS] Interview plan generated with {len(init_state['interview_plan'])} topics.")
    print(f"[PASS] Initial question: '{init_state['last_question']}' (topic: {init_state['current_topic']})")

    # 2. Candidate submits Turn 1 answer (High quality answer -> should upgrade difficulty to 'hard')
    strong_answer = (
        "To eliminate cache stampedes in a distributed Redis deployment, I implement a combination of "
        "probabilistic early expiration (XFetch algorithm) and distributed mutex locking using Redlock. "
        "First, before the TTL expires, background worker threads asynchronously refresh the cached key. "
        "Second, if multiple client requests detect a stale cache simultaneously, only one acquires the lock "
        "to query PostgreSQL, while others read the stale value or wait with exponential backoff, "
        "preventing cascading database saturation and maintaining sub-5ms read latency."
    )
    res_turn1 = await engine.submit_answer(thread_id, strong_answer)
    assert res_turn1["turn"] == 1
    eval1 = res_turn1["evaluation"]
    assert eval1 is not None
    assert eval1["overall_score"] >= 75.0
    assert eval1["technical_accuracy"] >= 75.0
    assert eval1["concept_understanding"] >= 75.0
    assert len(eval1["strengths"]) > 0
    assert res_turn1["difficulty"] == "hard"  # Difficulty upgraded from medium to hard!
    assert res_turn1["is_complete"] is False
    print(f"[PASS] Turn 1 evaluated: overall_score={eval1['overall_score']}, difficulty upgraded to '{res_turn1['difficulty']}'.")

    # 3. Candidate submits Turn 2 answer (Lower quality answer -> completes target count = 2)
    weaker_answer = "I would just put a lock on the database and restart the pod if it crashes."
    res_turn2 = await engine.submit_answer(thread_id, weaker_answer)
    assert res_turn2["turn"] == 2
    assert res_turn2["is_complete"] is True
    eval2 = res_turn2["evaluation"]
    assert eval2 is not None
    assert eval2["overall_score"] < 65.0
    assert len(res_turn2["candidate_weaknesses"]) > 0

    # Validate final Bar Raiser summary
    summary = res_turn2["final_summary"]
    assert summary is not None
    assert "hiring_recommendation" in summary
    assert summary["overall_score"] > 0
    assert len(summary["key_strengths"]) > 0
    assert len(summary["growth_areas"]) > 0
    print(f"[PASS] Turn 2 evaluated and interview completed: {summary['hiring_recommendation']} (Score: {summary['overall_score']})")


async def test_interview_api_endpoints():
    """Integration test verifying full HTTP API lifecycle, database persistence, and audit logs."""
    print("\n--- Testing Interview HTTP API Endpoints & Multi-Tenancy ---")
    db_ok = await check_database_health()
    if not db_ok:
        print("[SKIP] PostgreSQL not connected in this test run.")
        return

    # Seed test user
    test_email = f"lead-candidate-{uuid4().hex[:6]}@example.com"
    raw_pwd = "EnterprisePassword2026!"

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Register & Login
        reg_res = await client.post(
            "/api/v1/auth/register",
            json={"email": test_email, "full_name": "Devin Candidate", "password": raw_pwd},
        )
        assert reg_res.status_code == 201

        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": test_email, "password": raw_pwd},
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Create Interview Session
        create_res = await client.post(
            "/api/v1/interview/session",
            headers=headers,
            json={
                "target_question_count": 2,
                "focus_categories": ["technical", "system_design"],
                "starting_difficulty": "medium",
                "adaptive_mode": True,
            },
        )
        assert create_res.status_code == 201
        session_data = create_res.json()
        session_id = session_data["id"]
        assert session_data["status"] == "active"
        assert session_data["current_difficulty"] == "medium"
        assert session_data["current_question_index"] == 0
        print(f"[PASS] Interview session created via API: {session_id}")

        # 3. Inspect Live LangGraph State
        state_res = await client.get(
            f"/api/v1/interview/session/{session_id}/state",
            headers=headers,
        )
        assert state_res.status_code == 200
        state_data = state_res.json()
        assert len(state_data["interview_plan"]) >= 3
        assert state_data["last_question"] is not None
        assert state_data["is_complete"] is False
        print(f"[PASS] Session live state retrieved. Current topic: {state_data['current_topic']}")

        # 4. Submit Answer for Turn 0 (Text Mode)
        ans1_res = await client.post(
            "/api/v1/interview/answer",
            headers=headers,
            json={
                "session_id": session_id,
                "turn_index": 0,
                "answer_text": (
                    "In our production microservices architecture, we deploy Redis cluster with Sentinel "
                    "for automated failover. We configure key expiration with jitter and use a distributed lock "
                    "pattern to synchronize cache rebuilding across instances during heavy load spikes."
                ),
            },
        )
        assert ans1_res.status_code == 200
        ans1_data = ans1_res.json()
        assert ans1_data["turn_index"] == 1
        assert ans1_data["is_complete"] is False
        assert ans1_data["evaluation"]["overall_score"] >= 70.0
        assert ans1_data["evaluation"]["technical_accuracy"] >= 70.0
        assert ans1_data["evaluation"]["concept_understanding"] >= 70.0
        print(f"[PASS] Turn 0 submitted. Next question generated: '{ans1_data['question_text'][:60]}...'")

        # 5. Verify Turn Persisted in DB
        turns_res = await client.get(
            f"/api/v1/interview/session/{session_id}/turns",
            headers=headers,
        )
        assert turns_res.status_code == 200
        turns_list = turns_res.json()
        assert len(turns_list) == 1
        assert turns_list[0]["turn_index"] == 0
        assert turns_list[0]["eval_scores"] is not None
        assert "technical_accuracy" in turns_list[0]["eval_scores"]
        print("[PASS] Interview turn DB persistence and rubric breakdown verified.")

        # 6. Submit Answer for Turn 1 -> Triggers Completion
        ans2_res = await client.post(
            "/api/v1/interview/answer",
            headers=headers,
            json={
                "session_id": session_id,
                "turn_index": 1,
                "answer_text": (
                    "We use Kafka with transactional outbox pattern to ensure exactly-once semantics. "
                    "Consumer offsets are committed only after the database write succeeds in the local transaction."
                ),
            },
        )
        assert ans2_res.status_code == 200
        ans2_data = ans2_res.json()
        assert ans2_data["is_complete"] is True
        assert ans2_data["final_summary"] is not None
        assert ans2_data["final_summary"]["overall_score"] >= 70.0
        print(f"[PASS] Turn 1 submitted. Session finalized with recommendation: {ans2_data['final_summary']['hiring_recommendation']}")

        # 7. Verify Completed Session in DB
        sess_check = await client.get(
            f"/api/v1/interview/session/{session_id}",
            headers=headers,
        )
        assert sess_check.status_code == 200
        assert sess_check.json()["status"] == "completed"
        assert sess_check.json()["aggregate_score"] is not None
        print(f"[PASS] Session status completed with aggregate_score={sess_check.json()['aggregate_score']}")

        # 8. Verify Audit Logs Recorded
        async with AsyncSessionLocal() as session:
            audit_res = await session.execute(
                select(AuditLog).where(
                    AuditLog.entity_id.in_([session_id, str(turns_list[0]["id"])]),
                )
            )
            audit_logs = list(audit_res.scalars().all())
            actions = [a.action for a in audit_logs]
            assert "interview.session_created" in actions
            assert "interview.turn_completed" in actions
            print(f"[PASS] Audit logs verified for interview lifecycle: {actions}")


async def run_all():
    print("=== RUNNING PHASE 5 ADAPTIVE INTERVIEW ENGINE TESTS ===")
    await test_langgraph_state_machine_core()
    await test_interview_api_endpoints()
    print("=== ALL PHASE 5 TESTS PASSED SUCCESSFULLY ===")


if __name__ == "__main__":
    asyncio.run(run_all())
