"""
Phase 16 Test Suite: Enterprise Analytics, Distributed Tracing & Observability
Validates:
1. Talent Supply vs Demand Intelligence with skill shortage classifications & time-to-fill predictions.
2. Enterprise Platform ROI & Executive BI metrics (recruiter hours saved, cost savings, AI expense multiple).
3. Distributed Tracing & Correlation ID injection (X-Correlation-ID header, span waterfall).
4. Real-time Alerting & Anomaly Engine (rule evaluation, alert listing, incident acknowledgment).
5. Prometheus Metrics Exporter (HTTP exposition format, counters, gauges).
6. Deep Health Diagnostic Probes (database, redis, vector, sandbox, cloud storage).
7. Role-Based Access Control on Enterprise Analytics endpoints.
"""

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
from app.models.ai_governance import AIUsageLog, ModelTier
from app.models.candidate_twin import CandidateTwin
from app.models.interview_session import InterviewSession, QuestionDifficulty, SessionStatus
from app.models.learning_plan import LearningPlan, LearningPlanStatus
from app.models.recruiter import RecruiterRequisition, RequisitionStatus
from app.models.skill_graph import CandidateSkillMastery
from app.models.user import User, UserRole
from app.services.observability_service import AlertEngine, MetricsCollector, TraceCollector


