import asyncio
import os
import sys
import time
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
import structlog
from httpx import ASGITransport
from sqlalchemy import text

# Force UTF-8 on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.database import AsyncSessionLocal, engine
from app.main import app
from app.middleware.server_timing import RouteMetricsStore
from app.services.cache_service import L1MemoryCache, TieredCacheManager
from app.services.query_profiler import QueryProfiler

log = structlog.get_logger(__name__)


async def test_phase19_performance_caching_complete():
    print("\n" + "=" * 80)
    print("=== RUNNING PHASE 19: PERFORMANCE PROFILING & CACHING TEST SUITE ===")
    print("=" * 80)

    # ── 1. Test L1 In-Memory LRU Cache ─────────────────────────────────────────
    print("\n--- Step 1: L1 In-Memory LRU Cache Mechanics ---")
    l1 = L1MemoryCache(max_items=5, default_ttl=2)

    # Set and get
    await l1.set("key_1", {"name": "Alice"}, ttl=5)
    val1 = await l1.get("key_1")
    assert val1 is not None and val1["name"] == "Alice"
    print("  [PASS] L1 Cache set and instant get verified.")

    # Cache miss
    miss = await l1.get("non_existent_key")
    assert miss is None
    print("  [PASS] L1 Cache miss returns None.")

    # Max items eviction (capacity: 5)
    for i in range(2, 8):
        await l1.set(f"key_{i}", f"val_{i}", ttl=10)
    # Since capacity is 5 and we added 2..7 (6 items), earliest items should be evicted
    assert l1.stats["size"] <= 5
    print(f"  [PASS] L1 LRU capacity constraint enforced: size={l1.stats['size']}/5.")

    # TTL Expiration test
    await l1.set("expiring_key", "temp_data", ttl=1)
    await asyncio.sleep(1.2)
    expired_val = await l1.get("expiring_key")
    assert expired_val is None
    print("  [PASS] L1 TTL expiration verified (item evicted after 1.2s).")

    # Clear prefix
    await l1.set("taxonomy:node1", "data1", ttl=10)
    await l1.set("taxonomy:node2", "data2", ttl=10)
    await l1.set("other:node3", "data3", ttl=10)
    cleared = await l1.clear_prefix("taxonomy:")
    assert cleared == 2
    assert await l1.get("taxonomy:node1") is None
    assert await l1.get("other:node3") is not None
    print(f"  [PASS] L1 clear_prefix('taxonomy:') removed {cleared} keys.")


    # ── 2. Test L2 Redis Distributed Cache ────────────────────────────────────
    print("\n--- Step 2: L2 Distributed Redis Cache & Namespaces ---")
    cache = TieredCacheManager.get_instance()

    test_ns = f"test_phase19_{uuid4().hex[:6]}"
    await cache.set(test_ns, "user_profile_1", {"role": "Staff Architect", "score": 94.5}, ttl=120)

    val, status = await cache.get(test_ns, "user_profile_1")
    assert val is not None
    assert val["role"] == "Staff Architect"
    assert status in ("HIT-L1", "HIT-L2")
    print(f"  [PASS] L2 Distributed Cache set and get verified (status={status}).")

    # Namespace invalidation
    await cache.set(test_ns, "user_profile_2", {"role": "Senior Engineer"}, ttl=120)
    inv_count = await cache.invalidate_namespace(test_ns)
    assert inv_count >= 1
    val_after, status_after = await cache.get(test_ns, "user_profile_1")
    assert val_after is None
    assert status_after == "MISS"
    print(f"  [PASS] L2 Namespace '{test_ns}' invalidated ({inv_count} keys purged).")


    # ── 3. Test Tiered Hierarchical get_or_compute ─────────────────────────────
    print("\n--- Step 3: Tiered Hierarchical get_or_compute Lifecycle ---")
    tier_ns = f"skills_hierarchy_{uuid4().hex[:6]}"
    compute_count = 0

    async def compute_heavy_skill_dag() -> dict:
        nonlocal compute_count
        compute_count += 1
        await asyncio.sleep(0.01)  # Simulate compute
        return {"root_node": "Distributed Systems", "tiers": [1, 2, 3, 4, 5], "count": 26}

    # Pass 1: Cold fetch -> MISS
    data1, status1 = await cache.get_or_compute(tier_ns, "full_dag", compute_heavy_skill_dag, ttl=180, l1_ttl=60)
    assert status1 == "MISS"
    assert compute_count == 1
    assert data1["count"] == 26
    print(f"  [PASS] Pass 1 (Cold): status='{status1}', compute called {compute_count} time(s).")

    # Pass 2: Warm fetch -> HIT-L1 (In-Memory)
    data2, status2 = await cache.get_or_compute(tier_ns, "full_dag", compute_heavy_skill_dag, ttl=180, l1_ttl=60)
    assert status2 == "HIT-L1"
    assert compute_count == 1  # No extra compute
    print(f"  [PASS] Pass 2 (Warm In-Memory): status='{status2}', zero compute overhead.")

    # Pass 3: Evict from L1 only -> Fetch should hit L2 Redis and re-promote to L1
    await cache.l1.delete(f"{tier_ns}:full_dag")
    data3, status3 = await cache.get_or_compute(tier_ns, "full_dag", compute_heavy_skill_dag, ttl=180, l1_ttl=60)
    assert status3 == "HIT-L2"
    assert compute_count == 1  # Still zero compute overhead!
    print(f"  [PASS] Pass 3 (L1 Evicted, L2 Fallback): status='{status3}', successfully promoted back to L1.")

    # Pass 4: Next fetch should be HIT-L1 again
    data4, status4 = await cache.get_or_compute(tier_ns, "full_dag", compute_heavy_skill_dag, ttl=180, l1_ttl=60)
    assert status4 == "HIT-L1"
    assert compute_count == 1
    print(f"  [PASS] Pass 4 (Re-hit promoted L1): status='{status4}'.")


    # ── 4. Test Semantic Vector & LLM Embedding Response Cache ─────────────────
    print("\n--- Step 4: Semantic LLM Prompt & Embedding Deduplication Cache ---")
    sample_prompt = f"Evaluate the candidate's answer for PACELC theorem trade-offs in DynamoDB - {uuid4().hex}."
    prompt_hash = cache.hash_prompt(sample_prompt, model="gpt-4o", temperature=0.2)
    assert len(prompt_hash) == 64

    # Miss check (fresh dynamic prompt must not exist in cache)
    assert await cache.get_semantic_llm(prompt_hash) is None

    # Store semantic LLM evaluation response
    eval_response = {
        "score": 92.0,
        "recommendation": "Strong Hire",
        "critique": "Solid explanation of latency vs consistency trade-offs when partitioned.",
    }
    await cache.set_semantic_llm(prompt_hash, eval_response, estimated_tokens=1200, ttl=86400)

    # Retrieve cached evaluation
    cached_eval = await cache.get_semantic_llm(prompt_hash)
    assert cached_eval is not None
    assert cached_eval["score"] == 92.0
    assert cached_eval["recommendation"] == "Strong Hire"

    stats = await cache.get_stats()
    assert stats["semantic_llm_cache"]["hits"] >= 1
    assert stats["semantic_llm_cache"]["tokens_saved"] >= 1200
    assert stats["semantic_llm_cache"]["cost_saved_usd"] > 0.0
    print(f"  [PASS] Semantic LLM response cached: Saved {stats['semantic_llm_cache']['tokens_saved']} tokens (${stats['semantic_llm_cache']['cost_saved_usd']} USD).")


    # ── 5. Test SQLAlchemy Query Profiler & N+1 Loop Detection ─────────────────
    print("\n--- Step 5: SQLAlchemy Query Profiler & N+1 Loop Detection ---")
    profiler = QueryProfiler.get_instance()
    profiler.reset()

    # Execute real database queries
    async with AsyncSessionLocal() as session:
        # Simple fast query
        res = await session.execute(text("SELECT 1 AS probe"))
        assert res.scalar() == 1

        # Simulate slow query recording
        profiler.record_query("SELECT pg_sleep(0.04), candidate_id FROM resumes WHERE id = 'sample-uuid'", duration_ms=42.5)

        # Trigger N+1 antipattern warning by running identical query pattern 3+ times
        n1_stmt = "SELECT id, title FROM job_descriptions WHERE id = 'abc-123'"
        for _ in range(4):
            profiler.record_query(n1_stmt, duration_ms=2.1)

    summary = profiler.get_summary()
    assert summary["total_queries_executed"] >= 5
    assert summary["slow_query_count"] >= 1
    assert summary["n_plus_one_alerts_count"] >= 1
    assert any(a["fingerprint"] for a in summary["n_plus_one_warnings"])
    print(f"  [PASS] Query Profiler monitored {summary['total_queries_executed']} queries (avg: {summary['average_duration_ms']}ms).")
    print(f"  [PASS] Slow query detected (> {summary['slow_threshold_ms']}ms).")
    print(f"  [PASS] N+1 Query Antipattern detected with actionable recommendation: '{summary['n_plus_one_warnings'][0]['recommendation']}'.")


    # ── 6. Test W3C Server-Timing & Route Latency Metrics ──────────────────────
    print("\n--- Step 6: W3C Server-Timing Middleware & Latency Metrics ---")
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Request health endpoint
        r1 = await client.get("/health")
        assert r1.status_code == 200
        assert "Server-Timing" in r1.headers
        assert "total;dur=" in r1.headers["Server-Timing"]
        assert "X-Response-Time" in r1.headers
        assert "X-Cache" in r1.headers
        print(f"  [PASS] W3C Server-Timing header received: '{r1.headers['Server-Timing']}'.")
        print(f"  [PASS] X-Response-Time header: '{r1.headers['X-Response-Time']}', X-Cache: '{r1.headers['X-Cache']}'.")

        # Request performance cache stats
        r2 = await client.get("/api/v1/performance/cache/stats")
        assert r2.status_code == 200
        data_stats = r2.json()
        assert "l1" in data_stats
        assert "l2" in data_stats
        assert "overall" in data_stats
        print(f"  [PASS] GET /api/v1/performance/cache/stats: Effective hit ratio = {data_stats['overall']['effective_hit_ratio_pct']}%.")


    # ── 7. Test Performance API Endpoints ─────────────────────────────────────
    print("\n--- Step 7: REST API Endpoints & Cache Purge ---")
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Purge namespace
        p_res = await client.post("/api/v1/performance/cache/purge", json={"namespace": "bench_test", "purge_all": False})
        assert p_res.status_code == 200
        assert p_res.json()["namespace"] == "bench_test"
        print("  [PASS] POST /api/v1/performance/cache/purge namespace verified.")

        # 2. Get slow queries
        sq_res = await client.get("/api/v1/performance/queries/slow")
        assert sq_res.status_code == 200
        sq_data = sq_res.json()
        assert "top_slow_queries" in sq_data
        assert "n_plus_one_warnings" in sq_data
        print(f"  [PASS] GET /api/v1/performance/queries/slow: {sq_data['slow_query_count']} slow queries, {sq_data['n_plus_one_alerts_count']} N+1 alerts.")

        # 3. Get endpoint metrics
        em_res = await client.get("/api/v1/performance/endpoints/metrics")
        assert em_res.status_code == 200
        em_data = em_res.json()
        assert em_data["total_endpoints_tracked"] >= 1
        top_endpoint = em_data["metrics"][0]
        print(f"  [PASS] GET /api/v1/performance/endpoints/metrics: Tracked {em_data['total_endpoints_tracked']} routes. Top route '{top_endpoint['route']}' P50={top_endpoint['p50_ms']}ms, P99={top_endpoint['p99_ms']}ms.")


    # ── 8. Test Synthetic Load & Stress Benchmark Runner ──────────────────────
    print("\n--- Step 8: Synthetic Load & Stress Benchmark Runner ---")
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        bench_res = await client.post(
            "/api/v1/performance/benchmark/run",
            json={"iterations": 50, "workload": "cache_read"},
        )
        assert bench_res.status_code == 200
        bench_data = bench_res.json()
        assert bench_data["iterations"] == 50
        assert bench_data["cold_latency_avg_ms"] > bench_data["warm_latency_avg_ms"]
        assert bench_data["speedup_multiplier"] >= 2.0
        assert bench_data["operations_per_second"] > 100.0
        print(f"  [PASS] Synthetic benchmark completed: Cold={bench_data['cold_latency_avg_ms']}ms, Warm={bench_data['warm_latency_avg_ms']}ms.")
        print(f"  [PASS] Speedup Multiplier: {bench_data['speedup_multiplier']}x, Operations/sec: {bench_data['operations_per_second']}.")

    print("\n" + "=" * 80)
    print("=== ALL PHASE 19 PERFORMANCE PROFILING & CACHING TESTS PASSED (100%) ===")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_phase19_performance_caching_complete())
