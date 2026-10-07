from __future__ import annotations

import time
from collections.abc import Callable

import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import AppBaseException

log = structlog.get_logger(__name__)


class GlobalExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        try:
            response = await call_next(request)
            return response
        except AppBaseException as exc:
            log.warning(
                "app_exception",
                path=request.url.path,
                method=request.method,
                error_code=exc.error_code,
                message=exc.message,
            )
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.to_dict(),
                headers=exc.headers,
            )
        except ValidationError as exc:
            log.warning("pydantic_validation_error", errors=exc.errors())
            return JSONResponse(
                status_code=422,
                content={
                    "error_code": "VALIDATION_ERROR",
                    "message": "Request body validation failed",
                    "details": exc.errors(include_url=False),
                },
            )
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            log.exception(
                "unhandled_exception",
                path=request.url.path,
                method=request.method,
                elapsed_ms=elapsed,
                error=str(exc),
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error_code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred. Please try again.",
                },
            )


import uuid


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        corr_id = request.headers.get("X-Correlation-ID") or request.headers.get("X-Trace-ID") or f"corr_{uuid.uuid4().hex[:12]}"
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000

        # Inject correlation header in response
        response.headers["X-Correlation-ID"] = corr_id

        log.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            elapsed_ms=round(elapsed, 2),
            correlation_id=corr_id,
            client_ip=request.client.host if request.client else None,
        )
        try:
            from app.services.observability_service import MetricsCollector, TraceCollector, SpanRecord
            MetricsCollector.get_instance().record_request(request.url.path, elapsed, response.status_code)

            # Record request trace (skipping telemetry queries to prevent loop recursion)
            if not request.url.path.startswith("/api/v1/observability") and not request.url.path.startswith("/health") and request.url.path != "/metrics":
                TraceCollector.get_instance().record_trace(
                    trace_id=uuid.uuid4().hex,
                    correlation_id=corr_id,
                    root_endpoint=f"{request.method} {request.url.path}",
                    total_duration_ms=elapsed,
                    spans=[
                        SpanRecord(
                            span_name="http_request_ingress",
                            service="api_gateway",
                            duration_ms=round(elapsed * 0.2, 2),
                            status="ok",
                        ),
                        SpanRecord(
                            span_name="endpoint_execution",
                            service="business_logic",
                            duration_ms=round(elapsed * 0.8, 2),
                            status="ok" if response.status_code < 500 else "error",
                        ),
                    ],
                    status="ok" if response.status_code < 500 else "error",
                )
        except Exception:
            pass
        return response

