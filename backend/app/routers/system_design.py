from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID, uuid4

import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.core.exceptions import NotFoundException, SessionNotFoundException
from app.database import get_db
from app.models.interview_session import InterviewSession
from app.services.audit_service import record_audit_event
from app.services.system_design_service import SystemDesignEngine, SystemDesignEvaluation

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/system-design", tags=["System Design Interview"])

# Curated catalog of enterprise system design scenarios
SYSTEM_DESIGN_SCENARIOS = {
    "distributed_rate_limiter": {
        "title": "Design a Distributed Rate Limiter for an API Gateway",
        "domain": "Infrastructure & Networking",
        "prompt": (
            "Design a resilient, low-latency distributed rate limiter capable of throttling millions of requests per second "
            "across global edge regions. Support configurable algorithms (Token Bucket, Sliding Window Counter), per-tier quotas, "
            "sub-millisecond overhead, and graceful degradation during network partitions."
        ),
        "target_scale": "500,000 requests/sec peak, <2ms latency SLA, 99.999% availability",
        "key_focus_areas": ["Redis cluster / Token Bucket", "Clock drift across regions", "Local in-memory vs centralized sync", "Failure open vs failure closed"],
    },
    "notification_service": {
        "title": "Design a Real-Time Distributed Notification Engine",
        "domain": "Distributed Systems & Messaging",
        "prompt": (
            "Design a multi-channel notification platform (Push, Email, SMS, WebSockets) serving 100M daily active users. "
            "Handle user preference deduplication, priority queues (critical OTPs vs marketing broadcasts), idempotency, "
            "vendor rate-limit backpressure, and guaranteed at-least-once delivery."
        ),
        "target_scale": "100M notifications/day, burst capacity of 50,000/sec, delivery latency <1s for critical alerts",
        "key_focus_areas": ["Message broker partitioning", "Dead letter queues & exponential retries", "User rate-limiting & quiet hours", "Idempotency keys"],
    },
    "global_video_streaming": {
        "title": "Design a Global Video Streaming Platform (Netflix / YouTube Scale)",
        "domain": "Multimedia & Content Delivery",
        "prompt": (
            "Architect the backend and content delivery network for a global video streaming platform. "
            "Address adaptive bitrate streaming (HLS/DASH), multi-region CDN caching, video chunk transcoding workers, "
            "metadata persistence, and high-concurrency watch history tracking."
        ),
        "target_scale": "50M concurrent video streams, petabyte-scale storage, 99.99% playback uptime",
        "key_focus_areas": ["CDN edge caching topologies", "Transcoding pipeline asynchronous workers", "Chunked media storage", "Watch progress eventual consistency"],
    },
}


class SystemDesignChallengeRequest(BaseModel):
    session_id: UUID
    scenario_key: str | None = None  # Optional specific key, or auto-selected


class SystemDesignEvaluateRequest(BaseModel):
    session_id: UUID
    problem_title: str
    problem_prompt: str
    architecture_sections: dict[str, Any] = Field(
        ...,
        description="Structured sections e.g. requirements, non_functional, high_level, data_model, api_design, scalability, resilience, trade_offs",
    )
    whiteboard_components: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Optional visual diagram nodes and connections",
    )


@router.get("/scenarios", response_model=list[dict[str, Any]])
async def list_scenarios(current_user: CurrentUser) -> list[dict[str, Any]]:
    """List available enterprise system design challenge scenarios."""
    return [
        {"key": k, **v}
        for k, v in SYSTEM_DESIGN_SCENARIOS.items()
    ]


@router.get("/pillars", response_model=dict[str, Any])
async def get_evaluation_pillars(current_user: CurrentUser) -> dict[str, Any]:
    """Get the 8 architectural pillars and scoring rubric weights."""
    return {
        "pillars": [
            {"id": "requirements_clarification", "name": "Requirements & Scope Clarification", "weight": 0.10},
            {"id": "non_functional_requirements", "name": "Non-Functional Requirements & Capacity", "weight": 0.15},
            {"id": "high_level_architecture", "name": "High-Level Component Topology", "weight": 0.15},
            {"id": "data_model_and_storage", "name": "Data Model, Schemas & Storage Engines", "weight": 0.15},
            {"id": "api_design", "name": "API Contracts & Protocol Design", "weight": 0.10},
            {"id": "scalability_and_partitioning", "name": "Scalability, Sharding & Caching", "weight": 0.15},
            {"id": "failure_modes_and_resilience", "name": "Failure Modes, SPOF & Disaster Recovery", "weight": 0.10},
            {"id": "trade_offs_and_deep_dive", "name": "Trade-offs & Concrete Justification", "weight": 0.10},
        ],
        "anti_buzzword_policy": "Unsupported usage of complex technologies (Kafka, Cassandra, Kubernetes) without explaining sizing or failure modes incurs score penalties.",
    }


