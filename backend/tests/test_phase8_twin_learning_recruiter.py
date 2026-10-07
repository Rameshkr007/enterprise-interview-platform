import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4


from httpx import ASGITransport, AsyncClient
from sqlalchemy import select


from app.core.security import create_access_token, hash_password
from app.database import AsyncSessionLocal, check_database_health
from app.main import app
from app.models.advanced import CodingChallenge
from app.models.audit_log import AuditLog
from app.models.candidate_twin import CandidateTwin
from app.models.interview_session import InterviewSession, QuestionDifficulty, SessionStatus
from app.models.interview_turn import InterviewTurn, QuestionCategory
from app.models.learning_plan import LearningPlan, LearningPlanStatus
from app.models.organization import Organization
from app.models.recruiter import CandidateStage, RecruiterRequisition, RequisitionCandidate, RequisitionStatus
from app.models.user import User, UserRole
from app.services.candidate_twin_service import CandidateTwinEngine
from app.services.learning_engine import PersonalizedLearningEngine
from app.services.recruiter_copilot_service import RecruiterCopilotService


async def test_phase8_twin_learning_recruiter_complete() -> None:
    print("\n=== RUNNING PHASE 8 CANDIDATE AI TWIN, LEARNING ENGINE & RECRUITER COPILOT TESTS ===")
    assert await check_database_health() is True


    learning_engine = PersonalizedLearningEngine()
    twin_engine = CandidateTwinEngine()
    recruiter_service = RecruiterCopilotService()

    async with AsyncSessionLocal() as db:
        # Create test organization
        org = Organization(name="MetaTech Enterprise Systems", slug=f"metatech-{uuid4().hex[:6]}")
        db.add(org)
        await db.flush()

        # Create candidate user
        candidate_pwd = hash_password("CandidateSecure123!")
        candidate = User(
            email=f"candidate_{uuid4().hex[:6]}@example.com",
            full_name="Alex Mercer",
            hashed_password=candidate_pwd,
            role=UserRole.candidate,
            org_id=org.id,
        )
        # Create second candidate user for comparison
        candidate2 = User(
            email=f"candidate2_{uuid4().hex[:6]}@example.com",
            full_name="Jordan Vance",
            hashed_password=candidate_pwd,
            role=UserRole.candidate,
            org_id=org.id,
        )
        # Create recruiter user
        recruiter_pwd = hash_password("RecruiterSecure123!")
        recruiter = User(
            email=f"recruiter_{uuid4().hex[:6]}@example.com",
            full_name="Sarah Connor (Lead Recruiter)",
            hashed_password=recruiter_pwd,
            role=UserRole.recruiter,
            org_id=org.id,
        )
        db.add_all([candidate, candidate2, recruiter])
        await db.flush()
        await db.commit()

        candidate_id = candidate.id
        candidate2_id = candidate2.id
        recruiter_id = recruiter.id
        org_id = org.id

    # ── 1. Seed Multi-Session Historical Data for Candidate 1 ──────────────────
    async with AsyncSessionLocal() as db:
        # Session 1 (Initial baseline: score 72.0)
        s1 = InterviewSession(
            user_id=candidate_id,
            status=SessionStatus.completed,
            target_question_count=2,
            current_difficulty=QuestionDifficulty.medium,
            aggregate_score=72.0,
            started_at=datetime(2026, 9, 1, tzinfo=UTC),
            completed_at=datetime(2026, 9, 1, tzinfo=UTC),
        )
        db.add(s1)
        await db.flush()

        t1 = InterviewTurn(
            session_id=s1.id,
            turn_index=0,
            question_text="How do you handle query performance on large tables in PostgreSQL?",
            question_category=QuestionCategory.technical,
            question_difficulty="medium",
            raw_transcript="We usually just add indexes on all columns or rewrite queries.",
            eval_scores={"composite_score": 0.58, "relevance": 0.6, "depth": 0.5},
            audio_metrics={"speech_rate_wpm": 128.0, "filler_ratio": 0.05, "clarity": 0.76},
        )
        db.add(t1)

        # Session 2 (Follow-up interview: score 84.0 - demonstrating growth)
        s2 = InterviewSession(
            user_id=candidate_id,
            status=SessionStatus.completed,
            target_question_count=2,
            current_difficulty=QuestionDifficulty.hard,
            aggregate_score=84.0,
            started_at=datetime(2026, 9, 15, tzinfo=UTC),
            completed_at=datetime(2026, 9, 15, tzinfo=UTC),
        )
        db.add(s2)
        await db.flush()

        t2 = InterviewTurn(
            session_id=s2.id,
            turn_index=0,
            question_text="Design a distributed caching architecture using Redis with cache stampede protection.",
            question_category=QuestionCategory.system_design,
            question_difficulty="hard",
            raw_transcript="I implement probabilistic early expiration using XFetch, backed by Redis cluster with hash tags.",
            eval_scores={"composite_score": 0.88, "relevance": 0.9, "depth": 0.85},
            audio_metrics={"speech_rate_wpm": 142.0, "filler_ratio": 0.02, "clarity": 0.88},
        )
        db.add(t2)

        # Seed a Coding Challenge for Candidate 1 (Score: 92.0)
        coding1 = CodingChallenge(
            session_id=s2.id,
            title="Two Sum with Target Index Search",
            description="Find indices of two numbers adding to target.",
            difficulty="medium",
            language="python",
            starter_code="def two_sum(nums, target): pass",
            score=92.0,
            submitted_at=datetime.now(UTC),
        )
        db.add(coding1)
        await db.commit()

    print("[PASS] Seeded multi-session longitudinal interview & coding history.")

    # ── 2. Test Feature 12: Personalized Learning Engine ───────────────────────
    print("\n--- Testing Feature 12: Personalized Learning Engine ---")
    async with AsyncSessionLocal() as db:
        # Create plan for detected gap "SQL Query Optimization"
        plan = await learning_engine.create_plan_for_gap(
            db=db,
            user_id=candidate_id,
            gap_name="SQL Query Optimization",
            source_session_id=s1.id,
            category="technical",
            target_days=7,
        )
        plan_id = plan.id
        assert plan.title == "7-Day Deep Dive: SQL Query Optimization, Execution Plans & Indexing"
        assert len(plan.daily_schedule) == 7
        assert len(plan.reassessment_quiz) == 5
        assert plan.status == LearningPlanStatus.active
        assert plan.current_day == 1
        print(f"[PASS] 7-day personalized plan created: '{plan.title}' with {len(plan.daily_schedule)} daily modules.")

        # Complete Day 1 milestone
        plan_updated = await learning_engine.complete_day_milestone(
            db=db, plan_id=plan_id, day_number=1, user_id=candidate_id
        )
        assert plan_updated.daily_schedule[0]["is_completed"] is True
        assert plan_updated.daily_schedule[0]["completed_at"] is not None
        assert plan_updated.current_day == 2
        print("[PASS] Day 1 milestone completed and current_day advanced to 2.")

        # Complete Day 2 milestone
        plan_updated = await learning_engine.complete_day_milestone(
            db=db, plan_id=plan_id, day_number=2, user_id=candidate_id
        )
        assert plan_updated.current_day == 3
        print("[PASS] Day 2 milestone completed.")

        # Submit reassessment quiz answers demonstrating mastery
        answers = [
            {"question_id": 1, "answer_text": "Nested loop iterates inner table per outer row using O(1) memory, while Hash Join builds an in-memory hash table of smaller relation requiring O(N) memory."},
            {"question_id": 2, "answer_text": "Violates Leftmost Prefix rule of B-Trees because search cannot skip leading columns like tenant_id without full scan."},
            {"question_id": 3, "answer_text": "It means 500,000 tuples were loaded from disk/buffer and discarded post-scan due to lack of index predicate coverage."},
            {"question_id": 4, "answer_text": "Autovacuum freezes old transaction IDs to prevent 32-bit transaction circular counter wraparound and data invisibility."},
            {"question_id": 5, "answer_text": "Deterministic ordering of row IDs in ascending order before acquiring SELECT FOR UPDATE locks prevents cyclical deadlocks."},
        ]
        reassess_res = await learning_engine.submit_reassessment(
            db=db, plan_id=plan_id, answers=answers, user_id=candidate_id
        )
        assert reassess_res["passed"] is True
        assert reassess_res["reassessment_score"] >= 75.0
        assert reassess_res["status"] == "completed"
        print(f"[PASS] Reassessment passed with score {reassess_res['reassessment_score']}%: '{reassess_res['message']}'")
        await db.commit()

    # ── 3. Test Feature 13: Candidate AI Twin & Feature 16: Explainable AI ────
    print("\n--- Testing Feature 13 & 16: Candidate AI Twin & Explainable AI ---")
    async with AsyncSessionLocal() as db:
        twin = await twin_engine.sync_twin_from_history(db, candidate_id)
        assert twin.overall_readiness_score > 70.0
        assert twin.growth_velocity > 0.0  # Slope between session 1 (72) and session 2 (84) is positive (+12.0)
        assert len(twin.historical_trajectory) >= 2
        session_events = [e for e in twin.historical_trajectory if e.get("event_type") == "interview_session"]
        assert len(session_events) == 2
        assert session_events[1]["delta"] == 12.0
        print(f"[PASS] Candidate AI Twin synced: Overall Readiness={twin.overall_readiness_score}/100, Growth Velocity={twin.growth_velocity} pts/session.")
        print(f"[PASS] Historical Trajectory verified: Session 1 (72.0) -> Session 2 (84.0, delta +12.0).")

        # Explainable AI Breakdown for Technical Mastery
        tech_explain = await twin_engine.explain_score_dimension(db, candidate_id, "technical")
        assert "what_was_evaluated" in tech_explain
        assert "evidence_found" in tech_explain
        assert "score_rationale" in tech_explain
        assert "what_is_missing" in tech_explain
        assert "actionable_improvement_roadmap" in tech_explain
        print(f"[PASS] Feature 16 Explainable AI compliant: Explained '{tech_explain['dimension']}' with {len(tech_explain['evidence_found'])} evidence points.")

        # Explainable AI Breakdown for Communication
        comm_explain = await twin_engine.explain_score_dimension(db, candidate_id, "communication")
        assert comm_explain["dimension"] == "Communication & Speech Signals"
        assert len(comm_explain["evidence_found"]) == 3
        print(f"[PASS] Explainable speech signals validated: {comm_explain['evidence_found'][0]}")

    # ── 4. Test Feature 14: Recruiter Copilot Engine ───────────────────────────
    print("\n--- Testing Feature 14: Recruiter Copilot Engine ---")
    async with AsyncSessionLocal() as db:
        # Create requisition with customizable rubric weights
        weights = {"technical": 0.35, "system_design": 0.25, "coding": 0.20, "behavioral": 0.20}
        req = await recruiter_service.create_requisition(
            db=db,
            creator_id=recruiter_id,
            title="Senior Distributed Systems & AI Architect",
            department="Core Infrastructure",
            seniority_level="staff",
            description="Leading next-generation distributed transaction systems.",
            required_skills=["python", "redis", "system_design", "postgresql", "kafka"],
            rubric_weights=weights,
            hiring_threshold=75.0,
            org_id=org_id,
        )
        req_id = req.id
        assert req.status == RequisitionStatus.active
        assert req.rubric_weights["technical"] == 0.35
        print(f"[PASS] Recruiter requisition created: '{req.title}' with custom rubric weights: {req.rubric_weights}")

        # Invite Candidate 1 & Candidate 2
        inv1 = await recruiter_service.invite_candidate(db, req_id, candidate_id)
        inv2 = await recruiter_service.invite_candidate(db, req_id, candidate2_id)
        assert inv1.status == CandidateStage.invited
        assert inv2.status == CandidateStage.invited
        print("[PASS] Candidates 1 & 2 invited to requisition pipeline.")

        # Recruiter Copilot AI Evaluation for Candidate 1
        eval1 = await recruiter_service.evaluate_candidate_for_requisition(db, req_id, candidate_id)
        assert eval1.composite_score is not None
        assert eval1.composite_score >= 75.0
        assert eval1.hiring_recommendation in ("Strong Hire", "Hire")
        assert "copilot_narrative" in eval1.evidence_summary
        print(f"[PASS] Recruiter Copilot evaluated Candidate 1: Composite Score={eval1.composite_score}, Verdict={eval1.hiring_recommendation}")

        # Side-by-Side Candidate Comparison Matrix
        comparison = await recruiter_service.compare_candidates_side_by_side(
            db=db,
            requisition_id=req_id,
            candidate_ids=[candidate_id, candidate2_id],
        )
        assert comparison["total_compared"] == 2
        assert comparison["top_candidate_id"] == str(candidate_id)
        assert len(comparison["matrix"]) == 2
        print(f"[PASS] Side-by-side comparison matrix generated. Top candidate: {comparison['matrix'][0]['full_name']} (Score: {comparison['matrix'][0]['composite_score']})")

        # Talent pool search
        matches = await recruiter_service.search_talent_pool(db, req_id, min_score=60.0, top_k=200)
        assert len(matches) >= 1
        assert any(m["candidate_id"] == str(candidate_id) for m in matches)
        print(f"[PASS] Talent pool search retrieved {len(matches)} matching candidate(s) meeting readiness threshold.")
        await db.commit()


    # ── 5. Test HTTP REST Endpoints & RBAC Security ───────────────────────────
    print("\n--- Testing HTTP REST Endpoints & RBAC Security ---")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        candidate_token = create_access_token(candidate_id, UserRole.candidate.value)
        candidate_headers = {"Authorization": f"Bearer {candidate_token}"}

        recruiter_token = create_access_token(recruiter_id, UserRole.recruiter.value)
        recruiter_headers = {"Authorization": f"Bearer {recruiter_token}"}

        # 1. Candidate GET /api/v1/twin/me
        res = await client.get("/api/v1/twin/me", headers=candidate_headers)
        assert res.status_code == 200, res.text
        twin_data = res.json()
        assert twin_data["overall_readiness_score"] > 70.0
        print(f"[PASS] GET /api/v1/twin/me: Readiness={twin_data['overall_readiness_score']}")

        # 2. Candidate POST /api/v1/twin/sync
        res = await client.post("/api/v1/twin/sync", headers=candidate_headers)
        assert res.status_code == 200, res.text
        print("[PASS] POST /api/v1/twin/sync: Candidate AI Twin successfully resynced via API.")

        # 3. Candidate GET /api/v1/twin/explain/technical
        res = await client.get("/api/v1/twin/explain/technical", headers=candidate_headers)
        assert res.status_code == 200, res.text
        explain_data = res.json()
        assert explain_data["dimension"] == "Technical Mastery"
        print(f"[PASS] GET /api/v1/twin/explain/technical: Returned 5-point explainable breakdown.")

        # 4. Candidate POST /api/v1/learning/plans/generate
        res = await client.post(
            "/api/v1/learning/plans/generate",
            headers=candidate_headers,
            json={"gap_name": "Distributed Caching", "category": "system_design", "target_days": 7},
        )
        assert res.status_code == 201, res.text
        http_plan = res.json()
        assert http_plan["detected_gap"] == "Distributed Caching"
        print(f"[PASS] POST /api/v1/learning/plans/generate: Created plan via API: '{http_plan['title']}'")

        # 5. Candidate GET /api/v1/learning/plans/my
        res = await client.get("/api/v1/learning/plans/my", headers=candidate_headers)
        assert res.status_code == 200, res.text
        plans_data = res.json()
        assert len(plans_data) >= 1
        print(f"[PASS] GET /api/v1/learning/plans/my: Retrieved {len(plans_data)} learning plan(s).")

        # 6. Candidate attempts to access recruiter requisition creation -> 403 Forbidden
        res = await client.post(
            "/api/v1/recruiter/requisitions",
            headers=candidate_headers,
            json={"title": "Unauthorized Role", "required_skills": ["python"]},
        )
        assert res.status_code == 403, res.text
        print("[PASS] RBAC Enforced: Candidate blocked (403 Forbidden) from recruiter requisition endpoint.")

        # 7. Recruiter POST /api/v1/recruiter/requisitions
        res = await client.post(
            "/api/v1/recruiter/requisitions",
            headers=recruiter_headers,
            json={
                "title": "Principal AI Systems Engineer",
                "department": "AI Infrastructure",
                "seniority_level": "principal",
                "required_skills": ["python", "system_design", "distributed_systems"],
                "rubric_weights": {"technical": 0.4, "system_design": 0.3, "coding": 0.2, "behavioral": 0.1},
                "hiring_threshold": 80.0,
            },
        )
        assert res.status_code == 201, res.text
        http_req = res.json()
        http_req_id = http_req["id"]
        print(f"[PASS] POST /api/v1/recruiter/requisitions: Created requisition via API: '{http_req['title']}'")

        # 8. Recruiter GET /api/v1/recruiter/requisitions
        res = await client.get("/api/v1/recruiter/requisitions", headers=recruiter_headers)
        assert res.status_code == 200, res.text
        reqs_data = res.json()
        assert len(reqs_data) >= 1
        print(f"[PASS] GET /api/v1/recruiter/requisitions: Recruiter retrieved {len(reqs_data)} requisition(s).")

        # 9. Recruiter POST /api/v1/recruiter/requisitions/{id}/invite
        res = await client.post(
            f"/api/v1/recruiter/requisitions/{http_req_id}/invite",
            headers=recruiter_headers,
            json={"candidate_id": str(candidate_id)},
        )
        assert res.status_code == 201, res.text
        print(f"[PASS] POST /api/v1/recruiter/requisitions/{http_req_id}/invite: Candidate invited via API.")

        # 10. Recruiter POST /api/v1/recruiter/requisitions/{id}/compare
        res = await client.post(
            f"/api/v1/recruiter/requisitions/{req_id}/compare",
            headers=recruiter_headers,
            json={"candidate_ids": [str(candidate_id), str(candidate2_id)]},
        )
        assert res.status_code == 200, res.text
        comp_data = res.json()
        assert comp_data["total_compared"] == 2
        print(f"[PASS] POST /api/v1/recruiter/requisitions/{req_id}/compare: Compared 2 candidates.")


    # ── 6. Verify Enterprise Audit Log Persistence ────────────────────────────
    async with AsyncSessionLocal() as db:
        res = await db.execute(
            select(AuditLog).where(
                AuditLog.action.in_([
                    "learning.plan_generated",
                    "learning.day_completed",
                    "candidate_twin.synced",
                    "recruiter.requisition_created",
                    "recruiter.candidate_evaluated",
                    "recruiter.candidates_compared",
                ])
            )
        )
        logs = list(res.scalars().all())
        assert len(logs) >= 3
        actions = [l.action for l in logs]
        print(f"[PASS] Verified enterprise audit log entries recorded: {actions}")

    print("\n=== ALL PHASE 8 CANDIDATE AI TWIN, LEARNING ENGINE & RECRUITER COPILOT TESTS PASSED ===")


if __name__ == "__main__":
    asyncio.run(test_phase8_twin_learning_recruiter_complete())
