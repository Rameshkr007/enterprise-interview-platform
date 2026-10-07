from __future__ import annotations

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class CandidateTwinResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID
    overall_readiness_score: float
    technical_mastery: dict
    communication_metrics: dict
    system_design_mastery: dict
    coding_mastery: dict
    behavioral_mastery: dict
    weak_areas: list[dict]
    strong_areas: list[dict]
    historical_trajectory: list[dict]
    growth_velocity: float
    updated_at: datetime


class ExplainScoreResponse(BaseModel):
    dimension: str
    assigned_score: float
    what_was_evaluated: str
    evidence_found: list[str]
    score_rationale: str
    what_is_missing: list[str]
    actionable_improvement_roadmap: list[str]
    weights_breakdown: dict[str, float] = Field(default_factory=dict)
    calibration_sample_size: dict[str, int] = Field(default_factory=dict)
    projected_score_uplift: float = Field(default=0.0)


class TwinHistoryEventResponse(BaseModel):
    event_type: str  # "interview_session" | "coding_submission" | "sm2_retention" | "plan_completed"
    event_id: str
    title: str
    score: float
    delta: float
    timestamp: str
    metadata: dict = Field(default_factory=dict)


class CohortPercentile(BaseModel):
    metric: str
    candidate_score: float
    percentile_rank: float  # 0 to 100
    cohort_mean: float
    cohort_top_quartile: float


class TwinBenchmarkResponse(BaseModel):
    user_id: UUID
    overall_percentile: float
    cohort_name: str
    metrics: list[CohortPercentile]
    growth_velocity_status: str  # "accelerating" | "steady" | "plateauing" | "regressing"
    generated_at: str