@router.post("/challenge", response_model=dict[str, Any], status_code=201)
async def create_system_design_challenge(
    body: SystemDesignChallengeRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Retrieve or configure a system design challenge for an interview session."""
    session = await db.get(InterviewSession, body.session_id)
    if session is None or session.user_id != current_user.id:
        raise SessionNotFoundException()

    scenario_key = body.scenario_key or "distributed_rate_limiter"
    scenario = SYSTEM_DESIGN_SCENARIOS.get(scenario_key, SYSTEM_DESIGN_SCENARIOS["distributed_rate_limiter"])

    challenge_id = uuid4()
    return {
        "challenge_id": str(challenge_id),
        "session_id": str(session.id),
        "title": scenario["title"],
        "domain": scenario["domain"],
        "prompt": scenario["prompt"],
        "target_scale": scenario["target_scale"],
        "key_focus_areas": scenario["key_focus_areas"],
        "template_sections": [
            "1. Functional Requirements & Scope",
            "2. Non-Functional Requirements (Throughput, Latency, SLA)",
            "3. High-Level Architecture & Components",
            "4. Data Model, Schemas & Storage Engines",
            "5. API Endpoints & Contracts",
            "6. Scalability, Partitioning & Caching Strategy",
            "7. Failure Modes, SPOF & Fault Tolerance",
            "8. Core Architectural Trade-offs",
        ],
    }


@router.post("/evaluate", response_model=dict[str, Any])
async def evaluate_system_design(
    body: SystemDesignEvaluateRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Evaluate architectural proposal across 8 pillars with anti-buzzword verification."""
    session = await db.get(InterviewSession, body.session_id)
    if session is None or session.user_id != current_user.id:
        raise SessionNotFoundException()

    engine = SystemDesignEngine()
    eval_result: SystemDesignEvaluation = await engine.evaluate_architecture(
        problem_title=body.problem_title,
        problem_prompt=body.problem_prompt,
        candidate_submission=body.architecture_sections,
    )

    # Record Audit Event
    await record_audit_event(
        db=db,
        action="system_design.evaluated",
        entity_type="system_design_submission",
        user_id=session.user_id,
        org_id=session.org_id,
        entity_id=str(session.id),
        payload={
            "score": eval_result.overall_score,
            "tier": eval_result.tier,
            "buzzword_penalty": eval_result.buzzword_analysis.penalty_applied,
            "unjustified_buzzwords": len(eval_result.buzzword_analysis.unjustified_buzzwords),
        },
    )
    await db.commit()

    return eval_result.to_dict()


class ValidateGraphRequest(BaseModel):
    components: list[dict[str, Any]] = Field(default_factory=list)
    connections: list[dict[str, Any]] = Field(default_factory=list)


@router.post("/validate-graph", response_model=dict[str, Any])
async def validate_architecture_graph(
    body: ValidateGraphRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Topological graph validation and algorithmic Single Point of Failure (SPOF) detection."""
    engine = SystemDesignEngine()
    return engine.validate_architecture_graph(
        components=body.components,
        connections=body.connections,
    )


class CapacityEstimateRequest(BaseModel):
    scenario_key: str = "distributed_rate_limiter"
    estimates: dict[str, Any] = Field(..., description="Map of metrics: read_qps, write_qps, daily_storage_gb, bandwidth_gbps, ram_cache_gb")


@router.post("/capacity-estimate", response_model=dict[str, Any])
async def evaluate_capacity_estimation(
    body: CapacityEstimateRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Validates candidate back-of-the-envelope capacity estimations against benchmark baselines."""
    engine = SystemDesignEngine()
    return engine.verify_capacity_estimation(
        scenario_key=body.scenario_key,
        candidate_estimates=body.estimates,
    )


class ClarificationRequest(BaseModel):
    scenario_key: str
    question: str = Field(..., min_length=5)


@router.post("/clarify", response_model=dict[str, Any])
async def ask_clarification(
    body: ClarificationRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Collaborative Bar-Raiser persona answering candidate's scope and NFR clarification questions."""
    engine = SystemDesignEngine()
    return await engine.answer_clarification(
        scenario_key=body.scenario_key,
        question=body.question,
    )


@router.get("/scenarios/{scenario_key}", response_model=dict[str, Any])
async def get_scenario_detail(
    scenario_key: str,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Get detailed challenge requirements for a specific scenario."""
    if scenario_key not in SYSTEM_DESIGN_SCENARIOS:
        raise NotFoundException(f"Scenario '{scenario_key}' not found.")
    return {"key": scenario_key, **SYSTEM_DESIGN_SCENARIOS[scenario_key]}

