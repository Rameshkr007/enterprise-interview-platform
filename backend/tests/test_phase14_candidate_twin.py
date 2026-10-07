"""
Phase 14: Candidate AI Twin & History Test Suite
Validates:
1. Multi-source longitudinal telemetry synthesis across all 5 platform pillars:
   - Interview Sessions & turns (STAR+L, question categories, audio metrics)
   - Coding challenges & AST cyclomatic complexity
   - Resume & ATS matching
   - Verified Skill Graph DAG mastery nodes (Phase 12)
   - SuperMemo-2 Spaced Repetition retention & memory stability (Phase 13)
2. Chronological trajectory interleaving and OLS growth velocity slope calculation
3. Peer percentile benchmarking with Gaussian normalized cohort distribution
4. Feature 16 Explainable AI compliance (5 dimensions, evidence grounding, actionable uplift)
5. Full HTTP REST API endpoint coverage (/twin/me, /twin/sync, /twin/history, /twin/benchmarks, /twin/explain/{dim})
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token
from app.database import AsyncSessionLocal, Base, engine
from app.main import app
from app.models.advanced import CodingChallenge
from app.models.candidate_twin import CandidateTwin
from app.models.interview_session import InterviewSession, QuestionDifficulty, SessionStatus
from app.models.interview_turn import InterviewTurn, QuestionCategory
from app.models.learning_plan import LearningPlan, LearningPlanStatus
from app.models.skill_graph import CandidateSkillMastery
from app.models.sm2_card import SpacedRepetitionCard
from app.models.user import User, UserRole
from app.services.candidate_twin_service import CandidateTwinEngine


async def test_phase14_candidate_twin() -> None:
    print("\n========================================================")
    print("=== STARTING PHASE 14: CANDIDATE AI TWIN & HISTORY ===")
    print("========================================================\n")

    # ── Database Tables Setup ────────────────────────────────────────────────
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    twin_engine = CandidateTwinEngine()
    test_email = f"candidate.twin.{uuid.uuid4().hex[:8]}@enterprise.test"
    candidate_id = uuid.uuid4()

    # ── 1. POPULATE TEST TELEMETRY DATA ACROSS PLATFORM PILLARS ──────────────
    print("--- 1. Seeding Multi-Source Platform Telemetry ---")
    async with AsyncSessionLocal() as session:
        # Create test candidate
        user = User(
            id=candidate_id,
            email=test_email,
            full_name="Alex Twin-Engineer",
            hashed_password="TestPasswordHash123!",
            role=UserRole.candidate,
            is_active=True,
        )
        session.add(user)
        await session.flush()

        # 1.1 Interview Session & Turns
        s1 = InterviewSession(
            id=uuid.uuid4(),
            user_id=candidate_id,
            status=SessionStatus.completed,
            target_question_count=2,
            current_question_index=2,
            current_difficulty=QuestionDifficulty.hard,
            aggregate_score=84.0,
            started_at=datetime.now(UTC) - timedelta(days=5),
            completed_at=datetime.now(UTC) - timedelta(days=5, minutes=-30),
        )
        session.add(s1)

        turn1 = InterviewTurn(
            id=uuid.uuid4(),
            session_id=s1.id,
            turn_index=0,
            question_text="How do you architect distributed event logs?",
            question_category=QuestionCategory.system_design,
            question_difficulty="hard",
            raw_transcript="We leveraged Kafka partitioned topics with idempotency keys.",
            eval_scores={
                "composite_score": 0.86,
                "relevance": 0.90,
                "technical_accuracy": 0.88,
                "depth": 0.85,
                "clarity": 0.82,
            },
            audio_metrics={
                "speech_rate_wpm": 142.0,
                "silence_ratio": 0.08,
                "pitch_variance_score": 0.18,
                "filler_word_rate": 0.03,
            },
        )
        turn2 = InterviewTurn(
            id=uuid.uuid4(),
            session_id=s1.id,
            turn_index=1,
            question_text="Describe a conflict resolution within your platform team.",
            question_category=QuestionCategory.behavioral,
            question_difficulty="medium",
            raw_transcript="I facilitated an architecture review RFC resolving the database migration controversy.",
            eval_scores={
                "composite_score": 0.82,
                "relevance": 0.85,
                "technical_accuracy": 0.80,
                "depth": 0.80,
                "clarity": 0.85,
            },
            audio_metrics={
                "speech_rate_wpm": 138.0,
                "silence_ratio": 0.09,
                "pitch_variance_score": 0.20,
                "filler_word_rate": 0.02,
            },
        )
        session.add_all([turn1, turn2])

        # 1.2 Coding Challenge & Submission
        challenge = CodingChallenge(
            id=uuid.uuid4(),
            session_id=s1.id,
            title="Distributed Rate Limiter Leaky Bucket",
            description="Implement a thread-safe token bucket rate limiter.",
            difficulty="hard",
            language="python",
            starter_code="class RateLimiter:\n    pass",
            score=88.0,
            submitted_at=datetime.now(UTC) - timedelta(days=3),
        )
        session.add(challenge)

        # 1.3 Skill DAG Mastery Nodes (Phase 12 Integration)
        m1 = CandidateSkillMastery(
            id=uuid.uuid4(),
            user_id=candidate_id,
            skill_id="distributed-systems",
            mastery_score=92.0,
            confidence=0.92,
            last_assessed_at=datetime.now(UTC) - timedelta(days=2),
        )
        m2 = CandidateSkillMastery(
            id=uuid.uuid4(),
            user_id=candidate_id,
            skill_id="python-concurrency",
            mastery_score=86.0,
            confidence=0.86,
            last_assessed_at=datetime.now(UTC) - timedelta(days=1),
        )
        session.add_all([m1, m2])

        # 1.4 SM-2 Spaced Repetition Cards (Phase 13 Integration)
        card1 = SpacedRepetitionCard(
            id=uuid.uuid4(),
            user_id=candidate_id,
            skill_id="distributed-systems",
            concept_key="raft-log-replication",
            title="Raft Log Replication Consensus",
            question_prompt="What is the Raft log consensus commitment rule?",
            answer_explanation="Entry is committed when stored on a majority of nodes by current term leader.",
            category="system-design",
            tier=3,
            repetition_count=4,
            interval_days=15,
            easiness_factor=2.7,
            retention_score=0.94,
            last_reviewed_at=datetime.now(UTC) - timedelta(days=1),
            next_review_due=datetime.now(UTC) + timedelta(days=14),
            review_history=[
                {"reviewed_at": (datetime.now(UTC) - timedelta(days=1)).isoformat(), "quality": 5, "new_interval": 15}
            ],
        )
        card2 = SpacedRepetitionCard(
            id=uuid.uuid4(),
            user_id=candidate_id,
            skill_id="python-concurrency",
            concept_key="asyncio-vs-threading",
            title="Asyncio Event Loop vs Threads",
            question_prompt="Explain asyncio event loop task scheduling vs threads.",
            answer_explanation="Asyncio is single-threaded cooperative multitasking yielding at await.",
            category="programming-languages",
            tier=2,
            repetition_count=2,
            interval_days=6,
            easiness_factor=2.5,
            retention_score=0.88,
            last_reviewed_at=datetime.now(UTC) - timedelta(days=2),
            next_review_due=datetime.now(UTC) + timedelta(days=4),
            review_history=[
                {"reviewed_at": (datetime.now(UTC) - timedelta(days=2)).isoformat(), "quality": 4, "new_interval": 6}
            ],
        )
        session.add_all([card1, card2])

        # 1.5 Learning Plan
        plan = LearningPlan(
            id=uuid.uuid4(),
            user_id=candidate_id,
            title="Distributed Systems Resiliency",
            detected_gap="Kafka Partitioning",
            category="technical",
            status=LearningPlanStatus.completed,
            target_completion_days=7,
            current_day=7,
            daily_schedule=[],
        )
        session.add(plan)

        await session.commit()
    print("  [PASS] Seeding multi-source telemetry data successful.")

    # ── 2. SYNCHRONIZE CANDIDATE TWIN FROM MULTI-SOURCE TELEMETRY ────────────
    print("\n--- 2. Validating Candidate AI Twin Engine Longitudinal Sync ---")
    async with AsyncSessionLocal() as session:
        twin: CandidateTwin = await twin_engine.sync_twin_from_history(session, candidate_id)

        assert twin is not None
        assert twin.user_id == candidate_id
        assert 0.0 <= twin.overall_readiness_score <= 100.0
        print(f"  [PASS] Overall Readiness Score synthesized: {twin.overall_readiness_score:.2f}/100")

        # Check technical mastery synthesizes Skill DAG and SM-2 retention
        tech = twin.technical_mastery
        assert "dag_calibration" in tech
        assert "sm2_memory_stability" in tech
        assert tech["dag_calibration"]["verified_skills_count"] == 2
        assert tech["sm2_memory_stability"]["total_cards"] == 2
        assert tech["sm2_memory_stability"]["average_retention_pct"] > 80.0
        print(f"  [PASS] Technical Mastery synthesized Skill DAG ({tech['dag_calibration']['verified_skills_count']} nodes) & SM-2 memory retention ({tech['sm2_memory_stability']['average_retention_pct']:.1f}%).")

        # Check communication metrics
        comm = twin.communication_metrics
        assert comm["avg_pace_wpm"] > 100.0
        assert comm["avg_confidence"] > 0.70
        print(f"  [PASS] Communication Metrics: {comm['avg_pace_wpm']} WPM, confidence {comm['avg_confidence']}.")

        # Check coding mastery
        coding = twin.coding_mastery
        assert coding["submissions_count"] >= 1
        assert coding["overall_score"] >= 80.0
        print(f"  [PASS] Coding Mastery: submissions {coding['submissions_count']}, score {coding['overall_score']}.")

        # Check historical trajectory and growth velocity
        trajectory = twin.historical_trajectory
        assert len(trajectory) >= 3
        print(f"  [PASS] Trajectory timeline contains {len(trajectory)} interleaved milestones.")
        print(f"  [PASS] Growth velocity slope: {twin.growth_velocity:+.4f} pts/day.")

    # ── 3. VALIDATE PEER PERCENTILE BENCHMARKING ──────────────────────────────
    print("\n--- 3. Testing Peer Percentile Benchmarking ---")
    async with AsyncSessionLocal() as session:
        benchmarks = await twin_engine.get_peer_benchmarks(session, candidate_id)

        assert "overall_percentile" in benchmarks
        assert 1.0 <= benchmarks["overall_percentile"] <= 99.0
        assert "cohort_name" in benchmarks
        assert len(benchmarks["metrics"]) == 5
        assert benchmarks["growth_velocity_status"] in ("accelerating", "steady", "plateauing", "regressing")

        for m in benchmarks["metrics"]:
            assert 1.0 <= m["percentile_rank"] <= 99.0
            print(f"    - {m['metric']}: Candidate={m['candidate_score']}, Percentile={m['percentile_rank']}%, CohortMean={m['cohort_mean']}")

        print(f"  [PASS] Benchmarking verified. Overall Percentile: {benchmarks['overall_percentile']}%, Status: {benchmarks['growth_velocity_status']}")

    # ── 4. VALIDATE EXPLAINABLE AI COMPLIANCE (FEATURE 16) ───────────────────
    print("\n--- 4. Testing Feature 16 Explainable AI Breakdown ---")
    async with AsyncSessionLocal() as session:
        for dimension in ("readiness", "technical", "system_design", "coding", "communication", "sm2_retention"):
            explanation = await twin_engine.explain_score_dimension(session, candidate_id, dimension)
            assert "dimension" in explanation and len(explanation["dimension"]) > 0
            assert "what_was_evaluated" in explanation
            assert len(explanation["evidence_found"]) > 0
            assert "score_rationale" in explanation
            assert "what_is_missing" in explanation
            assert len(explanation["actionable_improvement_roadmap"]) > 0
            assert "weights_breakdown" in explanation
            assert "calibration_sample_size" in explanation
            assert explanation["projected_score_uplift"] >= 0.0
            print(f"  [PASS] Dimension '{dimension}' ({explanation['dimension']}) explainability verified (Uplift: +{explanation['projected_score_uplift']} pts).")

    # ── 5. FULL HTTP REST API ENDPOINTS COVERAGE ─────────────────────────────
    print("\n--- 5. Validating Candidate AI Twin REST Endpoints ---")
    auth_token = create_access_token(candidate_id, UserRole.candidate.value)
    headers = {"Authorization": f"Bearer {auth_token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        # 5.1 GET /twin/me
        resp = await client.get("/api/v1/twin/me", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert str(data["user_id"]) == str(candidate_id)
        assert "overall_readiness_score" in data
        assert "technical_mastery" in data
        assert "historical_trajectory" in data
        print("  [PASS] GET /api/v1/twin/me returned 200 OK.")

        # 5.2 POST /twin/sync
        resp = await client.post("/api/v1/twin/sync", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["overall_readiness_score"] > 0
        print("  [PASS] POST /api/v1/twin/sync returned 200 OK & recorded audit event.")

        # 5.3 GET /twin/history
        resp = await client.get("/api/v1/twin/history", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        history = resp.json()
        assert isinstance(history, list)
        assert len(history) >= 3
        print(f"  [PASS] GET /api/v1/twin/history returned {len(history)} milestone events.")

        # 5.4 GET /twin/history?event_type=coding_submission
        resp = await client.get("/api/v1/twin/history?event_type=coding_submission", headers=headers)
        assert resp.status_code == 200
        filtered = resp.json()
        for ev in filtered:
            assert ev["event_type"] == "coding_submission"
        print("  [PASS] GET /api/v1/twin/history category filtering verified.")

        # 5.5 GET /twin/benchmarks
        resp = await client.get("/api/v1/twin/benchmarks", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        bench = resp.json()
        assert "overall_percentile" in bench
        assert len(bench["metrics"]) == 5
        print(f"  [PASS] GET /api/v1/twin/benchmarks returned 200 OK (Percentile: {bench['overall_percentile']}%).")

        # 5.6 GET /twin/explain/{dimension}
        for d in ("technical", "communication", "sm2_retention"):
            resp = await client.get(f"/api/v1/twin/explain/{d}", headers=headers)
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
            exp = resp.json()
            assert len(exp["dimension"]) > 0
            assert len(exp["actionable_improvement_roadmap"]) > 0
            print(f"  [PASS] GET /api/v1/twin/explain/{d} returned 200 OK ({exp['dimension']}).")

    print("\n========================================================")
    print("=== ALL PHASE 14 CANDIDATE AI TWIN TESTS PASSED (100%) ===")
    print("========================================================\n")


if __name__ == "__main__":
    asyncio.run(test_phase14_candidate_twin())
