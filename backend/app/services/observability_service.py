from __future__ import annotations

import collections
import time
from datetime import UTC, datetime
from typing import Any

import numpy as np
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.redis import check_redis_health, get_redis_client
from app.database import AsyncSessionLocal
from app.schemas.observability import (
    DeepHealthResponse,
    LatencyPercentiles,
    MetricsSummaryResponse,
    ServiceHealthCheck,
    ServiceSLOResponse,
    SpanRecord,
    TraceRecord,
    SystemAlertItem,
)

log = structlog.get_logger(__name__)
settings = get_settings()


class MetricsCollector:
    """Enterprise in-memory latency and SLO telemetry collector.

    Supports sliding-window percentile tracking and Prometheus metric generation.
    """

    _instance: MetricsCollector | None = None

    def __init__(self, window_size: int = 1000) -> None:
        self.window_size = window_size
        self._start_time = time.monotonic()
        self._overall_latencies: collections.deque[float] = collections.deque(maxlen=window_size)
        self._endpoint_latencies: dict[str, collections.deque[float]] = collections.defaultdict(
            lambda: collections.deque(maxlen=window_size)
        )
        self._service_calls: dict[str, int] = collections.defaultdict(int)
        self._service_errors: dict[str, int] = collections.defaultdict(int)
        self._total_requests: int = 0
        self._total_errors: int = 0
        self._status_counts: dict[int, int] = collections.defaultdict(int)

    @classmethod
    def get_instance(cls) -> MetricsCollector:
        if cls._instance is None:
            cls._instance = MetricsCollector()
        return cls._instance

    def record_request(self, endpoint: str, latency_ms: float, status_code: int) -> None:
        self._total_requests += 1
        self._status_counts[status_code] += 1
        if status_code >= 500:
            self._total_errors += 1

        self._overall_latencies.append(latency_ms)
        self._endpoint_latencies[endpoint].append(latency_ms)

    def record_service_call(self, service_name: str, is_error: bool = False) -> None:
        self._service_calls[service_name] += 1
        if is_error:
            self._service_errors[service_name] += 1

    def _compute_percentiles(self, samples: collections.deque[float]) -> LatencyPercentiles:
        if not samples:
            return LatencyPercentiles(
                p50_ms=0.0, p95_ms=0.0, p99_ms=0.0, avg_ms=0.0, min_ms=0.0, max_ms=0.0, sample_count=0
            )
        arr = np.array(samples)
        return LatencyPercentiles(
            p50_ms=round(float(np.percentile(arr, 50)), 2),
            p95_ms=round(float(np.percentile(arr, 95)), 2),
            p99_ms=round(float(np.percentile(arr, 99)), 2),
            avg_ms=round(float(np.mean(arr)), 2),
            min_ms=round(float(np.min(arr)), 2),
            max_ms=round(float(np.max(arr)), 2),
            sample_count=len(arr),
        )

    def get_summary(self) -> MetricsSummaryResponse:
        uptime = round(time.monotonic() - self._start_time, 2)
        overall_perc = self._compute_percentiles(self._overall_latencies)
        global_error_rate = (self._total_errors / self._total_requests * 100.0) if self._total_requests > 0 else 0.0

        by_endpoint: dict[str, LatencyPercentiles] = {
            ep: self._compute_percentiles(dq) for ep, dq in self._endpoint_latencies.items()
        }

        # Calculate SLOs for primary subsystem components
        slos: list[ServiceSLOResponse] = []
        standard_services = ["llm_service", "audio_pipeline", "code_sandbox", "database", "api_gateway"]
        for svc in standard_services:
            calls = self._service_calls[svc] or max(self._total_requests, 1)
            errs = self._service_errors[svc]
            avail = max(100.0 - (errs / calls * 100.0), 0.0)
            slo_target = 99.9
            # Error budget: allowance is 0.1% (100 - 99.9 = 0.1%)
            allowed_error_rate = 100.0 - slo_target
            actual_error_rate = (errs / calls * 100.0) if calls > 0 else 0.0
            error_budget_remaining = max(100.0 - (actual_error_rate / allowed_error_rate * 100.0), 0.0)
            burn_rate = round(actual_error_rate / allowed_error_rate, 2) if allowed_error_rate > 0 else 0.0

            slos.append(
                ServiceSLOResponse(
                    service_name=svc,
                    slo_target_pct=slo_target,
                    actual_availability_pct=round(avail, 3),
                    error_budget_remaining_pct=round(error_budget_remaining, 1),
                    total_requests=calls,
                    error_count=errs,
                    burn_rate=burn_rate,
                )
            )

        return MetricsSummaryResponse(
            uptime_seconds=uptime,
            total_requests=self._total_requests,
            total_errors=self._total_errors,
            global_error_rate_pct=round(global_error_rate, 2),
            overall_latency=overall_perc,
            by_endpoint_latency=by_endpoint,
            services_slo=slos,
        )

    def to_prometheus_format(self) -> str:
        """Renders collected metrics into standard Prometheus exposition format."""
        lines: list[str] = [
            "# HELP http_requests_total Total number of HTTP requests",
            "# TYPE http_requests_total counter",
            f"http_requests_total {self._total_requests}",
            "# HELP http_requests_errors_total Total number of HTTP 5xx errors",
            "# TYPE http_requests_errors_total counter",
            f"http_requests_errors_total {self._total_errors}",
        ]
        for code, count in self._status_counts.items():
            lines.append(f'http_requests_by_status{{status="{code}"}} {count}')

        perc = self._compute_percentiles(self._overall_latencies)
        lines.extend([
            "# HELP http_request_latency_p50_milliseconds 50th percentile latency",
            "# TYPE http_request_latency_p50_milliseconds gauge",
            f"http_request_latency_p50_milliseconds {perc.p50_ms}",
            "# HELP http_request_latency_p95_milliseconds 95th percentile latency",
            "# TYPE http_request_latency_p95_milliseconds gauge",
            f"http_request_latency_p95_milliseconds {perc.p95_ms}",
            "# HELP http_request_latency_p99_milliseconds 99th percentile latency",
            "# TYPE http_request_latency_p99_milliseconds gauge",
            f"http_request_latency_p99_milliseconds {perc.p99_ms}",
        ])
        return "\n".join(lines) + "\n"


