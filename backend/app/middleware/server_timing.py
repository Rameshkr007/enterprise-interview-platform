from __future__ import annotations

import collections
import time
from collections.abc import Callable
from typing import Any

import numpy as np
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RouteMetricsStore:
    """Sliding-window collector for per-route response latency percentiles."""

    _instance: RouteMetricsStore | None = None

    def __init__(self) -> None:
        # (method, path_template) -> deque of duration_ms
        self._route_latencies: dict[str, collections.deque[float]] = collections.defaultdict(
            lambda: collections.deque(maxlen=200)
        )
        self._route_counts: dict[str, int] = collections.defaultdict(int)
        self._route_errors: dict[str, int] = collections.defaultdict(int)

    @classmethod
    def get_instance(cls) -> RouteMetricsStore:
        if cls._instance is None:
            cls._instance = RouteMetricsStore()
        return cls._instance

    def record(self, route_key: str, duration_ms: float, is_error: bool = False) -> None:
        self._route_latencies[route_key].append(duration_ms)
        self._route_counts[route_key] += 1
        if is_error:
            self._route_errors[route_key] += 1

    def get_metrics(self) -> list[dict[str, Any]]:
        results = []
        for route_key, latencies in self._route_latencies.items():
            if not latencies:
                continue
            arr = np.array(latencies)
            count = self._route_counts[route_key]
            errors = self._route_errors[route_key]
            err_rate = round((errors / count * 100) if count > 0 else 0.0, 1)

            results.append({
                "route": route_key,
                "request_count": count,
                "error_count": errors,
                "error_rate_pct": err_rate,
                "p50_ms": round(float(np.percentile(arr, 50)), 2),
                "p90_ms": round(float(np.percentile(arr, 90)), 2),
                "p95_ms": round(float(np.percentile(arr, 95)), 2),
                "p99_ms": round(float(np.percentile(arr, 99)), 2),
                "avg_ms": round(float(np.mean(arr)), 2),
                "min_ms": round(float(np.min(arr)), 2),
                "max_ms": round(float(np.max(arr)), 2),
            })
        results.sort(key=lambda x: x["request_count"], reverse=True)
        return results


class ServerTimingMiddleware(BaseHTTPMiddleware):
    """
    W3C Server-Timing middleware.
    Calculates execution duration, exposes Server-Timing header with sub-component spans,
    and updates endpoint percentile histograms.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()

        # Attach sub-timing slots on request state
        request.state.db_duration_ms = 0.0
        request.state.cache_duration_ms = 0.0
        request.state.ai_duration_ms = 0.0
        request.state.cache_hit_status = "BYPASS"

        is_error = False
        try:
            response = await call_next(request)
        except Exception:
            is_error = True
            raise
        finally:
            total_duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

            # Record route metrics
            path = request.url.path
            method = request.method
            route_key = f"{method} {path}"
            RouteMetricsStore.get_instance().record(route_key, total_duration_ms, is_error=is_error)

        # Assemble Server-Timing entries
        timing_parts = [f"total;dur={total_duration_ms}"]

        db_dur = getattr(request.state, "db_duration_ms", 0.0)
        if db_dur > 0:
            timing_parts.append(f'db;dur={round(db_dur, 2)};desc="PostgreSQL"')

        cache_dur = getattr(request.state, "cache_duration_ms", 0.0)
        if cache_dur > 0:
            timing_parts.append(f'cache;dur={round(cache_dur, 2)};desc="Redis/L1"')

        ai_dur = getattr(request.state, "ai_duration_ms", 0.0)
        if ai_dur > 0:
            timing_parts.append(f'ai;dur={round(ai_dur, 2)};desc="LLM Inference"')

        server_timing_header = ", ".join(timing_parts)
        response.headers["Server-Timing"] = server_timing_header
        response.headers["X-Response-Time"] = f"{total_duration_ms}ms"

        cache_status = getattr(request.state, "cache_hit_status", "BYPASS")
        response.headers["X-Cache"] = cache_status

        return response
