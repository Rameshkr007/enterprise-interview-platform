from __future__ import annotations

import asyncio
import time
from typing import Annotated, Any

import numpy as np
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.server_timing import RouteMetricsStore
from app.schemas.performance import (
    BenchmarkRunRequest,
    BenchmarkRunResponse,
    CachePurgeRequest,
    CachePurgeResponse,
    CacheStatsResponse,
    EndpointMetricsResponse,
    RouteMetricItem,
    SlowQueriesResponse,
)
from app.services.cache_service import TieredCacheManager
from app.services.query_profiler import QueryProfiler

router = APIRouter(prefix="/performance", tags=["Performance & Caching"])


@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats() -> dict[str, Any]:
    """Retrieves real-time hierarchical L1/L2 cache statistics, hit ratios, and semantic token savings."""
    cache = TieredCacheManager.get_instance()
    return await cache.get_stats()


@router.post("/cache/purge", response_model=CachePurgeResponse)
async def purge_cache(body: CachePurgeRequest) -> CachePurgeResponse:
    """Invalidates cache by specific namespace or purges all L1/L2 caches."""
    cache = TieredCacheManager.get_instance()
    if body.purge_all:
        count = await cache.purge_all()
        return CachePurgeResponse(
            cleared_keys_count=count,
            namespace="ALL",
            message=f"Purged all application caches ({count} keys removed).",
        )
    elif body.namespace:
        count = await cache.invalidate_namespace(body.namespace)
        return CachePurgeResponse(
            cleared_keys_count=count,
            namespace=body.namespace,
            message=f"Invalidated namespace '{body.namespace}' ({count} keys removed).",
        )
    else:
        return CachePurgeResponse(
            cleared_keys_count=0,
            namespace=None,
            message="No namespace specified and purge_all was false. No keys cleared.",
        )


@router.get("/queries/slow", response_model=SlowQueriesResponse)
async def get_slow_queries() -> dict[str, Any]:
    """Retrieves intercepted slow database queries, N+1 query antipattern alerts, and execution timings."""
    profiler = QueryProfiler.get_instance()
    return profiler.get_summary()


@router.post("/queries/reset")
async def reset_query_profiler() -> dict[str, str]:
    """Resets query profiler buffers and counters."""
    profiler = QueryProfiler.get_instance()
    profiler.reset()
    return {"status": "ok", "message": "Query profiler buffers and counters cleared."}


@router.get("/endpoints/metrics", response_model=EndpointMetricsResponse)
async def get_endpoint_metrics() -> EndpointMetricsResponse:
    """Retrieves per-route response latency percentiles (P50, P90, P95, P99) and request counts."""
    store = RouteMetricsStore.get_instance()
    raw = store.get_metrics()
    metrics = [RouteMetricItem(**m) for m in raw]
    return EndpointMetricsResponse(
        total_endpoints_tracked=len(metrics),
        metrics=metrics,
    )


@router.post("/benchmark/run", response_model=BenchmarkRunResponse)
async def run_synthetic_benchmark(body: BenchmarkRunRequest) -> BenchmarkRunResponse:
    """
    Executes a high-throughput synthetic benchmark comparing Cold uncached execution
    against Warm tiered cache execution over N iterations.
    """
    cache = TieredCacheManager.get_instance()
    iterations = body.iterations
    test_key = f"bench_{int(time.time())}"

    # Cold run: Uncached compute with simulated DB processing latency (5-15ms)
    cold_durations: list[float] = []
    async def simulate_workload() -> dict[str, Any]:
        await asyncio.sleep(0.008)  # 8ms simulated query/workload
        return {"data": "complex_taxonomy_node", "tier": 5, "payload": list(range(100))}

    for i in range(min(iterations, 30)):
        t0 = time.perf_counter()
        # Compute without caching
        _ = await simulate_workload()
        dur = (time.perf_counter() - t0) * 1000.0
        cold_durations.append(dur)

    # Warm run: Pre-populate cache, then run rapid gets
    await cache.set("benchmark", test_key, {"cached": True, "value": list(range(100))}, ttl=300)
    warm_durations: list[float] = []

    t_bench_start = time.perf_counter()
    for i in range(iterations):
        t0 = time.perf_counter()
        val, status = await cache.get("benchmark", test_key)
        dur = (time.perf_counter() - t0) * 1000.0
        warm_durations.append(dur)
    total_bench_time = time.perf_counter() - t_bench_start

    cold_arr = np.array(cold_durations)
    warm_arr = np.array(warm_durations)

    cold_avg = float(np.mean(cold_arr))
    warm_avg = float(np.mean(warm_arr))
    speedup = round(cold_avg / max(warm_avg, 0.001), 1)
    ops_sec = round(iterations / max(total_bench_time, 0.001), 1)

    return BenchmarkRunResponse(
        workload=body.workload,
        iterations=iterations,
        cold_latency_avg_ms=round(cold_avg, 2),
        warm_latency_avg_ms=round(warm_avg, 3),
        speedup_multiplier=speedup,
        operations_per_second=ops_sec,
        cold_p99_ms=round(float(np.percentile(cold_arr, 99)), 2),
        warm_p99_ms=round(float(np.percentile(warm_arr, 99)), 3),
        message=f"Benchmark complete: Warm cache achieved {speedup}x speedup over uncached compute at {ops_sec} ops/sec.",
    )