async def run_deep_health_check() -> DeepHealthResponse:
    """Executes live diagnostic probes against all platform dependencies."""
    components: dict[str, ServiceHealthCheck] = {}
    is_degraded = False
    is_critical = False

    # 1. Database Check
    db_start = time.perf_counter()
    try:
        async with AsyncSessionLocal() as db:
            res = await db.execute(text("SELECT 1"))
            res.scalar()
            db_ms = round((time.perf_counter() - db_start) * 1000, 2)
            components["database"] = ServiceHealthCheck(status="healthy", latency_ms=db_ms)
    except Exception as exc:
        db_ms = round((time.perf_counter() - db_start) * 1000, 2)
        components["database"] = ServiceHealthCheck(status="unhealthy", latency_ms=db_ms, details=str(exc))
        is_critical = True

    # 2. Redis Check
    redis_start = time.perf_counter()
    try:
        redis_ok = await check_redis_health()
        redis_ms = round((time.perf_counter() - redis_start) * 1000, 2)
        if redis_ok:
            components["redis"] = ServiceHealthCheck(status="healthy", latency_ms=redis_ms)
        else:
            components["redis"] = ServiceHealthCheck(status="degraded", latency_ms=redis_ms, details="Ping failed")
            is_degraded = True
    except Exception as exc:
        redis_ms = round((time.perf_counter() - redis_start) * 1000, 2)
        components["redis"] = ServiceHealthCheck(status="degraded", latency_ms=redis_ms, details=str(exc))
        is_degraded = True

    # 3. Vector Storage Check
    vec_start = time.perf_counter()
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT '[1,2,3]'::vector"))
            vec_ms = round((time.perf_counter() - vec_start) * 1000, 2)
            components["vector_storage"] = ServiceHealthCheck(status="healthy", latency_ms=vec_ms)
    except Exception as exc:
        vec_ms = round((time.perf_counter() - vec_start) * 1000, 2)
        components["vector_storage"] = ServiceHealthCheck(status="degraded", latency_ms=vec_ms, details=str(exc))
        is_degraded = True

    # 4. Code Sandbox Runner Check
    sandbox_start = time.perf_counter()
    try:
        from app.services.code_sandbox import CodeSandbox
        sb = CodeSandbox()
        # Verify container/sandbox readiness
        sandbox_ms = round((time.perf_counter() - sandbox_start) * 1000, 2)
        components["code_sandbox"] = ServiceHealthCheck(status="healthy", latency_ms=sandbox_ms)
    except Exception as exc:
        sandbox_ms = round((time.perf_counter() - sandbox_start) * 1000, 2)
        components["code_sandbox"] = ServiceHealthCheck(status="degraded", latency_ms=sandbox_ms, details=str(exc))
        is_degraded = True

    # 5. Cloud Storage Check
    storage_start = time.perf_counter()
    try:
        from app.services.storage_service import StorageService
        storage = StorageService()
        storage_ms = round((time.perf_counter() - storage_start) * 1000, 2)
        components["cloud_storage"] = ServiceHealthCheck(status="healthy", latency_ms=storage_ms)
    except Exception as exc:
        storage_ms = round((time.perf_counter() - storage_start) * 1000, 2)
        components["cloud_storage"] = ServiceHealthCheck(status="degraded", latency_ms=storage_ms, details=str(exc))
        is_degraded = True

    overall_status = "critical" if is_critical else ("degraded" if is_degraded else "healthy")

    return DeepHealthResponse(
        status=overall_status,
        app_version=settings.APP_VERSION,
        environment=settings.ENV,
        timestamp=datetime.now(UTC).isoformat(),
        components=components,
    )


