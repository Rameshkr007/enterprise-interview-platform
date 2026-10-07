from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import RecruiterUser
from app.core.exceptions import NotFoundException
from app.database import get_db
from app.models.candidate_twin import CandidateTwin
from app.models.recruiter import RecruiterRequisition, RequisitionCandidate
from app.models.user import User
from app.schemas.recruiter import (
    CandidateComparisonResponse,
    CandidateStageUpdateRequest,
    CompareCandidatesRequest,
    ExecutiveDebriefMemoResponse,
    InviteCandidateRequest,
    RequisitionCalibrationResponse,
    RequisitionCandidateResponse,
    RequisitionCreateRequest,
    RequisitionResponse,
    RequisitionUpdateRequest,
)
from app.services.audit_service import record_audit_event
from app.services.recruiter_copilot_service import RecruiterCopilotService

router = APIRouter(prefix="/recruiter", tags=["Recruiter Copilot"])

_recruiter_copilot = RecruiterCopilotService()


@router.post("/requisitions", response_model=RequisitionResponse, status_code=status.HTTP_201_CREATED)
async def create_requisition(
    body: RequisitionCreateRequest,
    current_user: RecruiterUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecruiterRequisition:
    """
    Feature 14: Creates a new role requisition with configurable scoring rubric weights
    (e.g., technical 30%, system design 25%, coding 25%, behavioral 20%).
    """
    req = await _recruiter_copilot.create_requisition(
        db=db,
        creator_id=current_user.id,
        title=body.title,
        department=body.department,
        seniority_level=body.seniority_level,
        description=body.description,
        required_skills=body.required_skills,
        rubric_weights=body.rubric_weights,
        hiring_threshold=body.hiring_threshold,
        org_id=current_user.org_id,
    )

    await record_audit_event(
        db=db,
        action="recruiter.requisition_created",
        entity_type="recruiter_requisition",
        entity_id=str(req.id),
        user_id=current_user.id,
        org_id=current_user.org_id,
        payload={"title": req.title, "weights": req.rubric_weights},
    )

    return req



@router.get("/requisitions", response_model=list[RequisitionResponse])
async def list_requisitions(
    current_user: RecruiterUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[RecruiterRequisition]:
    """
    Lists role requisitions accessible to the recruiter.
    """
    query = select(RecruiterRequisition).order_by(RecruiterRequisition.created_at.desc())
    if current_user.org_id:
        query = query.where(RecruiterRequisition.org_id == current_user.org_id)
    else:
        query = query.where(RecruiterRequisition.created_by == current_user.id)

    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/requisitions/{req_id}", response_model=RequisitionResponse)
async def get_requisition(
    req_id: UUID,
    current_user: RecruiterUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecruiterRequisition:
    """
    Retrieves requisition details.
    """
    req = await db.get(RecruiterRequisition, req_id)
    if req is None:
        raise NotFoundException("Requisition not found")
    return req


@router.patch("/requisitions/{req_id}", response_model=RequisitionResponse)
async def update_requisition(
    req_id: UUID,
    body: RequisitionUpdateRequest,
    current_user: RecruiterUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecruiterRequisition:
    """
    Updates role requisition details, hiring thresholds, or custom rubric weights.
    """
    req = await _recruiter_copilot.update_requisition(
        db=db,
        requisition_id=req_id,
        title=body.title,
        department=body.department,
        seniority_level=body.seniority_level,
        description=body.description,
        required_skills=body.required_skills,
        rubric_weights=body.rubric_weights,
        hiring_threshold=body.hiring_threshold,
        status=body.status,
    )
    await record_audit_event(
        db=db,
        action="recruiter.requisition_updated",
        entity_type="recruiter_requisition",
        entity_id=str(req.id),
        user_id=current_user.id,
        org_id=current_user.org_id,
        payload={"threshold": req.hiring_threshold, "status": req.status.value if hasattr(req.status, "value") else str(req.status)},
    )
    return req


@router.post("/requisitions/{req_id}/invite", response_model=RequisitionCandidateResponse, status_code=status.HTTP_201_CREATED)
async def invite_candidate_to_requisition(
    req_id: UUID,
    body: InviteCandidateRequest,
    current_user: RecruiterUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RequisitionCandidate:
    """
    Invites a candidate to the role's interview pipeline.
    """
    candidate_app = await _recruiter_copilot.invite_candidate(
        db=db,
        requisition_id=req_id,
        candidate_id=body.candidate_id,
    )

    await record_audit_event(
        db=db,
        action="recruiter.candidate_invited",
        entity_type="requisition_candidate",
        entity_id=str(candidate_app.id),
        user_id=current_user.id,
        org_id=current_user.org_id,
        payload={"requisition_id": str(req_id), "candidate_id": str(body.candidate_id)},
    )

    return candidate_app


@router.post("/requisitions/{req_id}/evaluate/{candidate_id}", response_model=RequisitionCandidateResponse)
async def evaluate_candidate_for_requisition(
    req_id: UUID,
    candidate_id: UUID,
    current_user: RecruiterUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RequisitionCandidate:
    """
    Feature 14: Recruiter Copilot AI Evaluation.
    Evaluates candidate against role-specific rubric weights and requirements,
    calculates composite score, verified skills, identified risks, and consensus recommendation.
    """
    candidate_app = await _recruiter_copilot.evaluate_candidate_for_requisition(
        db=db,
        requisition_id=req_id,
        candidate_id=candidate_id,
    )

    await record_audit_event(
        db=db,
        action="recruiter.candidate_evaluated",
        entity_type="requisition_candidate",
        entity_id=str(candidate_app.id),
        user_id=current_user.id,
        org_id=current_user.org_id,
        payload={
            "requisition_id": str(req_id),
            "candidate_id": str(candidate_id),
            "composite_score": candidate_app.composite_score,
            "recommendation": candidate_app.hiring_recommendation,
        },
    )

    return candidate_app


@router.post("/requisitions/{req_id}/compare", response_model=CandidateComparisonResponse)
async def compare_candidates(
    req_id: UUID,
    body: CompareCandidatesRequest,
    current_user: RecruiterUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Feature 14: Side-by-Side Candidate Comparison Matrix.
    Compares 2 or more candidates against identical job-relevant evidence:
    technical mastery, coding quality, system design rigor, behavioral ownership,
    and longitudinal growth velocity.
    """
    result = await _recruiter_copilot.compare_candidates_side_by_side(
        db=db,
        requisition_id=req_id,
        candidate_ids=body.candidate_ids,
    )

    await record_audit_event(
        db=db,
        action="recruiter.candidates_compared",
        entity_type="recruiter_requisition",
        entity_id=str(req_id),
        user_id=current_user.id,
        org_id=current_user.org_id,
        payload={"total_compared": result.get("total_compared")},
    )

    return result


@router.get("/requisitions/{req_id}/candidates", response_model=list[dict])
async def list_requisition_candidates(
    req_id: UUID,
    current_user: RecruiterUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    stage: str | None = None,
) -> list[dict]:
    """
    Lists candidates currently in the role requisition pipeline with evaluations and notes.
    """
    from app.models.recruiter import CandidateStage
    stage_enum = CandidateStage(stage) if stage else None
    return await _recruiter_copilot.list_requisition_candidates(
        db=db,
        requisition_id=req_id,
        stage=stage_enum,
    )


@router.patch("/requisitions/{req_id}/candidates/{candidate_id}/stage", response_model=RequisitionCandidateResponse)
async def update_candidate_stage(
    req_id: UUID,
    candidate_id: UUID,
    body: CandidateStageUpdateRequest,
    current_user: RecruiterUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RequisitionCandidate:
    """
    Updates a candidate's pipeline stage (e.g. interviewed -> offer/rejected) and appends recruiter notes.
    """
    cand = await _recruiter_copilot.update_candidate_stage(
        db=db,
        requisition_id=req_id,
        candidate_id=candidate_id,
        new_stage=body.stage,
        recruiter_notes=body.recruiter_notes,
    )
    await record_audit_event(
        db=db,
        action="recruiter.candidate_stage_updated",
        entity_type="requisition_candidate",
        entity_id=str(cand.id),
        user_id=current_user.id,
        org_id=current_user.org_id,
        payload={"requisition_id": str(req_id), "candidate_id": str(candidate_id), "stage": body.stage.value},
    )
    return cand


@router.get("/requisitions/{req_id}/calibration", response_model=RequisitionCalibrationResponse)
async def get_requisition_calibration(
    req_id: UUID,
    current_user: RecruiterUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Feature 15: Requisition Calibration Engine.
    Computes statistical percentiles, qualification rates, and what-if sensitivity curves.
    """
    return await _recruiter_copilot.calibrate_requisition(
        db=db,
        requisition_id=req_id,
    )


@router.get("/requisitions/{req_id}/debrief-memo/{candidate_id}", response_model=ExecutiveDebriefMemoResponse)
async def get_executive_debrief_memo(
    req_id: UUID,
    candidate_id: UUID,
    current_user: RecruiterUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Feature 15: Bar-Raiser Executive Hiring Debrief Memo.
    Synthesizes multi-pillar interview evidence into a structured markdown debrief briefing.
    """
    return await _recruiter_copilot.generate_executive_debrief_memo(
        db=db,
        requisition_id=req_id,
        candidate_id=candidate_id,
    )



@router.get("/requisitions/{req_id}/talent-pool", response_model=list[dict])
async def search_talent_pool(
    req_id: UUID,
    current_user: RecruiterUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    min_score: float = Query(default=60.0, ge=0.0, le=100.0),
    top_k: int = Query(default=10, ge=1, le=50),
) -> list[dict]:
    """
    Searches the candidate talent pool for candidates meeting or exceeding readiness thresholds.
    """
    return await _recruiter_copilot.search_talent_pool(
        db=db,
        requisition_id=req_id,
        min_score=min_score,
        top_k=top_k,
    )


@router.get("/talent-pool/search", response_model=list[dict])
async def search_talent_pool_global(
    current_user: RecruiterUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    min_readiness: float = Query(default=60.0, ge=0.0, le=100.0),
    min_score: float | None = None,
    required_skills: str | None = None,
    top_k: int = Query(default=10, ge=1, le=50),
) -> list[dict]:
    """
    Global talent pool search across all candidate twins by readiness threshold and required skills.
    """
    threshold = min_score if min_score is not None else min_readiness
    req_skills_list = [s.strip().lower() for s in required_skills.split(",")] if required_skills else []
    result = await db.execute(
        select(CandidateTwin, User)
        .join(User, CandidateTwin.user_id == User.id)
        .where(CandidateTwin.overall_readiness_score >= threshold)
        .order_by(CandidateTwin.overall_readiness_score.desc())
        .limit(top_k)
    )
    rows = result.all()
    matches = []
    for twin, user in rows:
        mastered = [s.get("topic", "").lower() for s in twin.strong_areas]
        verified = [s for s in req_skills_list if any(s in m or m in s for m in mastered)]
        coverage = round((len(verified) / max(len(req_skills_list), 1)) * 100, 1) if req_skills_list else 100.0
        matches.append({
            "candidate_id": str(user.id),
            "full_name": user.full_name,
            "email": user.email,
            "readiness_score": twin.overall_readiness_score,
            "skill_match_percentage": coverage,
            "verified_skills": verified,
            "growth_velocity": twin.growth_velocity,
        })
    return matches
