from __future__ import annotations

import time
import uuid
from typing import Annotated, Any
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import PlainTextResponse

from app.core.exceptions import NotFoundException
from app.schemas.observability import (
    AlertAcknowledgeResponse,
    AlertListResponse,
    DeepHealthResponse,
    MetricsSummaryResponse,
    SpanRecord,
    SystemAlertItem,
    TraceListResponse,
    TraceRecord,
)
from app.services.observability_service import (
    AlertEngine,
    MetricsCollector,
    TraceCollector,
    run_deep_health_check,
)

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/observability", tags=["Production Observability"])


@router.get("/metrics/summary", response_model=MetricsSummaryResponse)
async def get_metrics_summary() -> MetricsSummaryResponse:
    """Returns real-time latency percentiles (p50, p95, p99), error budgets, and service availability."""
    collector = MetricsCollector.get_instance()
    summary = collector.get_summary()
    # Evaluate alerting rules on live metrics
    AlertEngine.get_instance().evaluate_rules(summary)
    return summary


@router.get("/metrics/prometheus", response_class=PlainTextResponse)
async def get_prometheus_metrics() -> str:
    """Exposes real-time system metrics in standard Prometheus text format."""
    collector = MetricsCollector.get_instance()
    return collector.to_prometheus_format()


@router.get("/health/deep", response_model=DeepHealthResponse)
async def get_deep_health() -> DeepHealthResponse:
    """Executes live diagnostic health probes across database, redis, vector storage, and sandbox components."""
    return await run_deep_health_check()


# ── Distributed Tracing Endpoints ─────────────────────────────────────────────

@router.get("/traces", response_model=TraceListResponse)
async def get_traces(
    min_duration_ms: float = Query(0.0, ge=0.0),
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> TraceListResponse:
    """Returns collected distributed trace spans across subsystem hops."""
    collector = TraceCollector.get_instance()
    traces = collector.get_traces(min_duration_ms=min_duration_ms, status=status, limit=limit)
    return TraceListResponse(total_traces=len(traces), traces=traces)


@router.get("/traces/{trace_id}", response_model=TraceRecord)
async def get_trace_by_id(trace_id: str) -> TraceRecord:
    """Retrieves a single distributed trace with child span waterfall."""
    collector = TraceCollector.get_instance()
    trace = collector.get_trace_by_id(trace_id)
    if trace is None:
        raise NotFoundException(f"Trace {trace_id} not found")
    return trace


@router.post("/traces", response_model=TraceRecord, status_code=201)
async def record_synthetic_trace(
    root_endpoint: str = Query(..., description="Root API path"),
    duration_ms: float = Query(..., ge=0.0),
    service: str = Query("api_gateway"),
    status: str = Query("ok"),
) -> TraceRecord:
    """Records a synthetic or client-reported distributed trace span."""
    collector = TraceCollector.get_instance()
    trace_id = uuid.uuid4().hex
    corr_id = f"corr_{uuid.uuid4().hex[:12]}"

    spans = [
        SpanRecord(
            span_name="http_request_ingress",
            service="api_gateway",
            duration_ms=round(duration_ms * 0.15, 2),
            status="ok",
            metadata={"endpoint": root_endpoint},
        ),
        SpanRecord(
            span_name=f"{service}_execution",
            service=service,
            duration_ms=round(duration_ms * 0.75, 2),
            status=status,
            metadata={"caller": "test_client"},
        ),
        SpanRecord(
            span_name="http_response_egress",
            service="api_gateway",
            duration_ms=round(duration_ms * 0.10, 2),
            status="ok",
            metadata={},
        ),
    ]

    return collector.record_trace(
        trace_id=trace_id,
        correlation_id=corr_id,
        root_endpoint=root_endpoint,
        total_duration_ms=duration_ms,
        spans=spans,
        status=status,
    )


# ── Alerting & Incident Endpoints ─────────────────────────────────────────────

@router.get("/alerts", response_model=AlertListResponse)
async def get_alerts(only_active: bool = Query(False)) -> AlertListResponse:
    """Returns active or acknowledged system incidents and threshold breach alerts."""
    engine = AlertEngine.get_instance()
    alerts = engine.get_alerts(only_active=only_active)
    active_cnt = sum(1 for a in alerts if not a.acknowledged)
    return AlertListResponse(total_alerts=len(alerts), active_count=active_cnt, alerts=alerts)


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertAcknowledgeResponse)
async def acknowledge_alert(alert_id: str) -> AlertAcknowledgeResponse:
    """Marks an active incident alert as acknowledged by an operator."""
    engine = AlertEngine.get_instance()
    alert = engine.acknowledge_alert(alert_id)
    if alert is None:
        raise NotFoundException(f"Alert {alert_id} not found")
    return AlertAcknowledgeResponse(
        id=alert.id,
        acknowledged=True,
        acknowledged_at=alert.acknowledged_at or datetime.now(UTC).isoformat(),
        message=f"Alert {alert_id} acknowledged successfully.",
    )
