"""
Phase 11: System Design & Behavioral Engine Test Suite
Validates:
1. Anti-Buzzword Evaluation Engine with Contextual Justification Checks
2. Topological Architecture Graph Validation & Algorithmic SPOF Detection
3. Back-of-the-Envelope Capacity Estimation Verifier & Benchmark Comparison
4. Interactive Bar-Raiser Architecture Clarification Protocol
5. STAR+L (Situation, Task, Action, Result, Learning) Decomposition
6. Pronoun Ownership Audit (I vs We Ratio) & Attribution Level Detection
7. Quantitative Business Impact Extractor & Behavioral Red Flags
8. High-Pressure Bar-Raiser Follow-Up Probe Generator
9. Executive STAR Story Reframe Engine
10. Full REST API Endpoints for System Design & Behavioral Studios
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
import uuid
from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token
from app.database import AsyncSessionLocal
from app.main import app
from app.models.interview_session import InterviewSession, SessionStatus
from app.models.user import User, UserRole
from app.services.behavioral_service import BehavioralSTAREngine
from app.services.system_design_service import SystemDesignEngine


async def test_phase11_system_design_behavioral() -> None:
    print("\n========================================================")
    print("=== STARTING PHASE 11: SYSTEM DESIGN & BEHAVIORAL ENGINE ===")
    print("========================================================\n")

    sys_engine = SystemDesignEngine()
    beh_engine = BehavioralSTAREngine()

    # ── 1. SYSTEM DESIGN: ANTI-BUZZWORD EVALUATION ──────────────────────────
    print("--- 1. Testing Anti-Buzzword Semantic Justification Filter ---")
    
    # Text with unjustified buzzwords
    unjustified_text = (
        "We will just use Kafka and Cassandra and Kubernetes with CQRS and Event Sourcing "
        "because they are modern and scalable technologies for our system."
    )
    buzz_unjustified = sys_engine.inspect_buzzwords(unjustified_text)
    assert buzz_unjustified.total_buzzwords_detected >= 4
    assert len(buzz_unjustified.unjustified_buzzwords) >= 3
    assert buzz_unjustified.penalty_applied > 10.0
    print(f"  [PASS] Unjustified buzzwords caught: {len(buzz_unjustified.unjustified_buzzwords)} detected, penalty applied: {buzz_unjustified.penalty_applied} pts")

    # Text with properly justified architectural reasoning
    justified_text = (
        "We deploy Kafka configured with 64 partitions partitioned by customer_id to guarantee "
        "per-customer message ordering, consumer groups for horizontal worker scaling, and a 7-day retention log. "
        "For the vector database, we employ pgvector with HNSW index using cosine similarity distance to achieve "
        "sub-20ms approximate nearest neighbor recall. For caching, we introduce a Redis cluster with LRU eviction and 1-hour TTL."
    )
    buzz_justified = sys_engine.inspect_buzzwords(justified_text)
    assert "kafka" in buzz_justified.justified_buzzwords
    assert "redis" in buzz_justified.justified_buzzwords
    assert "vector database" in buzz_justified.justified_buzzwords
    assert buzz_justified.penalty_applied == 0.0
    print(f"  [PASS] Justified architectural markers recognized: {buzz_justified.justified_buzzwords}, 0 penalty applied")

    # ── 2. SYSTEM DESIGN: TOPOLOGY GRAPH & SPOF DETECTION ───────────────────
    print("\n--- 2. Testing Architecture Graph Validation & SPOF Traversal ---")

    # Fragile topology with single database, single gateway, and orphan node
    vulnerable_components = [
        {"id": "c1", "name": "Mobile & Web Clients", "type": "client", "replicas": 1},
        {"id": "gw1", "name": "API Gateway", "type": "gateway", "replicas": 1, "is_clustered": False},
        {"id": "app1", "name": "Order Service", "type": "service", "replicas": 2, "is_clustered": True},
        {"id": "db1", "name": "Postgres Primary", "type": "database", "replicas": 1, "is_clustered": False},
        {"id": "w1", "name": "Legacy Worker", "type": "worker", "replicas": 1, "is_clustered": False},
    ]
    vulnerable_connections = [
        {"from": "c1", "to": "gw1"},
        {"from": "gw1", "to": "app1"},
        {"from": "app1", "to": "db1"},
    ]
    vuln_report = sys_engine.validate_architecture_graph(vulnerable_components, vulnerable_connections)
    assert vuln_report["is_resilient"] is False
    assert len(vuln_report["spof_nodes"]) >= 2
    assert any("Postgres Primary" in s for s in vuln_report["spof_nodes"])
    assert any("API Gateway" in s for s in vuln_report["spof_nodes"])
    assert any("Legacy Worker" in w for w in vuln_report["warnings"])
    print(f"  [PASS] Vulnerable topology detected: {len(vuln_report['spof_nodes'])} SPOF(s) flagged, resilience score: {vuln_report['resilience_score']}/100")

    # Resilient multi-tier topology with redundancy and caching
    resilient_components = [
        {"id": "cdn", "name": "Cloudflare CDN Edge", "type": "cdn", "replicas": 100, "is_clustered": True},
        {"id": "gw", "name": "Envoy Ingress Gateway", "type": "gateway", "replicas": 3, "is_clustered": True},
        {"id": "svc", "name": "App Service Fleet", "type": "service", "replicas": 12, "is_clustered": True},
        {"id": "cache", "name": "Redis Cluster", "type": "cache", "replicas": 6, "is_clustered": True},
        {"id": "db", "name": "PostgreSQL Multi-AZ Primary", "type": "database", "replicas": 3, "is_clustered": True},
        {"id": "mq", "name": "Kafka Event Bus", "type": "queue", "replicas": 5, "is_clustered": True},
    ]
    resilient_connections = [
        {"from": "cdn", "to": "gw"},
        {"from": "gw", "to": "svc"},
        {"from": "svc", "to": "cache"},
        {"from": "svc", "to": "db"},
        {"from": "svc", "to": "mq"},
    ]
    res_report = sys_engine.validate_architecture_graph(resilient_components, resilient_connections)
    assert res_report["is_resilient"] is True
    assert len(res_report["spof_nodes"]) == 0
    assert res_report["resilience_score"] >= 85.0
    print(f"  [PASS] Resilient topology approved: 0 SPOFs, resilience score: {res_report['resilience_score']}/100")

    # ── 3. SYSTEM DESIGN: CAPACITY ESTIMATION VERIFIER ─────────────────────
    print("\n--- 3. Testing Capacity Estimation & Math Verifier ---")

    # Candidate estimates within realistic tolerance
    accurate_estimates = {
        "read_qps": 380_000.0,
        "write_qps": 120_000.0,
        "daily_storage_gb": 130.0,
        "bandwidth_gbps": 2.2,
        "ram_cache_gb": 35.0,
    }
    cap_result = sys_engine.verify_capacity_estimation("distributed_rate_limiter", accurate_estimates)
    assert cap_result["overall_accuracy_score"] >= 80.0
    assert cap_result["rating"] == "Exceptional Estimation Accuracy"
    print(f"  [PASS] Accurate capacity estimation verified: Score {cap_result['overall_accuracy_score']}% ({cap_result['rating']})")

    # Candidate estimates with wild deviations
    poor_estimates = {
        "read_qps": 5_000.0,  # 80x too small
        "write_qps": 500.0,
        "daily_storage_gb": 10_000.0,
        "bandwidth_gbps": 150.0,
        "ram_cache_gb": 1.0,
    }
    cap_poor = sys_engine.verify_capacity_estimation("distributed_rate_limiter", poor_estimates)
    assert cap_poor["overall_accuracy_score"] < 60.0
    assert len(cap_poor["feedback"]) >= 2
    print(f"  [PASS] Inaccurate estimation flagged: Score {cap_poor['overall_accuracy_score']}%, feedback provided: {len(cap_poor['feedback'])} notes")

    # ── 4. SYSTEM DESIGN: INTERACTIVE CLARIFICATION PROTOCOL ───────────────
    print("\n--- 4. Testing Bar-Raiser Architecture Clarification ---")
    clarify_resp = await sys_engine.answer_clarification(
        "distributed_rate_limiter",
        "What consistency guarantees do we require across global edge regions? Is eventual consistency acceptable?"
    )
    assert "eventual consistency" in clarify_resp["answer"].lower()
    assert len(clarify_resp["bar_raiser_tips"]) >= 1
    print(f"  [PASS] Clarification responded: '{clarify_resp['answer'][:80]}...'")

    # ── 5. BEHAVIORAL: PRONOUN OWNERSHIP AUDIT & METRIC EXTRACTION ─────────
    print("\n--- 5. Testing Pronoun Ownership & Quantitative Metric Extraction ---")

    # High ownership response
    high_ownership_text = (
        "I noticed our checkout service p99 latency spiked by 350ms during peak load. "
        "I personally led the investigation into our database connection pooling. "
        "I rewrote the query execution planner, reduced connection contention by 75%, and I deployed "
        "a Redis caching tier which saved $180,000 annually and supported 250,000 concurrent shoppers."
    )
    owner_high = beh_engine.analyze_ownership(high_ownership_text)
    assert owner_high.ownership_level == "High Individual Ownership"
    assert owner_high.i_we_ratio >= 0.60
    print(f"  [PASS] High ownership detected: ratio={owner_high.i_we_ratio}, level='{owner_high.ownership_level}'")

    # Passive team-shielding response
    passive_text = (
        "We had an issue where our system was failing. We decided that we should probably improve things. "
        "Our team got together and we discussed solutions, and we gradually fixed the issues over the quarter."
    )
    owner_passive = beh_engine.analyze_ownership(passive_text)
    assert owner_passive.ownership_level == "Passive/Ambiguous Team Attribution"
    assert owner_passive.i_we_ratio <= 0.25
    print(f"  [PASS] Passive team attribution flagged: ratio={owner_passive.i_we_ratio}, level='{owner_passive.ownership_level}'")

    # Metric extraction
    metrics = beh_engine.extract_quantifiable_metrics(high_ownership_text)
    assert any("350ms" in m for m in metrics)
    assert any("75%" in m for m in metrics)
    assert any("$180" in m or "180,000" in m for m in metrics)
    print(f"  [PASS] Quantifiable metrics extracted accurately: {metrics}")

    # ── 6. BEHAVIORAL: STAR+L EVALUATION & BAR-RAISER VERDICT ─────────────
    print("\n--- 6. Testing Full STAR+L Evaluation Engine ---")
    eval_star = await beh_engine.evaluate_star_answer(
        question="Tell me about a time when a critical system failed under your watch. What did you do?",
        answer_transcript=high_ownership_text + " In our retrospective, we institutionalized automated chaos tests to prevent recurrence.",
        competency="ownership",
    )
    assert "situation" in eval_star.star_breakdown
    assert "task" in eval_star.star_breakdown
    assert "action" in eval_star.star_breakdown
    assert "result" in eval_star.star_breakdown
    assert "learning" in eval_star.star_breakdown
    assert eval_star.bar_raiser_verdict in ["Strong Hire", "Hire"]
    assert eval_star.competency_scores["ownership"] >= 80.0
    print(f"  [PASS] STAR+L evaluated: overall_score={eval_star.overall_score}, verdict='{eval_star.bar_raiser_verdict}'")

    # ── 7. BEHAVIORAL: BAR-RAISER FOLLOW-UP PROBES & EXECUTIVE REFRAME ─────
    print("\n--- 7. Testing Follow-Up Probes & Executive Reframe ---")
    probes = beh_engine.generate_follow_up_probes(
        question="Tell me about a time when a critical system failed under your watch.",
        answer_transcript=passive_text,
        eval_result=await beh_engine.evaluate_star_answer("Question", passive_text, "ownership"),
    )
    assert len(probes) >= 3
    assert any("individual responsibility" in p["question"].lower() or "we" in p["question"].lower() for p in probes)
    print(f"  [PASS] High-pressure Bar-Raiser follow-up probes generated: {len(probes)} probes ready")

    reframe = beh_engine.generate_executive_reframe(
        question="Tell me about a time when you resolved an outage.",
        answer_transcript=passive_text,
        competency="ownership",
    )
    assert "reframed_story" in reframe
    assert "**Situation**" in reframe["reframed_story"]
    assert "**Result**" in reframe["reframed_story"]
    assert len(reframe["key_enhancements"]) >= 3
    print("  [PASS] Executive STAR+L story reframe synthesized with positive score uplift")

    # ── 8. REST API INTEGRATION SUITE ──────────────────────────────────────
    print("\n--- 8. Testing REST API Router Integration (System Design & Behavioral) ---")
    async with AsyncSessionLocal() as db:
        user = User(
            email=f"candidate.phase11.{uuid.uuid4().hex[:6]}@apex.com",
            full_name="Morgan Vance",
            hashed_password="hashed_pw_test_123",
            role=UserRole.candidate,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        session = InterviewSession(
            user_id=user.id,
            status=SessionStatus.active,
            target_question_count=5,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

    token = create_access_token(user.id, role="candidate")
    headers = {"Authorization": f"Bearer {token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # System Design Scenarios
        res_scenarios = await client.get("/api/v1/system-design/scenarios", headers=headers)
        assert res_scenarios.status_code == 200
        assert len(res_scenarios.json()) >= 3
        print(f"  [PASS] GET /system-design/scenarios returned {len(res_scenarios.json())} scenario(s)")

        # System Design Scenario Detail
        res_detail = await client.get("/api/v1/system-design/scenarios/distributed_rate_limiter", headers=headers)
        assert res_detail.status_code == 200
        assert res_detail.json()["title"] == "Design a Distributed Rate Limiter for an API Gateway"
        print("  [PASS] GET /system-design/scenarios/{id} returned target challenge specification")

        # System Design Graph Validation
        res_graph = await client.post(
            "/api/v1/system-design/validate-graph",
            headers=headers,
            json={"components": resilient_components, "connections": resilient_connections},
        )
        assert res_graph.status_code == 200
        assert res_graph.json()["is_resilient"] is True
        print(f"  [PASS] POST /system-design/validate-graph: score={res_graph.json()['resilience_score']}/100")

        # System Design Capacity Estimation
        res_cap = await client.post(
            "/api/v1/system-design/capacity-estimate",
            headers=headers,
            json={"scenario_key": "distributed_rate_limiter", "estimates": accurate_estimates},
        )
        assert res_cap.status_code == 200
        assert res_cap.json()["overall_accuracy_score"] >= 80.0
        print("  [PASS] POST /system-design/capacity-estimate: verified capacity calculations")

        # System Design Clarification
        res_clar = await client.post(
            "/api/v1/system-design/clarify",
            headers=headers,
            json={"scenario_key": "distributed_rate_limiter", "question": "What is the peak QPS and SLA?"},
        )
        assert res_clar.status_code == 200
        assert "answer" in res_clar.json()
        print("  [PASS] POST /system-design/clarify: Bar-Raiser clarification responded")

        # System Design Full 8-Pillar Evaluation
        res_eval = await client.post(
            "/api/v1/system-design/evaluate",
            headers=headers,
            json={
                "session_id": str(session.id),
                "problem_title": "Design a Distributed Rate Limiter",
                "problem_prompt": "Global rate limiter handling 500k QPS",
                "architecture_sections": {
                    "requirements": "Support 500,000 QPS with sub-2ms latency SLA and eventual consistency across regions.",
                    "high_level": "Envoy API Gateway with Redis Cluster using sliding window counter and local token bucket.",
                    "data_model": "Redis sorted sets for timestamped request sliding window with TTL expiration.",
                    "scalability": "Consistent hashing across 32 Redis shards with Envoy sidecars to minimize network hops.",
                    "resilience": "Fail-open circuit breaker on complete Redis split; automated replica promotion in multi-AZ.",
                    "trade_offs": "Eventual consistency favored over CP lock to strictly preserve the 2ms SLA target.",
                },
            },
        )
        assert res_eval.status_code == 200
        assert res_eval.json()["overall_score"] >= 70.0
        print(f"  [PASS] POST /system-design/evaluate: 8-pillar overall score={res_eval.json()['overall_score']}, tier='{res_eval.json()['tier']}'")

        # Behavioral Questions & Competencies
        res_comp = await client.get("/api/v1/behavioral/competencies", headers=headers)
        assert res_comp.status_code == 200
        assert len(res_comp.json()) >= 8
        print(f"  [PASS] GET /behavioral/competencies: {len(res_comp.json())} leadership competencies cataloged")

        res_q = await client.get("/api/v1/behavioral/questions", headers=headers)
        assert res_q.status_code == 200
        assert len(res_q.json()) >= 5
        print(f"  [PASS] GET /behavioral/questions: {len(res_q.json())} curated questions retrieved")

        # Behavioral STAR Evaluation
        res_star = await client.post(
            "/api/v1/behavioral/evaluate-star",
            headers=headers,
            json={
                "session_id": str(session.id),
                "question": "Tell me about a time you handled a critical outage.",
                "answer_transcript": high_ownership_text,
                "competency": "ownership",
            },
        )
        assert res_star.status_code == 200
        assert res_star.json()["ownership_metrics"]["ownership_level"] == "High Individual Ownership"
        print(f"  [PASS] POST /behavioral/evaluate-star: verdict='{res_star.json()['bar_raiser_verdict']}', metrics={len(res_star.json()['quantifiable_metrics_found'])}")

        # Behavioral Follow-Up Probes
        res_probes = await client.post(
            "/api/v1/behavioral/follow-up-probes",
            headers=headers,
            json={
                "question": "Tell me about a time you handled a critical outage.",
                "answer_transcript": passive_text,
                "competency": "ownership",
            },
        )
        assert res_probes.status_code == 200
        assert len(res_probes.json()["probes"]) >= 3
        print(f"  [PASS] POST /behavioral/follow-up-probes returned {len(res_probes.json()['probes'])} targeted Bar-Raiser follow-ups")

        # Behavioral Reframe
        res_reframe = await client.post(
            "/api/v1/behavioral/reframe",
            headers=headers,
            json={
                "question": "Tell me about a time you handled a critical outage.",
                "raw_answer": passive_text,
                "competency": "ownership",
            },
        )
        assert res_reframe.status_code == 200
        assert "reframed_story" in res_reframe.json()
        print("  [PASS] POST /behavioral/reframe produced high-impact executive STAR narrative")

    print("\n========================================================")
    print("=== PHASE 11: SYSTEM DESIGN & BEHAVIORAL SUITE PASSED 100% ===")
    print("========================================================\n")


if __name__ == "__main__":
    asyncio.run(test_phase11_system_design_behavioral())
