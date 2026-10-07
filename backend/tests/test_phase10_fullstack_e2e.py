import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
import uuid
from datetime import UTC, datetime
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.security import create_access_token
from app.database import AsyncSessionLocal
from app.main import app
from app.models.organization import Organization, OrganizationTier
from app.models.user import User, UserRole
from app.models.job_description import JobDescription
from app.models.resume import Resume
from app.models.ats_analysis import AtsAnalysis, AtsMatchTier
from app.models.interview_session import InterviewSession, SessionStatus, QuestionDifficulty
from app.models.interview_turn import InterviewTurn, QuestionCategory
from app.models.candidate_twin import CandidateTwin
from app.models.learning_plan import LearningPlan, LearningPlanStatus
from app.models.recruiter import RecruiterRequisition, RequisitionCandidate, CandidateStage
from app.services.audit_service import record_audit_event, verify_audit_chain
from app.services.candidate_twin_service import CandidateTwinEngine
from app.services.system_design_service import SystemDesignEngine
from app.services.ai_cost_controller import calculate_token_cost
from app.services.circuit_breaker import CircuitBreakerRegistry


async def test_phase10_fullstack_e2e():
    print("\n========================================================")
    print("=== STARTING PHASE 10: FULL-STACK INTEGRATION & E2E PLATFORM TESTS ===")
    print("========================================================")

    async with AsyncSessionLocal() as db:
        # Step 1: Organization & Identity Setup
        print("\n--- Step 1: Multi-Tenant Organization & User Identities ---")
        org = Organization(
            name=f"Apex Global Systems {uuid.uuid4().hex[:6]}",
            slug=f"apex-{uuid.uuid4().hex[:6]}",
            tier=OrganizationTier.enterprise,
        )
        db.add(org)
        await db.flush()

        admin_user = User(
            email=f"admin.{uuid.uuid4().hex[:6]}@apex.com",
            full_name="Apex System Admin",
            hashed_password="hashed_pw_test_123",
            role=UserRole.admin,
            org_id=org.id,
            is_active=True,
        )
        recruiter_user = User(
            email=f"recruiter.{uuid.uuid4().hex[:6]}@apex.com",
            full_name="Lead Talent Partner",
            hashed_password="hashed_pw_test_123",
            role=UserRole.recruiter,
            org_id=org.id,
            is_active=True,
        )
        candidate_user = User(
            email=f"candidate.{uuid.uuid4().hex[:6]}@apex.com",
            full_name="Alex Mercer",
            hashed_password="hashed_pw_test_123",
            role=UserRole.candidate,
            org_id=org.id,
            is_active=True,
        )
        db.add_all([admin_user, recruiter_user, candidate_user])
        await db.commit()
        await db.refresh(admin_user)
        await db.refresh(recruiter_user)
        await db.refresh(candidate_user)

    admin_token = create_access_token(admin_user.id, role="admin", org_id=org.id)
    recruiter_token = create_access_token(recruiter_user.id, role="recruiter", org_id=org.id)
    candidate_token = create_access_token(candidate_user.id, role="candidate")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 2: Semantic ATS & Resume Upload
        print("\n--- Step 2: Semantic ATS Analyzer ---")
        dummy_embedding = [0.05] * 3072
        async with AsyncSessionLocal() as db:
            resume = Resume(
                user_id=candidate_user.id,
                file_name="alex_mercer_resume.pdf",
                s3_key=f"resumes/{candidate_user.id}/{uuid.uuid4().hex}.pdf",
                parsed_text=(
                    "Alex Mercer: Senior Distributed Systems Engineer with 6 years experience in Python, "
                    "Go, PostgreSQL, Redis, Kubernetes, and event-driven architecture. Designed rate limiters "
                    "and microservices handling 50k QPS."
                ),
                embedding=dummy_embedding,
                metadata_={"word_count": 35, "ext": "pdf"},
            )
            jd = JobDescription(
                created_by=recruiter_user.id,
                title="Principal Distributed Infrastructure Engineer",
                company="Apex Global",
                raw_text=(
                    "Looking for a Principal Infrastructure Engineer skilled in Distributed Systems, Redis, "
                    "Kafka, Cassandra, Kubernetes, microservice scalability, and fault tolerance."
                ),
                embedding=dummy_embedding,
                structured_skills=["Distributed Systems", "Redis", "Kafka", "Kubernetes", "PostgreSQL"],
            )
            db.add_all([resume, jd])
            await db.flush()

            ats = AtsAnalysis(
                resume_id=resume.id,
                jd_id=jd.id,
                cosine_similarity=0.88,
                match_tier=AtsMatchTier.excellent,
                skill_gaps=[
                    {"skill_name": "Kafka", "gap_type": "missing", "jd_importance": 0.85, "semantic_distance": 0.4},
                    {"skill_name": "Cassandra", "gap_type": "missing", "jd_importance": 0.75, "semantic_distance": 0.5},
                ],
                matched_skills=[
                    {"skill_name": "Redis", "confidence": 0.95, "resume_evidence": "Designed rate limiters"},
                    {"skill_name": "PostgreSQL", "confidence": 0.92, "resume_evidence": "6 years experience"},
                    {"skill_name": "Kubernetes", "confidence": 0.90, "resume_evidence": "Production Kubernetes"},
                ],
                section_scores={"skills": 0.88, "experience": 0.85, "education": 0.80},
                overall_score=87.5,
            )
            db.add(ats)
            await db.commit()
            ats_id = str(ats.id)

        ats_resp = await client.get(
            f"/api/v1/ats/analysis/{ats_id}",
            headers={"Authorization": f"Bearer {candidate_token}"},
        )
        assert ats_resp.status_code == 200, f"ATS analysis fetch failed: {ats_resp.text}"
        ats_data = ats_resp.json()
        assert ats_data["overall_score"] >= 80.0
        print(f"  [PASS] ATS analysis verified. Score: {ats_data['overall_score']}, Tier: {ats_data['match_tier']}")

        # Step 3: Adaptive Mock Interview Session & Turns
        print("\n--- Step 3: Adaptive Mock Interview State Machine ---")
        async with AsyncSessionLocal() as db:
            session = InterviewSession(
                user_id=candidate_user.id,
                resume_id=resume.id,
                jd_id=jd.id,
                ats_analysis_id=ats.id,
                target_question_count=4,
                current_question_index=2,
                current_difficulty=QuestionDifficulty.hard,
                status=SessionStatus.completed,
                aggregate_score=84.0,
                session_config={"focus_categories": ["technical", "system_design"]},
                started_at=datetime.now(UTC),
                completed_at=datetime.now(UTC),
            )
            db.add(session)
            await db.flush()

            turn1 = InterviewTurn(
                session_id=session.id,
                turn_index=0,
                question_text="How do you guarantee sliding-window atomicity in Redis under high concurrency?",
                question_category=QuestionCategory.technical,
                question_difficulty="hard",
                raw_transcript="I use a Redis sorted set with ZADD and ZREMRANGEBYSCORE executed in a MULTI-EXEC pipeline or Lua script.",
                audio_metrics={"speech_rate_wpm": 142.0, "silence_ratio": 0.08, "filler_word_rate": 0.02},
                eval_scores={"composite_score": 0.88, "technical_accuracy": 0.92, "clarity": 0.85},
            )
            turn2 = InterviewTurn(
                session_id=session.id,
                turn_index=1,
                question_text="Tell me about a time you resolved a critical production incident under pressure.",
                question_category=QuestionCategory.behavioral,
                question_difficulty="hard",
                raw_transcript="When our primary cache cluster degraded, I analyzed thread pools, identified socket starvation, and deployed connection pooling.",
                audio_metrics={"speech_rate_wpm": 138.0, "silence_ratio": 0.06, "filler_word_rate": 0.01},
                eval_scores={"composite_score": 0.84, "depth": 0.86, "clarity": 0.82},
            )
            db.add_all([turn1, turn2])
            await db.commit()
            await db.refresh(session)
            session_id = str(session.id)

        session_resp = await client.get(
            f"/api/v1/interview/session/{session_id}",
            headers={"Authorization": f"Bearer {candidate_token}"},
        )
        assert session_resp.status_code == 200, f"Session fetch failed: {session_resp.text}"
        assert session_resp.json()["aggregate_score"] == 84.0
        print(f"  [PASS] Adaptive interview completed with aggregate score 84.0")

        # Step 4: Specialized Round - 8-Pillar System Design Studio
        print("\n--- Step 4: 8-Pillar System Design & Anti-Buzzword Evaluation ---")
        sd_resp = await client.get("/api/v1/system-design/scenarios", headers={"Authorization": f"Bearer {candidate_token}"})
        assert sd_resp.status_code == 200
        scenarios = sd_resp.json()
        assert len(scenarios) >= 3

        sd_eval_resp = await client.post(
            "/api/v1/system-design/evaluate",
            headers={"Authorization": f"Bearer {candidate_token}"},
            json={
                "session_id": session_id,
                "problem_title": "Design a Distributed Rate Limiter for an API Gateway",
                "problem_prompt": "Design a resilient, low-latency distributed rate limiter.",
                "architecture_sections": {
                    "requirements": "Throttle 500k QPS across global edge regions with sub-2ms overhead.",
                    "non_functional": "High availability, eventual consistency across regions, fallback open.",
                    "high_level": "Client -> Edge Envoy Proxy -> Local Cache Filter -> Central Redis Cluster via Token Bucket.",
                    "data_model": "Redis Hash storing tokens, last_updated_epoch, capacity, refill_rate.",
                    "api_design": "HTTP 429 Too Many Requests with X-RateLimit-Remaining and Retry-After headers.",
                    "scalability": "Consistent hashing across 32 Redis shards with client-side batching.",
                    "resilience": "Circuit breaker fallback to local memory limit when Redis latency exceeds 5ms.",
                    "trade_offs": "Sacrifice strict global consistency during partition to preserve sub-millisecond p99 SLA.",
                },
            },
        )
        assert sd_eval_resp.status_code == 200, f"System design eval failed: {sd_eval_resp.text}"
        sd_eval = sd_eval_resp.json()
        assert sd_eval["overall_score"] >= 60.0
        assert "buzzword_analysis" in sd_eval
        print(f"  [PASS] System design evaluation complete. Score: {sd_eval['overall_score']}%, Tier: {sd_eval['tier']}")

        # Step 5: Candidate AI Twin Sync & Feature 16 Explainable AI
        print("\n--- Step 5: Candidate AI Twin & Feature 16 Explainable AI ---")
        async with AsyncSessionLocal() as db:
            twin_engine = CandidateTwinEngine()
            twin = await twin_engine.sync_twin_from_history(db, candidate_user.id)
            await db.commit()
            assert twin is not None
            assert twin.overall_readiness_score > 0.0
            print(f"  [PASS] Candidate Twin synchronized. Overall readiness: {twin.overall_readiness_score:.1f}")

        twin_resp = await client.get("/api/v1/candidate-twin/my", headers={"Authorization": f"Bearer {candidate_token}"})
        assert twin_resp.status_code == 200, f"Get twin failed: {twin_resp.text}"
        twin_json = twin_resp.json()
        assert twin_json["overall_readiness_score"] > 0

        # Feature 16: Explainable AI Dimension Rationale
        explain_resp = await client.get(
            "/api/v1/candidate-twin/my/explain/overall_readiness",
            headers={"Authorization": f"Bearer {candidate_token}"},
        )
        assert explain_resp.status_code == 200, f"Explain score failed: {explain_resp.text}"
        explain_data = explain_resp.json()
        assert "score_rationale" in explain_data
        assert len(explain_data["evidence_found"]) > 0
        assert len(explain_data["actionable_improvement_roadmap"]) > 0
        print(f"  [PASS] Feature 16 Explainable AI generated rationale with {len(explain_data['evidence_found'])} evidence points")

        # Step 6: Personalized Learning Engine (7-Day Plan & Reassessment)
        print("\n--- Step 6: Personalized Learning Engine & Reassessment Loop ---")
        plan_gen_resp = await client.post(
            "/api/v1/learning/plans/generate",
            headers={"Authorization": f"Bearer {candidate_token}"},
            json={
                "skill_name": "Kafka Distributed Messaging",
                "target_role": "Staff Infrastructure Engineer",
            },
        )
        assert plan_gen_resp.status_code == 201, f"Plan gen failed: {plan_gen_resp.text}"
        plan_data = plan_gen_resp.json()
        plan_id = plan_data["id"]
        assert len(plan_data["daily_schedule"]) == 7
        assert len(plan_data["reassessment_quiz"]) == 5
        print(f"  [PASS] Generated 7-day curriculum: '{plan_data['title']}' with 5-point reassessment")

        # Complete Day 1 milestone
        ms_resp = await client.post(
            f"/api/v1/learning/plans/{plan_id}/milestone/1",
            headers={"Authorization": f"Bearer {candidate_token}"},
        )
        assert ms_resp.status_code == 200
        assert ms_resp.json()["daily_schedule"][0]["is_completed"] is True
        print("  [PASS] Day 1 milestone completed")

        # Submit Reassessment Quiz
        reassess_resp = await client.post(
            f"/api/v1/learning/plans/{plan_id}/reassess",
            headers={"Authorization": f"Bearer {candidate_token}"},
            json={
                "answers": {
                    "0": "Kafka uses log segments, zero-copy OS sendfile, and sequential disk I/O.",
                    "1": "Consumer group rebalances are orchestrated via group coordinator using heartbeats.",
                    "2": "Idempotent producers use producer ID and monotonic sequence numbers per partition.",
                    "3": "Tuning linger.ms and batch.size maximizes batching efficiency.",
                    "4": "In-sync replicas (ISR) and acks=all guarantee zero data loss.",
                }
            },
        )
        assert reassess_resp.status_code == 200, f"Reassessment failed: {reassess_resp.text}"
        reassess_data = reassess_resp.json()
        assert reassess_data["reassessment_score"] >= 75.0
        assert reassess_data["gap_resolved"] is True
        print(f"  [PASS] Reassessment passed: {reassess_data['reassessment_score']}%, Gap resolved: {reassess_data['gap_resolved']}")

        # Step 7: Recruiter Copilot & Comparative Decision Matrix
        print("\n--- Step 7: Recruiter Copilot & Talent Pipeline ---")
        req_resp = await client.post(
            "/api/v1/recruiter/requisitions",
            headers={"Authorization": f"Bearer {recruiter_token}"},
            json={
                "title": "Principal Infrastructure Architect",
                "department": "Platform Core",
                "seniority_level": "L6 / Principal",
                "required_skills": ["Distributed Systems", "Redis", "PostgreSQL", "Kafka"],
                "rubric_weights": {"system_design": 0.4, "technical": 0.3, "behavioral": 0.3},
                "hiring_threshold": 75.0,
            },
        )
        assert req_resp.status_code == 201, f"Req creation failed: {req_resp.text}"
        req_id = req_resp.json()["id"]

        # Invite Candidate
        invite_resp = await client.post(
            f"/api/v1/recruiter/requisitions/{req_id}/invite",
            headers={"Authorization": f"Bearer {recruiter_token}"},
            json={"candidate_id": str(candidate_user.id)},
        )
        assert invite_resp.status_code in [200, 201], f"Invite failed: {invite_resp.text}"

        # Evaluate Candidate
        eval_cand_resp = await client.post(
            f"/api/v1/recruiter/requisitions/{req_id}/evaluate/{candidate_user.id}",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert eval_cand_resp.status_code == 200, f"Eval cand failed: {eval_cand_resp.text}"
        cand_eval = eval_cand_resp.json()
        eval_score = cand_eval.get("composite_score") or cand_eval.get("score") or 0.0
        eval_rec = cand_eval.get("hiring_recommendation") or cand_eval.get("recommendation") or "Review"
        assert eval_score >= 70.0
        print(f"  [PASS] Candidate evaluated. Score: {eval_score}, Recommendation: {eval_rec}")

        # Compare Candidates Matrix
        compare_resp = await client.post(
            f"/api/v1/recruiter/requisitions/{req_id}/compare",
            headers={"Authorization": f"Bearer {recruiter_token}"},
            json={"candidate_ids": [str(candidate_user.id)]},
        )
        assert compare_resp.status_code == 200
        matrix_data = compare_resp.json()
        assert len(matrix_data["matrix"]) == 1
        print(f"  [PASS] Comparative matrix rendered for {matrix_data['total_compared']} candidate(s)")

        # Talent pool search
        pool_resp = await client.get(
            "/api/v1/recruiter/talent-pool/search?min_readiness=60",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert pool_resp.status_code == 200
        assert len(pool_resp.json()) >= 1
        print(f"  [PASS] Talent pool search returned {len(pool_resp.json())} candidate match(es)")

        # Step 8: Enterprise Analytics & Executive Reporting
        print("\n--- Step 8: Enterprise Analytics & Executive Telemetry ---")
        overview_resp = await client.get(
            "/api/v1/analytics/enterprise/overview",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert overview_resp.status_code == 200
        overview = overview_resp.json()
        assert overview["total_candidates"] >= 1
        assert overview["active_requisitions"] >= 1
        print(f"  [PASS] Enterprise overview: {overview['total_candidates']} candidates, {overview['completed_interviews']} interviews")

        funnel_resp = await client.get(
            "/api/v1/analytics/enterprise/recruiter-funnel",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert funnel_resp.status_code == 200
        assert len(funnel_resp.json()["stages"]) > 0

        shortage_resp = await client.get(
            "/api/v1/analytics/enterprise/skill-shortages",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert shortage_resp.status_code == 200

        impact_resp = await client.get(
            "/api/v1/analytics/enterprise/learning-impact",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert impact_resp.status_code == 200
        assert impact_resp.json()["total_plans_generated"] >= 1
        print("  [PASS] Enterprise analytics endpoints verified with real data")

        # Step 9: Observability, Circuit Breakers & Cryptographic Audit
        print("\n--- Step 9: Observability, Resilience & Cryptographic Audit ---")
        metrics_resp = await client.get(
            "/api/v1/observability/metrics/summary",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert metrics_resp.status_code == 200
        assert "overall_latency" in metrics_resp.json()

        health_resp = await client.get("/api/v1/observability/health/deep")
        assert health_resp.status_code == 200
        assert health_resp.json()["status"] in ["healthy", "degraded"]

        # Cryptographic Audit Verification
        async with AsyncSessionLocal() as db:
            audit_result = await verify_audit_chain(db, org.id)
            assert audit_result["is_valid"] is True, f"Audit log hash chain validation failed: {audit_result}"
            print("  [PASS] Cryptographic SHA-256 audit chain verified intact (zero tampering detected)")

    print("\n========================================================")
    print("=== PHASE 10 FULL-STACK E2E SUITE COMPLETED WITH 100% SUCCESS ===")
    print("========================================================\n")


if __name__ == "__main__":
    asyncio.run(test_phase10_fullstack_e2e())
