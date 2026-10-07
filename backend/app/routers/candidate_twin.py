from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.database import get_db
from app.models.candidate_twin import CandidateTwin
from app.schemas.candidate_twin import (
    CandidateTwinResponse,
    ExplainScoreResponse,
    TwinBenchmarkResponse,
    TwinHistoryEventResponse,
)
from app.services.audit_service import record_audit_event
from app.services.candidate_twin_service import CandidateTwinEngine

router = APIRouter(tags=["Candidate AI Twin & Explainable AI"])

_twin_engine = CandidateTwinEngine()


@router.get("/twin/me", response_model=CandidateTwinResponse)
@router.get("/twin/my", response_model=CandidateTwinResponse)
@router.get("/candidate-twin/me", response_model=CandidateTwinResponse)
@router.get("/candidate-twin/my", response_model=CandidateTwinResponse)
async def get_my_candidate_twin(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CandidateTwin:
    """
    Feature 13: Retrieves the candidate's longitudinal AI Twin model.
    Tracks technical mastery, communication telemetry, coding performance,
    chronological score progression, and growth velocity.
    """
    return await _twin_engine.sync_twin_from_history(db, current_user.id)


@router.post("/twin/sync", response_model=CandidateTwinResponse)
@router.post("/candidate-twin/sync", response_model=CandidateTwinResponse)
async def sync_candidate_twin(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CandidateTwin:
    """
    Forces a comprehensive re-evaluation of all interview sessions,
    coding challenges, and learning plans to update the candidate twin.
    """
    twin = await _twin_engine.sync_twin_from_history(db, current_user.id)
    await record_audit_event(
        db=db,
        action="candidate_twin.synced",
        entity_type="candidate_twin",
        entity_id=str(twin.id),
        user_id=current_user.id,
        payload={"readiness_score": twin.overall_readiness_score, "velocity": twin.growth_velocity},
    )
    return twin


@router.get("/twin/history", response_model=list[TwinHistoryEventResponse])
@router.get("/candidate-twin/history", response_model=list[TwinHistoryEventResponse])
async def get_candidate_twin_history(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    event_type: str | None = None,
) -> list[dict]:
    """
    Retrieves chronological milestone telemetry across sessions, coding,
    SM-2 memory reviews, and learning plans.
    """
    return await _twin_engine.get_chronological_history(
        db=db, user_id=current_user.id, event_type=event_type
    )


@router.get("/twin/benchmarks", response_model=TwinBenchmarkResponse)
@router.get("/candidate-twin/benchmarks", response_model=TwinBenchmarkResponse)
async def get_candidate_twin_benchmarks(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Feature 14 Peer Benchmarks:
    Calculates Gaussian percentiles against representative enterprise cohort.
    """
    return await _twin_engine.get_peer_benchmarks(db=db, user_id=current_user.id)


@router.get("/twin/explain/{dimension}", response_model=ExplainScoreResponse)
@router.get("/twin/my/explain/{dimension}", response_model=ExplainScoreResponse)
@router.get("/candidate-twin/explain/{dimension}", response_model=ExplainScoreResponse)
@router.get("/candidate-twin/my/explain/{dimension}", response_model=ExplainScoreResponse)
async def explain_candidate_score(
    dimension: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Feature 16 Explainable AI:
    Breaks down exactly:
    - What was evaluated?
    - What evidence was found?
    - Why was the score assigned?
    - What is missing?
    - How can the candidate improve?
    """
    return await _twin_engine.explain_score_dimension(
        db=db, user_id=current_user.id, dimension=dimension
    )
