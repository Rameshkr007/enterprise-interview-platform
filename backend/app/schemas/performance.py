from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CachePurgeRequest(BaseModel):
    namespace: str | None = Field(default=None, description="Optional namespace (e.g., 'skills', 'ats', 'llm_semantic')")
    purge_all: bool = Field(default=False, description="Purge all L1 and L2 caches")


class CachePurgeResponse(BaseModel):
    cleared_keys_count: int
    namespace: str | None
    message: str


class CacheStatsResponse(BaseModel):
    l1: dict[str, Any]
    l2: dict[str, Any]
    overall: dict[str, Any]
    semantic_llm_cache: dict[str, Any]
    namespaces: list[dict[str, Any]]


class SlowQueryItem(BaseModel):
    statement: str
    fingerprint: str
    duration_ms: float
    is_slow: bool
    is_n_plus_one: bool
    timestamp: float


class SlowQueriesResponse(BaseModel):
    total_queries_executed: int
    total_duration_ms: float
    average_duration_ms: float
    slow_query_count: int
    n_plus_one_alerts_count: int
    slow_threshold_ms: float
    top_slow_queries: list[dict[str, Any]]
    top_fingerprints: list[dict[str, Any]]
    n_plus_one_warnings: list[dict[str, Any]]


class RouteMetricItem(BaseModel):
    route: str
    request_count: int
    error_count: int
    error_rate_pct: float
    p50_ms: float
    p90_ms: float
    p95_ms: float
    p99_ms: float
    avg_ms: float
    min_ms: float
    max_ms: float


class EndpointMetricsResponse(BaseModel):
    total_endpoints_tracked: int
    metrics: list[RouteMetricItem]


class BenchmarkRunRequest(BaseModel):
    iterations: int = Field(default=50, ge=10, le=500, description="Iterations for synthetic benchmark")
    workload: str = Field(default="cache_read", description="Benchmark workload: 'cache_read', 'db_query', 'semantic_hash'")


class BenchmarkRunResponse(BaseModel):
    workload: str
    iterations: int
    cold_latency_avg_ms: float
    warm_latency_avg_ms: float
    speedup_multiplier: float
    operations_per_second: float
    cold_p99_ms: float
    warm_p99_ms: float
    message: str
