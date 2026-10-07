from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class LatencyPercentiles(BaseModel):
    p50_ms: float
    p95_ms: float
    p99_ms: float
    avg_ms: float
    min_ms: float
    max_ms: float
    sample_count: int


class ServiceHealthCheck(BaseModel):
    status: str
    latency_ms: float
    details: str | None = None


class DeepHealthResponse(BaseModel):
    status: str  # "healthy", "degraded", "critical"
    app_version: str
    environment: str
    timestamp: str
    components: dict[str, ServiceHealthCheck]


class ServiceSLOResponse(BaseModel):
    service_name: str
    slo_target_pct: float
    actual_availability_pct: float
    error_budget_remaining_pct: float
    total_requests: int
    error_count: int
    burn_rate: float


class MetricsSummaryResponse(BaseModel):
    uptime_seconds: float
    total_requests: int
    total_errors: int
    global_error_rate_pct: float
    overall_latency: LatencyPercentiles
    by_endpoint_latency: dict[str, LatencyPercentiles]
    services_slo: list[ServiceSLOResponse]


class SpanRecord(BaseModel):
    span_name: str
    service: str
    duration_ms: float
    status: str  # "ok", "error"
    metadata: dict[str, Any] = Field(default_factory=dict)


class TraceRecord(BaseModel):
    trace_id: str
    correlation_id: str
    root_endpoint: str
    total_duration_ms: float
    spans: list[SpanRecord]
    status: str  # "ok", "error"
    timestamp: str


class TraceListResponse(BaseModel):
    total_traces: int
    traces: list[TraceRecord]


class SystemAlertItem(BaseModel):
    id: str
    severity: str  # "critical", "warning", "info"
    rule: str
    title: str
    message: str
    metric_value: float
    threshold_value: float
    triggered_at: str
    acknowledged: bool
    acknowledged_at: str | None = None


class AlertListResponse(BaseModel):
    total_alerts: int
    active_count: int
    alerts: list[SystemAlertItem]


class AlertAcknowledgeResponse(BaseModel):
    id: str
    acknowledged: bool
    acknowledged_at: str
    message: str
