import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
import uuid
from datetime import UTC, datetime
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.exceptions import CircuitBreakerOpenException, QuotaExceededException
from app.core.security import create_access_token
from app.database import AsyncSessionLocal
from app.main import app
from app.models.organization import Organization, OrganizationTier
from app.models.user import User, UserRole
from app.services.ai_cost_controller import AICostController, calculate_token_cost
from app.services.audit_service import AuditService, record_audit_event, verify_audit_chain
from app.services.circuit_breaker import CircuitBreaker, CircuitBreakerRegistry, CircuitState
from app.services.observability_service import MetricsCollector, run_deep_health_check
from app.services.pii_scrubber import mask_pii_for_logs, restore_pii, scrub_pii


async def test_phase9_complete_suite():
    print("\n========================================================")
    print("=== STARTING PHASE 9: OBSERVABILITY, GOVERNANCE & RESILIENCE TESTS ===")
    print("========================================================")

    async with AsyncSessionLocal() as db:
        # Setup Organization and Users
        org = Organization(
            name=f"Enterprise Tech Corp {uuid.uuid4().hex[:6]}",
            slug=f"techcorp-{uuid.uuid4().hex[:6]}",
            tier=OrganizationTier.enterprise,
        )
        db.add(org)
        await db.flush()

        admin_user = User(
            email=f"admin.{uuid.uuid4().hex[:6]}@techcorp.com",
            full_name="Platform Admin",
            hashed_password="hashed_pw_test_123",
            role=UserRole.admin,
            org_id=org.id,
            is_active=True,
        )
        recruiter_user = User(
            email=f"recruiter.{uuid.uuid4().hex[:6]}@techcorp.com",
            full_name="Enterprise Recruiter",
            hashed_password="hashed_pw_test_123",
            role=UserRole.recruiter,
            org_id=org.id,
            is_active=True,
        )
        candidate_user = User(
            email=f"candidate.{uuid.uuid4().hex[:6]}@gmail.com",
            full_name="Lead Candidate",
            hashed_password="hashed_pw_test_123",
            role=UserRole.candidate,
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

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    recruiter_headers = {"Authorization": f"Bearer {recruiter_token}"}
    candidate_headers = {"Authorization": f"Bearer {candidate_token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:

        # ── 1. TEST ZERO-TRUST PII SCRUBBING & RESTORATION ────────────────────
        print("\n--- 1. Testing Zero-Trust PII Scrubber (Feature 20) ---")
        raw_text = (
            "Candidate John Doe with email john.doe@acme-corp.com and phone +1 (555) 234-5678, "
            "SSN 123-45-6789 reported from IP 192.168.1.50 using card 4532-1234-5678-9012."
        )
        scrubbed, surrogate_map = scrub_pii(raw_text)
        print(f"Scrubbed Text: {scrubbed}")
        assert "john.doe@acme-corp.com" not in scrubbed
        assert "123-45-6789" not in scrubbed
        assert "4532-1234-5678-9012" not in scrubbed
        assert "[EMAIL_1]" in scrubbed
        assert "[PHONE_1]" in scrubbed
        assert "[SSN_1]" in scrubbed
        assert "[CARD_1]" in scrubbed
        assert "[IP_1]" in scrubbed
        print("[PASS] PII redacted into reversible cryptographic surrogate tokens.")

        restored = restore_pii(scrubbed, surrogate_map)
        assert restored == raw_text
        print("[PASS] PII successfully restored to exact original text using token map.")

        masked_log = mask_pii_for_logs(raw_text)
        assert "[EMAIL_REDACTED]" in masked_log
        assert "[SSN_REDACTED]" in masked_log
        assert "[CARD_REDACTED]" in masked_log
        print("[PASS] Permanent log masking verified.")

        # ── 2. TEST ENTERPRISE CIRCUIT BREAKER & BULKHEAD ─────────────────────
        print("\n--- 2. Testing Circuit Breakers & Resilience (Feature 19) ---")
        breaker = CircuitBreaker("test_service", failure_threshold=3, recovery_timeout_s=0.2)
        assert breaker.state == CircuitState.CLOSED

        async def _failing_op():
            raise ConnectionError("Service unreachable")

        async def _fallback_op():
            return "degraded_fallback_result"

        # Execute 3 failing calls to trip the breaker
        for i in range(3):
            raised = False
            try:
                await breaker.call(_failing_op)
            except ConnectionError:
                raised = True
            assert raised, "Expected ConnectionError from _failing_op"

        assert breaker.state == CircuitState.OPEN
        print(f"[PASS] Circuit breaker correctly tripped to {breaker.state.value} after 3 failures.")

        # In OPEN state, fallback should be invoked immediately
        fallback_res = await breaker.call(_failing_op, fallback=_fallback_op)
        assert fallback_res == "degraded_fallback_result"
        print("[PASS] Fast-fail graceful degradation fallback executed while OPEN.")

        # Without fallback in OPEN state, CircuitBreakerOpenException is raised
        raised_cb = False
        try:
            await breaker.call(_failing_op)
        except CircuitBreakerOpenException:
            raised_cb = True
        assert raised_cb, "Expected CircuitBreakerOpenException when no fallback is provided in OPEN state"
        print("[PASS] CircuitBreakerOpenException raised when no fallback provided.")

        # Wait recovery timeout to transition to HALF_OPEN
        await asyncio.sleep(0.25)
        assert breaker.state == CircuitState.HALF_OPEN
        print(f"[PASS] Circuit breaker transitioned to {breaker.state.value} after recovery timeout.")

        async def _success_op():
            return "healthy_result"

        # 2 successful probe calls should transition back to CLOSED
        await breaker.call(_success_op)
        await breaker.call(_success_op)
        assert breaker.state == CircuitState.CLOSED
        print("[PASS] Circuit breaker recovered to CLOSED after successful probes.")

        # Test Resilience REST endpoints
        res_cb = await client.get("/api/v1/resilience/circuit-breakers", headers=admin_headers)
        assert res_cb.status_code == 200
        cb_data = res_cb.json()
        assert len(cb_data["circuit_breakers"]) >= 5
        print(f"[PASS] GET /api/v1/resilience/circuit-breakers: {len(cb_data['circuit_breakers'])} breakers active.")

        # Trip drill
        trip_res = await client.post("/api/v1/resilience/circuit-breakers/llm_reasoning/trip", headers=admin_headers)
        assert trip_res.status_code == 200
        assert trip_res.json()["current_state"] == "OPEN"
        print("[PASS] POST /api/v1/resilience/circuit-breakers/llm_reasoning/trip: Drill successful.")

        # Reset drill
        reset_res = await client.post("/api/v1/resilience/circuit-breakers/llm_reasoning/reset", headers=admin_headers)
        assert reset_res.status_code == 200
        assert reset_res.json()["current_state"] == "CLOSED"
        print("[PASS] POST /api/v1/resilience/circuit-breakers/llm_reasoning/reset: Breaker reset to CLOSED.")

        # ── 3. TEST AI COST CONTROL & BUDGET GOVERNANCE ────────────────────────
        print("\n--- 3. Testing AI Cost Control & Model Routing (Feature 18) ---")
        cost_fast = calculate_token_cost("fast", 1000, 500)
        cost_reasoning = calculate_token_cost("reasoning", 1000, 500)
        assert cost_reasoning > cost_fast
        print(f"[PASS] Token cost calculated: Fast=${cost_fast:.6f}, Reasoning=${cost_reasoning:.6f}")

        async with AsyncSessionLocal() as db:
            controller = AICostController(db)
            b = await controller.get_or_create_budget(org.id)
            b.monthly_budget_usd = 10.0
            b.current_spend_usd = 0.0
            b.hard_limit_action = "degrade_to_cheap"
            db.add(b)
            await db.flush()

            # Within budget
            tier = await controller.authorize_tier(org.id, "reasoning")
            assert tier == "reasoning"

            # Spend exceeds budget -> should degrade to fast
            b.current_spend_usd = 15.0
            db.add(b)
            await db.flush()
            tier = await controller.authorize_tier(org.id, "reasoning")
            assert tier == "fast"
            print("[PASS] AI Budget limit reached: Tier automatically degraded to 'fast'.")

            # Block mode
            b.hard_limit_action = "block"
            db.add(b)
            await db.flush()
            quota_raised = False
            try:
                await controller.authorize_tier(org.id, "reasoning")
            except QuotaExceededException:
                quota_raised = True
            assert quota_raised, "Expected QuotaExceededException when budget is exceeded and action is block"
            print("[PASS] AI Budget limit reached in block mode: QuotaExceededException raised.")

            # Record invocation
            log_entry = await controller.record_invocation(
                operation="system_design_eval",
                model_name="gpt-4o",
                model_tier="reasoning",
                prompt_tokens=1500,
                completion_tokens=800,
                latency_ms=1250.0,
                org_id=org.id,
                user_id=candidate_user.id,
            )
            assert log_entry.total_tokens == 2300
            assert log_entry.estimated_cost_usd > 0.0
            await db.commit()

        # REST API AI Governance
        res_pricing = await client.get("/api/v1/ai-governance/pricing")
        assert res_pricing.status_code == 200
        assert len(res_pricing.json()["pricing"]) == 3
        print("[PASS] GET /api/v1/ai-governance/pricing: Returned 3 tiered model rate cards.")

        res_budget = await client.get("/api/v1/ai-governance/budget", headers=recruiter_headers)
        assert res_budget.status_code == 200
        assert res_budget.json()["monthly_budget_usd"] == 10.0
        print("[PASS] GET /api/v1/ai-governance/budget: Retrieved budget utilization.")

        # Update budget
        update_budget_res = await client.post(
            "/api/v1/ai-governance/budget",
            headers=admin_headers,
            json={"monthly_budget_usd": 750.0, "alert_threshold_pct": 0.85, "hard_limit_action": "degrade_to_cheap"},
        )
        assert update_budget_res.status_code == 200
        assert update_budget_res.json()["monthly_budget_usd"] == 750.0
        print("[PASS] POST /api/v1/ai-governance/budget: Updated org budget to $750.00.")

        res_usage = await client.get("/api/v1/ai-governance/usage/my", headers=candidate_headers)
        assert res_usage.status_code == 200
        assert res_usage.json()["total_calls"] >= 1
        print("[PASS] GET /api/v1/ai-governance/usage/my: User usage tracked accurately.")

        # ── 4. TEST TAMPER-EVIDENT AUDIT LOG HASH CHAINING ────────────────────
        print("\n--- 4. Testing Tamper-Evident Audit Log Hash Chaining (Feature 20) ---")
        async with AsyncSessionLocal() as db:
            await record_audit_event(
                db=db,
                action="security.key_rotation",
                entity_type="api_key",
                org_id=org.id,
                user_id=admin_user.id,
                payload={"key_id": "key_primary", "status": "rotated"},
            )
            await record_audit_event(
                db=db,
                action="security.firewall_rule_applied",
                entity_type="firewall",
                org_id=org.id,
                user_id=admin_user.id,
                payload={"ip": "10.0.0.1", "action": "allow"},
            )
            await db.commit()

            verification = await verify_audit_chain(db, org.id)
            assert verification["is_valid"] is True
            print(f"[PASS] Audit log cryptographic chain verified: {verification['total_entries']} entries valid.")

        res_audit = await client.get("/api/v1/audit/verify-integrity", headers=admin_headers)
        assert res_audit.status_code == 200
        assert res_audit.json()["is_valid"] is True
        print("[PASS] GET /api/v1/audit/verify-integrity: Cryptographic proof confirmed via API.")

        # ── 5. TEST OBSERVABILITY, METRICS & DEEP HEALTH CHECK ─────────────────
        print("\n--- 5. Testing Production Observability & Telemetry (Feature 17) ---")
        collector = MetricsCollector.get_instance()
        collector.record_request("/api/v1/interview/answer", 120.5, 200)
        collector.record_request("/api/v1/interview/answer", 240.8, 200)
        collector.record_request("/api/v1/interview/answer", 85.2, 200)
        collector.record_request("/api/v1/interview/answer", 410.0, 500)

        summary = collector.get_summary()
        assert summary.overall_latency.sample_count >= 4
        assert summary.overall_latency.p50_ms > 0
        assert summary.overall_latency.p95_ms > 0
        print(f"[PASS] Latency percentiles computed: p50={summary.overall_latency.p50_ms}ms, p95={summary.overall_latency.p95_ms}ms, p99={summary.overall_latency.p99_ms}ms")

        # Deep health check
        health_res = await run_deep_health_check()
        assert health_res.status in ("healthy", "degraded")
        assert "database" in health_res.components
        assert health_res.components["database"].status == "healthy"
        print(f"[PASS] Deep health check executed: DB healthy with {health_res.components['database'].latency_ms}ms latency.")

        # Prometheus /metrics endpoint
        res_prom = await client.get("/metrics")
        assert res_prom.status_code == 200
        assert "http_requests_total" in res_prom.text
        assert "http_request_latency_p95_milliseconds" in res_prom.text
        print("[PASS] GET /metrics: Valid Prometheus exposition format verified.")

        # Observability summary endpoint
        res_obs = await client.get("/api/v1/observability/metrics/summary")
        assert res_obs.status_code == 200
        assert "overall_latency" in res_obs.json()
        print("[PASS] GET /api/v1/observability/metrics/summary: Structured telemetry returned.")

        # Deep health endpoint
        res_deep = await client.get("/api/v1/observability/health/deep")
        assert res_deep.status_code == 200
        assert res_deep.json()["components"]["database"]["status"] == "healthy"
        print("[PASS] GET /api/v1/observability/health/deep: Multi-component status verified.")

        # ── 6. TEST SECURITY HEADERS & RATE LIMITING ──────────────────────────
        print("\n--- 6. Testing Security Headers & Rate Limiting (Feature 20) ---")
        ping_res = await client.get("/api/v1/ai-governance/pricing")
        headers = ping_res.headers
        assert "strict-transport-security" in headers
        assert "x-content-type-options" in headers
        assert headers["x-content-type-options"] == "nosniff"
        assert "x-frame-options" in headers
        assert headers["x-frame-options"] == "DENY"
        assert "content-security-policy" in headers
        assert "x-ratelimit-limit" in headers
        print("[PASS] Security headers (HSTS, CSP, X-Frame-Options, X-Content-Type-Options) verified on response.")

        # ── 7. TEST ENTERPRISE PLATFORM ANALYTICS ─────────────────────────────
        print("\n--- 7. Testing Enterprise Platform Analytics (Feature 15) ---")
        res_overview = await client.get("/api/v1/analytics/enterprise/overview", headers=recruiter_headers)
        assert res_overview.status_code == 200
        ov_data = res_overview.json()
        assert "total_candidates" in ov_data
        assert "readiness_distribution" in ov_data
        assert "domain_breakdown" in ov_data
        print(f"[PASS] GET /api/v1/analytics/enterprise/overview: {ov_data['total_candidates']} candidate(s), readiness avg {ov_data['overall_readiness_avg']}")

        res_funnel = await client.get("/api/v1/analytics/enterprise/recruiter-funnel", headers=recruiter_headers)
        assert res_funnel.status_code == 200
        assert "stages" in res_funnel.json()
        print(f"[PASS] GET /api/v1/analytics/enterprise/recruiter-funnel: Funnel stages retrieved.")

        res_shortages = await client.get("/api/v1/analytics/enterprise/skill-shortages", headers=recruiter_headers)
        assert res_shortages.status_code == 200
        assert "shortages" in res_shortages.json()
        print(f"[PASS] GET /api/v1/analytics/enterprise/skill-shortages: Top shortage areas analyzed.")

        res_impact = await client.get("/api/v1/analytics/enterprise/learning-impact", headers=recruiter_headers)
        assert res_impact.status_code == 200
        assert "completion_rate_pct" in res_impact.json()
        print(f"[PASS] GET /api/v1/analytics/enterprise/learning-impact: Learning impact metrics verified.")

    print("\n========================================================")
    print("=== ALL PHASE 9 OBSERVABILITY, GOVERNANCE & RESILIENCE TESTS PASSED ===")
    print("========================================================\n")


if __name__ == "__main__":
    asyncio.run(test_phase9_complete_suite())
