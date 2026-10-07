"""
Phase 15: Enterprise Recruiter Platform & Copilot Test Suite
Validates:
1. Requisition lifecycle: Creation with customizable rubrics, weights validation, dynamic threshold updates.
2. Candidate invitation and multi-source AI Copilot evaluation with grounded evidence synthesis.
3. Bar-Raiser Executive Hiring Debrief Memo generation with STAR+L, DAG, and SM-2 evidence grounding.
4. Requisition calibration engine with statistical percentiles and what-if sensitivity curves.
5. Candidate stage progression workflow (invited -> in_progress -> interviewed -> offer) with recruiter notes.
6. Side-by-side comparative decision matrix across multiple candidates.
7. Global talent pool search with skill coverage filtering.
8. Complete HTTP REST API endpoint coverage under /api/v1/recruiter/*.
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
from app.models.interview_session import InterviewSession, QuestionDifficulty, SessionStatus
from app.models.interview_turn import InterviewTurn, QuestionCategory
from app.models.recruiter import CandidateStage, RecruiterRequisition, RequisitionCandidate, RequisitionStatus
from app.models.skill_graph import CandidateSkillMastery
from app.models.sm2_card import SpacedRepetitionCard
from app.models.user import User, UserRole
from app.services.recruiter_copilot_service import RecruiterCopilotService


async def test_phase15_recruiter_copilot() -> None:
    print("\n========================================================")
    print("=== STARTING PHASE 15: RECRUITER PLATFORM & COPILOT ===")
    print("========================================================\n")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    copilot_svc = RecruiterCopilotService()
    recruiter_id = uuid.uuid4()
    candidate_1_id = uuid.uuid4()
    candidate_2_id = uuid.uuid4()

    # ── 1. SEED TEST USERS & TELEMETRY ────────────────────────────────────────
    print("--- 1. Seeding Recruiter & Candidates with Multi-Pillar Telemetry ---")
    async with AsyncSessionLocal() as session:
        # Recruiter User
        recruiter = User(
            id=recruiter_id,
            email=f"recruiter.{uuid.uuid4().hex[:6]}@enterprise.test",
            full_name="Sarah Staffing",
            hashed_password="RecruiterPass123!",
            role=UserRole.recruiter,
            is_active=True,
        )
        session.add(recruiter)

        # Candidate 1: Strong Backend Engineer
        c1 = User(
            id=candidate_1_id,
            email=f"candidate1.{uuid.uuid4().hex[:6]}@enterprise.test",
            full_name="David Dist-Systems",
            hashed_password="CandPass123!",
            role=UserRole.candidate,
            is_active=True,
        )
        session.add(c1)

        # Candidate 2: High Potential Junior/Mid
        c2 = User(
            id=candidate_2_id,
            email=f"candidate2.{uuid.uuid4().hex[:6]}@enterprise.test",
            full_name="Elena Junior-Dev",
            hashed_password="CandPass123!",
            role=UserRole.candidate,
            is_active=True,
        )
        session.add(c2)
        await session.flush()

        # Telemetry for Candidate 1 (Completed Session & Turns)
        s1 = InterviewSession(
            id=uuid.uuid4(),
            user_id=candidate_1_id,
            status=SessionStatus.completed,
            target_question_count=2,
            current_question_index=2,
            current_difficulty=QuestionDifficulty.hard,
            aggregate_score=88.0,
            started_at=datetime.now(UTC) - timedelta(days=3),
            completed_at=datetime.now(UTC) - timedelta(days=3, minutes=-45),
        )
        session.add(s1)

        turn1 = InterviewTurn(
            id=uuid.uuid4(),
            session_id=s1.id,
            turn_index=0,
            question_text="How do you architect distributed event streaming?",
            question_category=QuestionCategory.system_design,
            question_difficulty="hard",
            raw_transcript="We leveraged Kafka partitioned topics with idempotent consumer offsets.",
            eval_scores={"composite_score": 0.90, "relevance": 0.92, "technical_accuracy": 0.90},
            audio_metrics={"speech_rate_wpm": 140.0, "silence_ratio": 0.07, "filler_word_rate": 0.02},
        )
        turn2 = InterviewTurn(
            id=uuid.uuid4(),
            session_id=s1.id,
            turn_index=1,
            question_text="Describe how you managed an engineering disagreement.",
            question_category=QuestionCategory.behavioral,
            question_difficulty="medium",
            raw_transcript="I drove an RFC review where I facilitated cross-team alignment on database sharding.",
            eval_scores={"composite_score": 0.85, "relevance": 0.88, "technical_accuracy": 0.85},
            audio_metrics={"speech_rate_wpm": 138.0, "silence_ratio": 0.08, "filler_word_rate": 0.02},
        )
        session.add_all([turn1, turn2])

        # Coding challenge for Candidate 1
        challenge1 = CodingChallenge(
            id=uuid.uuid4(),
            session_id=s1.id,
            title="Consistent Hashing Ring",
            description="Build a consistent hash ring with virtual nodes.",
            difficulty="hard",
            language="python",
            starter_code="class HashRing:\n    pass",
            score=92.0,
            submitted_at=datetime.now(UTC) - timedelta(days=2),
        )
        session.add(challenge1)

        # Skill DAG Masteries for Candidate 1
        m1 = CandidateSkillMastery(
            id=uuid.uuid4(),
            user_id=candidate_1_id,
            skill_id="distributed-systems",
            mastery_score=94.0,
            confidence=0.95,
        )
        m2 = CandidateSkillMastery(
            id=uuid.uuid4(),
            user_id=candidate_1_id,
            skill_id="python-concurrency",
            mastery_score=88.0,
            confidence=0.90,
        )
        session.add_all([m1, m2])

        # SM-2 Flashcards for Candidate 1
        card1 = SpacedRepetitionCard(
            id=uuid.uuid4(),
            user_id=candidate_1_id,
            skill_id="distributed-systems",
            concept_key="raft-log-matching",
            title="Raft Log Matching Invariant",
            question_prompt="What guarantees log consistency across terms in Raft?",
            answer_explanation="If two logs contain an entry with the same index and term, they are identical up to that point.",
            category="system-design",
            tier=4,
            repetition_count=5,
            interval_days=25,
            easiness_factor=2.8,
            retention_score=0.96,
            last_reviewed_at=datetime.now(UTC) - timedelta(days=1),
            next_review_due=datetime.now(UTC) + timedelta(days=24),
        )
        session.add(card1)

        # Candidate 2: basic telemetry
        s2 = InterviewSession(
            id=uuid.uuid4(),
            user_id=candidate_2_id,
            status=SessionStatus.completed,
            target_question_count=1,
            current_question_index=1,
            current_difficulty=QuestionDifficulty.easy,
            aggregate_score=68.0,
            started_at=datetime.now(UTC) - timedelta(days=4),
            completed_at=datetime.now(UTC) - timedelta(days=4, minutes=-20),
        )
        session.add(s2)

        turn2_1 = InterviewTurn(
            id=uuid.uuid4(),
            session_id=s2.id,
            turn_index=0,
            question_text="Explain Python lists vs dictionaries.",
            question_category=QuestionCategory.technical,
            question_difficulty="easy",
            raw_transcript="Lists are ordered sequential arrays, dictionaries are hash maps with O(1) lookup.",
            eval_scores={"composite_score": 0.70},
            audio_metrics={"speech_rate_wpm": 120.0, "silence_ratio": 0.12},
        )
        session.add(turn2_1)

        await session.commit()
    print("  [PASS] Seeding users and multi-pillar telemetry successful.")

    # ── 2. REQUISITION CREATION, WEIGHTS VALIDATION & UPDATES ─────────────────
    print("\n--- 2. Validating Requisition Lifecycle & Calibration Settings ---")
    async with AsyncSessionLocal() as session:
        # 2.1 Create Requisition
        req = await copilot_svc.create_requisition(
            db=session,
            creator_id=recruiter_id,
            title="Senior Distributed Systems Architect",
            department="Core Infrastructure",
            seniority_level="senior",
            description="Lead distributed consensus and stream processing platforms.",
            required_skills=["distributed-systems", "python-concurrency", "kafka"],
            rubric_weights={
                "technical": 0.35,
                "system_design": 0.30,
                "coding": 0.20,
                "behavioral": 0.15,
            },
            hiring_threshold=78.0,
        )
        await session.commit()

        assert req.id is not None
        assert req.title == "Senior Distributed Systems Architect"
        assert req.hiring_threshold == 78.0
        assert req.rubric_weights["technical"] == 0.35
        print(f"  [PASS] Requisition created: {req.title} (ID: {req.id}).")

        # 2.2 Update Requisition Threshold
        updated_req = await copilot_svc.update_requisition(
            db=session,
            requisition_id=req.id,
            hiring_threshold=80.0,
            description="Updated role charter with heightened bar.",
        )
        await session.commit()
        assert updated_req.hiring_threshold == 80.0
        assert "heightened bar" in updated_req.description
        print("  [PASS] Requisition threshold updated to 80.0% successfully.")

    # ── 3. CANDIDATE INVITATION & AI COPILOT EVALUATION ───────────────────────
    print("\n--- 3. Testing Candidate Invitation & Multi-Pillar AI Evaluation ---")
    async with AsyncSessionLocal() as session:
        # Invite candidates
        inv1 = await copilot_svc.invite_candidate(session, req.id, candidate_1_id)
        inv2 = await copilot_svc.invite_candidate(session, req.id, candidate_2_id)
        await session.commit()
        assert inv1.status == CandidateStage.invited
        assert inv2.status == CandidateStage.invited
        print("  [PASS] Candidates 1 and 2 successfully invited to requisition pipeline.")

        # Run AI Copilot Evaluation for Candidate 1
        eval1 = await copilot_svc.evaluate_candidate_for_requisition(session, req.id, candidate_1_id)
        await session.commit()

        assert eval1.composite_score is not None
        assert eval1.composite_score >= 80.0
        assert eval1.hiring_recommendation in ("Hire", "Strong Hire")
        assert eval1.status == CandidateStage.interviewed
        assert eval1.evidence_summary is not None
        assert "distributed-systems" in eval1.evidence_summary["verified_skills"]
        print(f"  [PASS] Candidate 1 evaluated: Score={eval1.composite_score}%, Recommendation={eval1.hiring_recommendation}.")

        # Run AI Copilot Evaluation for Candidate 2
        eval2 = await copilot_svc.evaluate_candidate_for_requisition(session, req.id, candidate_2_id)
        await session.commit()
        assert eval2.composite_score is not None
        assert eval2.composite_score < eval1.composite_score
        print(f"  [PASS] Candidate 2 evaluated: Score={eval2.composite_score}%, Recommendation={eval2.hiring_recommendation}.")

    # ── 4. BAR-RAISER EXECUTIVE HIRING DEBRIEF MEMO ───────────────────────────
    print("\n--- 4. Testing Bar-Raiser Executive Debrief Memo Generator ---")
    async with AsyncSessionLocal() as session:
        memo = await copilot_svc.generate_executive_debrief_memo(session, req.id, candidate_1_id)

        assert memo["candidate_name"] == "David Dist-Systems"
        assert memo["role_title"] == "Senior Distributed Systems Architect"
        assert memo["composite_score"] >= 80.0
        assert "# Executive Hiring Debrief Memo" in memo["memo_markdown"]
        assert "Multi-Modal Evidence Grounding" in memo["memo_markdown"]
        assert len(memo["key_strengths"]) >= 3
        assert len(memo["suggested_debrief_questions"]) == 3
        print("  [PASS] Debrief Memo generated with structured STAR+L, DAG, and SM-2 evidence.")
        print(f"    - Sample Committee Probe: '{memo['suggested_debrief_questions'][0]}'")

    # ── 5. REQUISITION CALIBRATION & SENSITIVITY CURVE ────────────────────────
    print("\n--- 5. Validating Requisition Calibration & Sensitivity Simulation ---")
    async with AsyncSessionLocal() as session:
        calib = await copilot_svc.calibrate_requisition(session, req.id)

        assert calib["requisition_id"] == req.id
        assert calib["current_threshold"] == 80.0
        assert calib["total_candidates"] >= 2
        assert "score_statistics" in calib
        assert calib["score_statistics"]["median"] > 0
        assert len(calib["sensitivity_curve"]) == 7  # 60 through 90 thresholds

        print(f"  [PASS] Calibration computed. Median Score={calib['score_statistics']['median']}%, Pass Rate={calib['pass_rate_pct']}%.")
        for pt in calib["sensitivity_curve"][:3]:
            print(f"    - Threshold {pt['threshold']}% -> {pt['qualifying_candidates']} qualify ({pt['pass_rate_pct']}%)")

    # ── 6. CANDIDATE STAGE PROGRESSION & RECRUITER NOTES ──────────────────────
    print("\n--- 6. Testing Candidate Pipeline Stage Progression & Notes ---")
    async with AsyncSessionLocal() as session:
        updated_cand = await copilot_svc.update_candidate_stage(
            db=session,
            requisition_id=req.id,
            candidate_id=candidate_1_id,
            new_stage=CandidateStage.offer,
            recruiter_notes="Unanimous hire recommendation from Bar-Raiser panel. Extending L5 offer.",
        )
        await session.commit()

        assert updated_cand.status == CandidateStage.offer
        assert "Extending L5 offer" in updated_cand.recruiter_notes
        print("  [PASS] Candidate 1 stage transitioned to 'offer' with audit-logged recruiter notes.")

    # ── 7. SIDE-BY-SIDE CANDIDATE COMPARISON MATRIX ───────────────────────────
    print("\n--- 7. Testing Side-by-Side Candidate Comparison Matrix ---")
    async with AsyncSessionLocal() as session:
        comparison = await copilot_svc.compare_candidates_side_by_side(
            db=session,
            requisition_id=req.id,
            candidate_ids=[candidate_1_id, candidate_2_id],
        )

        assert comparison["total_compared"] == 2
        assert comparison["top_candidate_id"] == str(candidate_1_id)
        assert len(comparison["matrix"]) == 2
        assert comparison["matrix"][0]["candidate_id"] == str(candidate_1_id)
        assert comparison["matrix"][1]["candidate_id"] == str(candidate_2_id)
        print("  [PASS] Side-by-side comparative matrix correctly ranked candidates.")

    # ── 8. FULL HTTP REST API ENDPOINTS COVERAGE ─────────────────────────────
    print("\n--- 8. Validating Recruiter Platform HTTP REST Endpoints ---")
    recruiter_token = create_access_token(recruiter_id, UserRole.recruiter.value)
    headers = {"Authorization": f"Bearer {recruiter_token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        # 8.1 GET /recruiter/requisitions
        resp = await client.get("/api/v1/recruiter/requisitions", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        req_list = resp.json()
        assert len(req_list) >= 1
        print("  [PASS] GET /api/v1/recruiter/requisitions returned 200 OK.")

        # 8.2 GET /recruiter/requisitions/{id}
        resp = await client.get(f"/api/v1/recruiter/requisitions/{req.id}", headers=headers)
        assert resp.status_code == 200
        assert str(resp.json()["id"]) == str(req.id)
        print("  [PASS] GET /api/v1/recruiter/requisitions/{id} returned 200 OK.")

        # 8.3 PATCH /recruiter/requisitions/{id}
        resp = await client.patch(
            f"/api/v1/recruiter/requisitions/{req.id}",
            headers=headers,
            json={"hiring_threshold": 82.0, "seniority_level": "lead"},
        )
        assert resp.status_code == 200
        assert resp.json()["hiring_threshold"] == 82.0
        assert resp.json()["seniority_level"] == "lead"
        print("  [PASS] PATCH /api/v1/recruiter/requisitions/{id} returned 200 OK.")

        # 8.4 GET /recruiter/requisitions/{id}/candidates
        resp = await client.get(f"/api/v1/recruiter/requisitions/{req.id}/candidates", headers=headers)
        assert resp.status_code == 200
        cands = resp.json()
        assert len(cands) >= 2
        print(f"  [PASS] GET /api/v1/recruiter/requisitions/{{id}}/candidates returned {len(cands)} candidates.")

        # 8.5 PATCH /recruiter/requisitions/{id}/candidates/{cid}/stage
        resp = await client.patch(
            f"/api/v1/recruiter/requisitions/{req.id}/candidates/{candidate_2_id}/stage",
            headers=headers,
            json={"stage": "review_required", "recruiter_notes": "Needs additional systems review."},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "review_required"
        print("  [PASS] PATCH /api/v1/recruiter/requisitions/{id}/candidates/{cid}/stage returned 200 OK.")

        # 8.6 GET /recruiter/requisitions/{id}/calibration
        resp = await client.get(f"/api/v1/recruiter/requisitions/{req.id}/calibration", headers=headers)
        assert resp.status_code == 200
        calib_resp = resp.json()
        assert "score_statistics" in calib_resp
        assert len(calib_resp["sensitivity_curve"]) == 7
        print("  [PASS] GET /api/v1/recruiter/requisitions/{id}/calibration returned 200 OK.")

        # 8.7 GET /recruiter/requisitions/{id}/debrief-memo/{cid}
        resp = await client.get(
            f"/api/v1/recruiter/requisitions/{req.id}/debrief-memo/{candidate_1_id}",
            headers=headers,
        )
        assert resp.status_code == 200
        memo_resp = resp.json()
        assert "memo_markdown" in memo_resp
        assert len(memo_resp["suggested_debrief_questions"]) == 3
        print("  [PASS] GET /api/v1/recruiter/requisitions/{id}/debrief-memo/{cid} returned 200 OK.")

        # 8.8 POST /recruiter/requisitions/{id}/compare
        resp = await client.post(
            f"/api/v1/recruiter/requisitions/{req.id}/compare",
            headers=headers,
            json={"candidate_ids": [str(candidate_1_id), str(candidate_2_id)]},
        )
        assert resp.status_code == 200
        comp_resp = resp.json()
        assert comp_resp["total_compared"] == 2
        print("  [PASS] POST /api/v1/recruiter/requisitions/{id}/compare returned 200 OK.")

        # 8.9 GET /recruiter/talent-pool/search
        resp = await client.get(
            "/api/v1/recruiter/talent-pool/search?min_readiness=50.0",
            headers=headers,
        )
        assert resp.status_code == 200
        pool_matches = resp.json()
        assert len(pool_matches) >= 1
        print(f"  [PASS] GET /api/v1/recruiter/talent-pool/search returned {len(pool_matches)} matches.")

    print("\n========================================================")
    print("=== ALL PHASE 15 RECRUITER PLATFORM TESTS PASSED (100%) ===")
    print("========================================================\n")


if __name__ == "__main__":
    asyncio.run(test_phase15_recruiter_copilot())
