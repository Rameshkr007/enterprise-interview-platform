from __future__ import annotations

import logging
import sys

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.config import get_settings
from app.database import dispose_engine
from app.middleware.error_handler import GlobalExceptionMiddleware, RequestLoggingMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.rate_limiter import RateLimitMiddleware
from app.middleware.server_timing import ServerTimingMiddleware
from app.routers import auth, ats, interview, reports, websocket_router, organization, resumes
from app.routers import analytics, coding, resume_builder, gamification, job_tracker, negotiation, system_design, behavioral
from app.routers import learning, candidate_twin, recruiter, ai_governance, resilience, observability, enterprise_analytics, audit, skill_graph, security, diagnostics, performance, deployment
from fastapi.responses import PlainTextResponse


settings = get_settings()

# ── Structured Logging ────────────────────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
logging.basicConfig(stream=sys.stdout, level=getattr(logging, settings.LOG_LEVEL))


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Enterprise AI-Powered Mock Interview & Semantic ATS Analyzer",
        docs_url="/api/docs" if settings.DEBUG else None,
        redoc_url="/api/redoc" if settings.DEBUG else None,
        openapi_url="/api/openapi.json" if settings.DEBUG else None,
        default_response_class=ORJSONResponse,
    )

    # ── Middleware (order matters: outermost first) ────────────────────────────
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(ServerTimingMiddleware)
    app.add_middleware(GlobalExceptionMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    prefix = settings.API_PREFIX
    app.include_router(auth.router, prefix=prefix)
    app.include_router(ats.router, prefix=prefix)
    app.include_router(interview.router, prefix=prefix)
    app.include_router(reports.router, prefix=prefix)
    app.include_router(websocket_router.router)  # No prefix: /ws/interview/{id}
    app.include_router(analytics.router, prefix=prefix)
    app.include_router(coding.router, prefix=prefix)
    app.include_router(resume_builder.router, prefix=prefix)
    app.include_router(gamification.router, prefix=prefix)
    app.include_router(job_tracker.router, prefix=prefix)
    app.include_router(negotiation.router, prefix=prefix)
    app.include_router(organization.router, prefix=prefix)
    app.include_router(resumes.router, prefix=prefix)
    app.include_router(system_design.router, prefix=prefix)
    app.include_router(behavioral.router, prefix=prefix)
    app.include_router(learning.router, prefix=prefix)
    app.include_router(candidate_twin.router, prefix=prefix)
    app.include_router(recruiter.router, prefix=prefix)
    app.include_router(ai_governance.router, prefix=prefix)
    app.include_router(resilience.router, prefix=prefix)
    app.include_router(observability.router, prefix=prefix)
    app.include_router(enterprise_analytics.router, prefix=prefix)
    app.include_router(audit.router, prefix=prefix)
    app.include_router(skill_graph.router, prefix=prefix)
    app.include_router(security.router, prefix=prefix)
    app.include_router(diagnostics.router, prefix=prefix)
    app.include_router(performance.router, prefix=prefix)
    app.include_router(deployment.router, prefix=prefix)

    # ── Query Profiler Hook ──────────────────────────────────────────────────
    from app.database import engine
    from app.services.query_profiler import QueryProfiler
    QueryProfiler.get_instance().attach_to_engine(engine)


    # ── Lifecycle ─────────────────────────────────────────────────────────────
    @app.on_event("startup")
    async def startup_event() -> None:
        from app.core.db_init import auto_init_database
        await auto_init_database()

    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        from app.core.redis import close_redis_pool
        await dispose_engine()
        await close_redis_pool()

    @app.get("/", tags=["Root"], include_in_schema=False)
    async def root() -> dict:
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "online",
            "health": "/health",
            "api_prefix": settings.API_PREFIX,
        }

    @app.get("/health", tags=["Health"], include_in_schema=False)
    async def health() -> dict:
        from app.database import check_database_health
        from app.core.redis import check_redis_health

        db_ok = await check_database_health()
        redis_ok = await check_redis_health()
        is_healthy = db_ok and redis_ok

        return {
            "status": "healthy" if is_healthy else "degraded",
            "version": settings.APP_VERSION,
            "environment": settings.ENV,
            "checks": {
                "database": "reachable" if db_ok else "unreachable",
                "redis": "reachable" if redis_ok else "unreachable",
            },
        }

    @app.get("/metrics", response_class=PlainTextResponse, tags=["Observability"], include_in_schema=False)
    async def prometheus_metrics() -> str:
        from app.services.observability_service import MetricsCollector
        return MetricsCollector.get_instance().to_prometheus_format()

    return app


app = create_app()