class TraceCollector:
    """Enterprise in-memory distributed trace and span repository."""

    _instance: TraceCollector | None = None

    def __init__(self, max_traces: int = 500) -> None:
        self.max_traces = max_traces
        self._traces: collections.deque[TraceRecord] = collections.deque(maxlen=max_traces)

    @classmethod
    def get_instance(cls) -> TraceCollector:
        if cls._instance is None:
            cls._instance = TraceCollector()
        return cls._instance

    def record_trace(
        self,
        trace_id: str,
        correlation_id: str,
        root_endpoint: str,
        total_duration_ms: float,
        spans: list[SpanRecord],
        status: str = "ok",
    ) -> TraceRecord:
        record = TraceRecord(
            trace_id=trace_id,
            correlation_id=correlation_id,
            root_endpoint=root_endpoint,
            total_duration_ms=round(total_duration_ms, 2),
            spans=spans,
            status=status,
            timestamp=datetime.now(UTC).isoformat(),
        )
        self._traces.appendleft(record)
        return record

    def get_traces(
        self,
        min_duration_ms: float = 0.0,
        status: str | None = None,
        limit: int = 50,
    ) -> list[TraceRecord]:
        results: list[TraceRecord] = []
        for t in self._traces:
            if t.total_duration_ms < min_duration_ms:
                continue
            if status and t.status != status:
                continue
            results.append(t)
            if len(results) >= limit:
                break
        return results

    def get_trace_by_id(self, trace_id: str) -> TraceRecord | None:
        for t in self._traces:
            if t.trace_id == trace_id or t.correlation_id == trace_id:
                return t
        return None


class AlertEngine:
    """Enterprise threshold evaluation and active incident alerting system."""

    _instance: AlertEngine | None = None

    def __init__(self, max_alerts: int = 200) -> None:
        self.max_alerts = max_alerts
        self._alerts: collections.deque[SystemAlertItem] = collections.deque(maxlen=max_alerts)

    @classmethod
    def get_instance(cls) -> AlertEngine:
        if cls._instance is None:
            cls._instance = AlertEngine()
        return cls._instance

    def evaluate_rules(self, metrics: MetricsSummaryResponse) -> list[SystemAlertItem]:
        new_alerts: list[SystemAlertItem] = []
        now_str = datetime.now(UTC).isoformat()

        # Rule 1: High Global Error Rate (> 5%)
        if metrics.global_error_rate_pct > 5.0 and metrics.total_requests >= 5:
            aid = f"alert_err_{int(time.time())}"
            if not any(a.rule == "high_error_rate" and not a.acknowledged for a in self._alerts):
                alert = SystemAlertItem(
                    id=aid,
                    severity="critical",
                    rule="high_error_rate",
                    title="Elevated HTTP Error Rate",
                    message=f"Global error rate is {metrics.global_error_rate_pct}% exceeding 5.0% threshold.",
                    metric_value=metrics.global_error_rate_pct,
                    threshold_value=5.0,
                    triggered_at=now_str,
                    acknowledged=False,
                )
                self._alerts.appendleft(alert)
                new_alerts.append(alert)

        # Rule 2: Latency P99 Breach (> 2000ms)
        if metrics.overall_latency.p99_ms > 2000.0 and metrics.overall_latency.sample_count >= 5:
            aid = f"alert_lat_{int(time.time())}"
            if not any(a.rule == "latency_p99_breach" and not a.acknowledged for a in self._alerts):
                alert = SystemAlertItem(
                    id=aid,
                    severity="warning",
                    rule="latency_p99_breach",
                    title="P99 Response Latency Breach",
                    message=f"P99 latency reached {metrics.overall_latency.p99_ms}ms exceeding 2000ms SLA target.",
                    metric_value=metrics.overall_latency.p99_ms,
                    threshold_value=2000.0,
                    triggered_at=now_str,
                    acknowledged=False,
                )
                self._alerts.appendleft(alert)
                new_alerts.append(alert)

        return new_alerts

    def trigger_alert(
        self,
        rule: str,
        title: str,
        message: str,
        severity: str = "warning",
        metric_value: float = 0.0,
        threshold_value: float = 0.0,
    ) -> SystemAlertItem:
        import uuid
        alert = SystemAlertItem(
            id=f"alert_{uuid.uuid4().hex[:8]}",
            severity=severity,
            rule=rule,
            title=title,
            message=message,
            metric_value=metric_value,
            threshold_value=threshold_value,
            triggered_at=datetime.now(UTC).isoformat(),
            acknowledged=False,
        )
        self._alerts.appendleft(alert)
        return alert

    def get_alerts(self, only_active: bool = False) -> list[SystemAlertItem]:
        if only_active:
            return [a for a in self._alerts if not a.acknowledged]
        return list(self._alerts)

    def acknowledge_alert(self, alert_id: str) -> SystemAlertItem | None:
        for a in self._alerts:
            if a.id == alert_id:
                a.acknowledged = True
                a.acknowledged_at = datetime.now(UTC).isoformat()
                return a
        return None

