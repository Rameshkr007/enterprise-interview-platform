from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.ats_analysis import AtsMatchTier


class SkillGap(BaseModel):
    skill_name: str
    gap_type: str
    jd_importance: float = Field(default=1.0)
    suggested_action: str = ""


class MatchedSkill(BaseModel):
    skill_name: str
    match_type: str
    evidence: str
    confidence: float = Field(default=1.0)


class AtsAnalyzeRequest(BaseModel):
    resume_id: UUID
    jd_id: UUID


class MultiJobMatchRequest(BaseModel):
    resume_id: UUID
    jd_ids: list[UUID] = Field(..., min_length=1, max_length=20)


class JobDescriptionCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=512)
    company: str | None = Field(default=None, max_length=255)
    raw_text: str = Field(..., min_length=50)


class JobMatchSummaryResponse(BaseModel):
    jd_id: UUID
    title: str
    company: str | None
    overall_score: float
    recommendation: str
    match_tier: AtsMatchTier
    technical_score: float
    seniority_fit: str
    critical_gaps: list[str]
    key_strengths: list[str]


class AtsAnalysisResult(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    resume_id: UUID
    jd_id: UUID
    cosine_similarity: float
    match_tier: AtsMatchTier
    recommendation: str
    technical_score: float
    experience_score: float
    education_score: float
    project_score: float
    seniority_fit: str
    overall_score: float
    skill_gaps: list[dict]
    matched_skills: list[dict]
    skill_gap_details: list[dict]
    section_scores: dict
    explainable_summary: str
    created_at: datetime
