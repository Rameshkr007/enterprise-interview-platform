from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.core.exceptions import NotFoundException, SessionNotFoundException
from app.database import get_db
from app.models.interview_session import InterviewSession
from app.services.audit_service import record_audit_event
from app.services.behavioral_service import BehavioralSTAREngine, STARBehavioralEvaluation

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/behavioral", tags=["Behavioral STAR Interview"])

# Curated Amazon Leadership Principles & Google Structured Behavioral Questions
BEHAVIORAL_QUESTIONS_CATALOG: list[dict[str, Any]] = [
    {
        "id": "ownership_complex_failure",
        "competency": "ownership",
        "title": "Taking Ownership During System Outage",
        "question": "Tell me about a time when a critical system or project failed under your watch. What was your personal responsibility, what immediate actions did you take, and how did you prevent recurrence?",
        "evaluation_criteria": ["Distinguish personal actions from team actions", "Accountability without blame", "Root cause post-mortem", "Quantifiable recovery time"],
    },
    {
        "id": "deliver_results_tight_deadline",
        "competency": "deliver_results",
        "title": "Delivering Under Aggressive Constraints",
        "question": "Describe a project where you faced tight deadlines and unexpected roadblocks. How did you prioritize technical debt versus delivery, and what were the measurable results?",
        "evaluation_criteria": ["Clear prioritization framework", "Measurable delivery outcome", "Management of technical debt", "Stakeholder communication"],
    },
    {
        "id": "disagree_and_commit",
        "competency": "conflict_resolution",
        "title": "Technical Disagreement with Senior Stakeholders",
        "question": "Give an example of a tough technical disagreement you had with an architect, manager, or peer. How did you present your data, how was the dispute resolved, and how did you commit to the final decision?",
        "evaluation_criteria": ["Data-driven argumentation", "Professional empathy", "Disagree and commit ethos", "Post-decision alignment"],
    },
    {
        "id": "customer_obsession_metrics",
        "competency": "customer_obsession",
        "title": "Advocating for Customer Performance",
        "question": "Tell me about a time when you identified a non-obvious customer pain point or performance bottleneck. How did you investigate it and what impact did your solution have on end users?",
        "evaluation_criteria": ["Proactive investigation", "Telemetry and data analysis", "Quantifiable customer impact (latency, satisfaction, error rate)"],
    },
    {
        "id": "bias_for_action_ambiguity",
        "competency": "bias_for_action",
        "title": "Decisive Action Under Incomplete Data",
        "question": "Describe a scenario where you had to make an urgent architectural or product decision with incomplete information. How did you assess risk, calculate reversibility, and validate the outcome?",
        "evaluation_criteria": ["Two-way door vs one-way door risk assessment", "Decisive speed", "Monitoring and rollback plan", "Post-launch validation"],
    },
]


class STAREvaluateRequest(BaseModel):
    session_id: UUID | None = None
    question: str = Field(..., min_length=10)
    answer_transcript: str = Field(..., min_length=20, max_length=10_000)
    competency: str = Field(default="ownership")


@router.get("/questions", response_model=list[dict[str, Any]])
async def list_behavioral_questions(
    current_user: CurrentUser,
    competency: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve structured behavioral questions filtered by competency."""
    if competency:
        comp_lower = competency.lower()
        return [q for q in BEHAVIORAL_QUESTIONS_CATALOG if q["competency"] == comp_lower]
    return BEHAVIORAL_QUESTIONS_CATALOG


@router.post("/evaluate-star", response_model=dict[str, Any])
async def evaluate_star(
    body: STAREvaluateRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Evaluate candidate response using STAR methodology, ownership audit, and metric detection."""
    org_id = None
    if body.session_id:
        session = await db.get(InterviewSession, body.session_id)
        if session:
            org_id = session.org_id

    engine = BehavioralSTAREngine()
    eval_result: STARBehavioralEvaluation = await engine.evaluate_star_answer(
        question=body.question,
        answer_transcript=body.answer_transcript,
        competency=body.competency,
    )

    # Record Audit Event
    await record_audit_event(
        db=db,
        action="behavioral.star_evaluated",
        entity_type="behavioral_evaluation",
        user_id=current_user.id,
        org_id=org_id,
        payload={
            "competency": body.competency,
            "overall_score": eval_result.overall_score,
            "i_we_ratio": eval_result.ownership_metrics.i_we_ratio,
            "ownership_level": eval_result.ownership_metrics.ownership_level,
            "verdict": eval_result.bar_raiser_verdict,
            "quantifiable_metrics_count": len(eval_result.quantifiable_metrics_found),
            "flag_count": len(eval_result.flags),
        },
    )
    await db.commit()

    return eval_result.to_dict()


@router.get("/competencies", response_model=list[dict[str, Any]])
async def list_competencies(current_user: CurrentUser) -> list[dict[str, Any]]:
    """Retrieve full catalog of enterprise leadership principles (Amazon LPs, Google, Meta)."""
    return BehavioralSTAREngine.get_leadership_competencies()


@router.get("/questions/{question_id}", response_model=dict[str, Any])
async def get_behavioral_question(
    question_id: str,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Retrieve detailed question information and evaluation criteria by ID."""
    for q in BEHAVIORAL_QUESTIONS_CATALOG:
        if q["id"] == question_id:
            return q
    raise NotFoundException(f"Question with ID '{question_id}' not found.")


class FollowUpProbesRequest(BaseModel):
    question: str = Field(..., min_length=10)
    answer_transcript: str = Field(..., min_length=20)
    competency: str = "ownership"


@router.post("/follow-up-probes", response_model=dict[str, Any])
async def generate_probes(
    body: FollowUpProbesRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Generate high-pressure Bar-Raiser follow-up probes tailored to candidate response weaknesses."""
    engine = BehavioralSTAREngine()
    eval_result = await engine.evaluate_star_answer(
        question=body.question,
        answer_transcript=body.answer_transcript,
        competency=body.competency,
    )
    probes = engine.generate_follow_up_probes(
        question=body.question,
        answer_transcript=body.answer_transcript,
        eval_result=eval_result,
    )
    return {
        "question": body.question,
        "competency": body.competency,
        "probes": probes,
        "weakest_area": eval_result.ownership_metrics.ownership_level if eval_result.ownership_metrics.ownership_level == "Passive/Ambiguous Team Attribution" else "Quantifiable Business Results",
    }


class STARReframeRequest(BaseModel):
    question: str = Field(..., min_length=10)
    raw_answer: str = Field(..., min_length=20)
    competency: str = "ownership"


@router.post("/reframe", response_model=dict[str, Any])
async def reframe_star_story(
    body: STARReframeRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Transform candidate's narrative into an executive STAR+L story with bold metrics and active ownership."""
    engine = BehavioralSTAREngine()
    return engine.generate_executive_reframe(
        question=body.question,
        answer_transcript=body.raw_answer,
        competency=body.competency,
    )

