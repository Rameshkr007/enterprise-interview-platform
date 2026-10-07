from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.recruiter import CandidateStage, RequisitionStatus


class RequisitionCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=512)
    department: str = Field(default="Engineering", max_length=255)
    seniority_level: str = Field(default="senior", max_length=50)
    description: str = Field(default="")
    required_skills: list[str] = Field(default_factory=list)
    rubric_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "technical": 0.30,
            "system_design": 0.25,
            "coding": 0.25,
            "behavioral": 0.20,
        }
    )
    hiring_threshold: float = Field(default=75.0, ge=0.0, le=100.0)


class InviteCandidateRequest(BaseModel):
    candidate_id: UUID


class RequisitionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    org_id: UUID | None
    created_by: UUID
    title: str
    department: str
    seniority_level: str
    description: str
    required_skills: list[str]
    rubric_weights: dict[str, float]
    hiring_threshold: float
    status: RequisitionStatus
    created_at: datetime
    updated_at: datetime


class RequisitionCandidateResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    requisition_id: UUID
    candidate_id: UUID
    status: CandidateStage
    stage_evaluations: dict
    composite_score: float | None
    hiring_recommendation: str | None
    evidence_summary: dict | None
    recruiter_notes: str | None
    invited_at: datetime
    updated_at: datetime


class CompareCandidatesRequest(BaseModel):
    candidate_ids: list[UUID] = Field(..., min_length=1)


class CandidateComparisonResponse(BaseModel):
    requisition_id: str
    role_title: str
    rubric_weights: dict[str, float]
    hiring_threshold: float
    total_compared: int
    top_candidate_id: str | None
    matrix: list[dict]


class RequisitionUpdateRequest(BaseModel):
    title: str | None = None
    department: str | None = None
    seniority_level: str | None = None
    description: str | None = None
    required_skills: list[str] | None = None
    rubric_weights: dict[str, float] | None = None
    hiring_threshold: float | None = Field(default=None, ge=0.0, le=100.0)
    status: RequisitionStatus | None = None


class CandidateStageUpdateRequest(BaseModel):
    stage: CandidateStage
    recruiter_notes: str | None = None


class RequisitionCalibrationResponse(BaseModel):
    requisition_id: UUID
    role_title: str
    current_threshold: float
    total_candidates: int
    qualified_count: int
    pass_rate_pct: float
    score_statistics: dict[str, float]
    sensitivity_curve: list[dict]
    calibration_guidance: str


class ExecutiveDebriefMemoResponse(BaseModel):
    requisition_id: UUID
    candidate_id: UUID
    candidate_name: str
    role_title: str
    composite_score: float
    hiring_threshold: float
    hiring_recommendation: str
    memo_markdown: str
    evidence_pillars: dict
    key_strengths: list[str]
    identified_risks: list[str]
    suggested_debrief_questions: list[str]
    generated_at: str