async def test_phase16_analytics_observability() -> None:
    print("\n================================================================")
    print("=== STARTING PHASE 16: ENTERPRISE ANALYTICS & OBSERVABILITY ===")
    print("================================================================\n")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # ── 1. SEEDING TEST ACTORS & TELEMETRY ──────────────────────────────
        print("--- 1. Seeding Test Actors & Platform Telemetry ---")
        async with AsyncSessionLocal() as session:
            admin_id = uuid.uuid4()
            recruiter_id = uuid.uuid4()
            candidate_id = uuid.uuid4()

            admin = User(
                id=admin_id,
                email=f"admin_{admin_id.hex[:6]}@enterprise.io",
                full_name="Platform Admin",
                hashed_password="AdminPass123!",
                role=UserRole.admin,
                is_active=True,
            )
            recruiter = User(
                id=recruiter_id,
                email=f"recruiter_{recruiter_id.hex[:6]}@enterprise.io",
                full_name="Enterprise Recruiter",
                hashed_password="RecruiterPass123!",
                role=UserRole.recruiter,
                is_active=True,
            )
            candidate = User(
                id=candidate_id,
                email=f"cand_{candidate_id.hex[:6]}@enterprise.io",
                full_name="Alice Architect",
                hashed_password="CandPass123!",
                role=UserRole.candidate,
                is_active=True,
            )
            session.add_all([admin, recruiter, candidate])
            await session.flush()

            # Seed Requisition with required skills
            req = RecruiterRequisition(
                id=uuid.uuid4(),
                created_by=recruiter_id,
                title="Principal Distributed Systems Architect",
                department="Engineering",
                seniority_level="principal",
                required_skills=["distributed-systems", "raft-consensus", "kafka", "python"],
                rubric_weights={"technical": 0.35, "system_design": 0.35, "coding": 0.15, "behavioral": 0.15},
                hiring_threshold=85.0,
                status=RequisitionStatus.active,
            )
            session.add(req)

            # Seed Verified Skill DAG Masteries for Candidate
            m1 = CandidateSkillMastery(
                id=uuid.uuid4(),
                user_id=candidate_id,
                skill_id="distributed-systems",
                mastery_score=92.0,
                confidence=0.95,
            )
            m2 = CandidateSkillMastery(
                id=uuid.uuid4(),
                user_id=candidate_id,
                skill_id="python",
                mastery_score=88.0,
                confidence=0.90,
            )
            session.add_all([m1, m2])

            # Seed Completed Interview Session
            sess1 = InterviewSession(
                id=uuid.uuid4(),
                user_id=candidate_id,
                status=SessionStatus.completed,
                target_question_count=5,
                current_question_index=5,
                current_difficulty=QuestionDifficulty.hard,
                aggregate_score=89.5,
                started_at=datetime.now(UTC) - timedelta(days=2),
                completed_at=datetime.now(UTC) - timedelta(days=2, minutes=-45),
            )
            session.add(sess1)

            # Seed Completed Learning Plan
            plan1 = LearningPlan(
                id=uuid.uuid4(),
                user_id=candidate_id,
                title="Advanced Raft & Distributed Invariants",
                status=LearningPlanStatus.completed,
                target_completion_days=7,
                current_day=7,
                reassessment_score=88.0,
                detected_gap="raft-consensus",
                daily_schedule=[{"day": 1, "topic": "Leader Election"}],
                reassessment_quiz=[],
            )
            session.add(plan1)

            # Seed AI Usage Log for Cost Tracking
            log1 = AIUsageLog(
                id=uuid.uuid4(),
                user_id=candidate_id,
                model_name="gpt-4o",
                model_tier=ModelTier.reasoning,
                operation="interview_evaluation",
                prompt_tokens=1500,
                completion_tokens=400,
                total_tokens=1900,
                estimated_cost_usd=0.015,
                latency_ms=850.0,
            )
            session.add(log1)

            await session.commit()
            print("  [PASS] Seeding test entities and operational telemetry successful.")

        admin_token = create_access_token(admin_id, UserRole.admin.value)
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        recruiter_token = create_access_token(recruiter_id, UserRole.recruiter.value)
        recruiter_headers = {"Authorization": f"Bearer {recruiter_token}"}
        candidate_token = create_access_token(candidate_id, UserRole.candidate.value)
        cand_headers = {"Authorization": f"Bearer {candidate_token}"}

        # ── 2. TALENT SUPPLY VS DEMAND INTELLIGENCE ──────────────────────────
        print("\n--- 2. Validating Talent Supply vs Demand Intelligence ---")
        sd_res = await client.get("/api/v1/analytics/enterprise/supply-demand", headers=recruiter_headers)
        assert sd_res.status_code == 200, f"Expected 200, got {sd_res.status_code}: {sd_res.text}"
        sd_data = sd_res.json()

        assert "total_skills_tracked" in sd_data
        assert "critical_shortage_count" in sd_data
        assert "skills" in sd_data
        assert len(sd_data["skills"]) > 0

        skill_names = [s["skill_name"] for s in sd_data["skills"]]
        assert "distributed-systems" in skill_names or "raft-consensus" in skill_names
        print(f"  [PASS] Supply-Demand returned {sd_data['total_skills_tracked']} skills, {sd_data['critical_shortage_count']} critical shortages.")

        sample_skill = sd_data["skills"][0]
        assert "candidate_supply_count" in sample_skill
        assert "requisition_demand_count" in sample_skill
        assert "supply_demand_ratio" in sample_skill
        assert sample_skill["shortage_level"] in ("critical", "moderate", "balanced", "surplus")
        assert sample_skill["projected_time_to_fill_days"] > 0
        print(f"  [PASS] Sample skill '{sample_skill['skill_name']}': Ratio={sample_skill['supply_demand_ratio']}, Level={sample_skill['shortage_level']}, Est. Fill={sample_skill['projected_time_to_fill_days']}d.")

        # ── 3. ENTERPRISE PLATFORM ROI & EXECUTIVE BI ────────────────────────
        print("\n--- 3. Testing Enterprise Platform ROI & Executive BI Metrics ---")
        roi_res = await client.get("/api/v1/analytics/enterprise/roi-metrics", headers=recruiter_headers)
        assert roi_res.status_code == 200, f"Expected 200, got {roi_res.status_code}: {roi_res.text}"
        roi_data = roi_res.json()

        assert roi_data["total_interviews_conducted"] >= 1
        assert roi_data["recruiter_hours_saved"] >= 2.5
        assert roi_data["cost_savings_usd"] > 0
        assert roi_data["ai_infrastructure_cost_usd"] > 0
        assert roi_data["net_roi_multiple"] > 0
        assert roi_data["avg_candidate_score_lift"] > 0
        assert "Engineering" in roi_data["department_metrics"]
        print(f"  [PASS] ROI Metrics: Interviews={roi_data['total_interviews_conducted']}, Hours Saved={roi_data['recruiter_hours_saved']}h, Savings=${roi_data['cost_savings_usd']}, Net ROI Multiple={roi_data['net_roi_multiple']}x.")

        # ── 4. RBAC PROTECTION ON ENTERPRISE ANALYTICS ───────────────────────
        print("\n--- 4. Validating Role-Based Access Control on Analytics Endpoints ---")
        unauth_sd = await client.get("/api/v1/analytics/enterprise/supply-demand", headers=cand_headers)
        assert unauth_sd.status_code in (401, 403), f"Expected 401/403 for candidate on recruiter endpoint, got {unauth_sd.status_code}"
        print("  [PASS] Candidate role properly rejected from recruiter enterprise analytics.")

        # ── 5. DISTRIBUTED TRACING & CORRELATION INJECTION ───────────────────
        print("\n--- 5. Testing Distributed Tracing & Correlation ID Injection ---")
        custom_corr = f"corr-test-{uuid.uuid4().hex[:8]}"
        req_with_corr = await client.get(
            "/api/v1/analytics/enterprise/overview",
            headers={**recruiter_headers, "X-Correlation-ID": custom_corr},
        )
        assert req_with_corr.status_code == 200
        assert req_with_corr.headers.get("X-Correlation-ID") == custom_corr
        print(f"  [PASS] Custom Correlation ID {custom_corr} propagated cleanly in response headers.")

        # Record synthetic multi-service trace
        synth_res = await client.post(
            "/api/v1/observability/traces",
            params={
                "root_endpoint": "POST /interview/session",
                "duration_ms": 142.5,
                "service": "langgraph_engine",
                "status": "ok",
            },
            headers=admin_headers,
        )
        assert synth_res.status_code == 201, f"Expected 201, got {synth_res.status_code}: {synth_res.text}"
        synth_trace = synth_res.json()
        assert synth_trace["root_endpoint"] == "POST /interview/session"
        assert len(synth_trace["spans"]) >= 3
        trace_id = synth_trace["trace_id"]
        print(f"  [PASS] Synthetic trace recorded with ID: {trace_id}.")

        # Retrieve trace by ID
        get_trace_res = await client.get(f"/api/v1/observability/traces/{trace_id}", headers=admin_headers)
        assert get_trace_res.status_code == 200
        retrieved_trace = get_trace_res.json()
        assert retrieved_trace["trace_id"] == trace_id
        assert retrieved_trace["total_duration_ms"] == 142.5
        print(f"  [PASS] Retrieved trace {trace_id} with {len(retrieved_trace['spans'])} spans in waterfall.")

        # List traces
        list_traces_res = await client.get("/api/v1/observability/traces?limit=10", headers=admin_headers)
        assert list_traces_res.status_code == 200
        assert list_traces_res.json()["total_traces"] > 0
        print(f"  [PASS] Trace listing returned {list_traces_res.json()['total_traces']} traces.")

        # ── 6. REAL-TIME ALERTING & INCIDENT MANAGEMENT ──────────────────────
        print("\n--- 6. Testing Real-time Alerting & Anomaly Engine ---")
        alert_engine = AlertEngine.get_instance()
        test_alert = alert_engine.trigger_alert(
            rule="p99_latency_spike",
            title="High System Design Eval Latency",
            message="P99 latency on system-design evaluation reached 2450ms.",
            severity="warning",
            metric_value=2450.0,
            threshold_value=2000.0,
        )
        assert test_alert.id is not None

        # Fetch active alerts
        alerts_res = await client.get("/api/v1/observability/alerts?only_active=true", headers=admin_headers)
        assert alerts_res.status_code == 200
        alerts_data = alerts_res.json()
        assert alerts_data["active_count"] >= 1
        found_alert = any(a["id"] == test_alert.id for a in alerts_data["alerts"])
        assert found_alert
        print(f"  [PASS] Triggered alert {test_alert.id} present in active alerts list.")

        # Acknowledge the alert
        ack_res = await client.post(f"/api/v1/observability/alerts/{test_alert.id}/acknowledge", headers=admin_headers)
        assert ack_res.status_code == 200
        ack_data = ack_res.json()
        assert ack_data["acknowledged"] is True
        print(f"  [PASS] Alert {test_alert.id} acknowledged successfully.")

        # Confirm acknowledged status
        alerts_after = await client.get("/api/v1/observability/alerts?only_active=true", headers=admin_headers)
        still_active = any(a["id"] == test_alert.id for a in alerts_after.json()["alerts"])
        assert not still_active
        print("  [PASS] Alert correctly removed from active incident queue.")

        # ── 7. PROMETHEUS METRICS EXPOSITION ─────────────────────────────────
        print("\n--- 7. Validating Prometheus Text Format Exporter ---")
        prom_res = await client.get("/metrics")
        assert prom_res.status_code == 200
        assert "# HELP http_requests_total" in prom_res.text
        assert "# TYPE http_requests_total" in prom_res.text
        assert "http_requests_total" in prom_res.text
        print("  [PASS] Prometheus endpoint `/metrics` returned valid exposition text format.")

        prom_sub_res = await client.get("/api/v1/observability/metrics/prometheus", headers=admin_headers)
        assert prom_sub_res.status_code == 200
        assert "# HELP" in prom_sub_res.text
        print("  [PASS] Router `/api/v1/observability/metrics/prometheus` returned valid exposition text format.")

        # ── 8. DEEP HEALTH PROBE DIAGNOSTICS ─────────────────────────────────
        print("\n--- 8. Testing Deep Health Check Diagnostics ---")
        health_res = await client.get("/api/v1/observability/health/deep", headers=admin_headers)
        assert health_res.status_code == 200
        health_data = health_res.json()
        assert health_data["status"] in ("healthy", "degraded", "critical")
        assert "database" in health_data["components"]
        assert "redis" in health_data["components"]
        assert "vector_storage" in health_data["components"]
        assert "code_sandbox" in health_data["components"]
        assert "cloud_storage" in health_data["components"]
        print(f"  [PASS] Deep health check passed with status: {health_data['status']}. 5 components probed.")

    print("\n================================================================")
    print("=== ALL PHASE 16 ANALYTICS & OBSERVABILITY TESTS PASSED (100%) ===")
    print("================================================================\n")


if __name__ == "__main__":
    asyncio.run(test_phase16_analytics_observability())
