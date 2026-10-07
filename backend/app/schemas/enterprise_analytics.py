from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class DomainMasterySummary(BaseModel):
    domain: str
    average_score: float
    candidate_count: int


class ReadinessDistribution(BaseModel):
    needs_work_count: int
    progressing_count: int
    interview_ready_count: int
    bar_raiser_count: int
    total_candidates: int


class EnterpriseOverviewResponse(BaseModel):
    total_candidates: int
    active_requisitions: int
    completed_interviews: int
    overall_readiness_avg: float
    readiness_distribution: ReadinessDistribution
    domain_breakdown: list[DomainMasterySummary]
    avg_velocity_score: float
    hiring_recommendation_rate: float


class FunnelStageMetric(BaseModel):
    stage: str
    count: int
    conversion_rate_pct: float


class RecruiterFunnelResponse(BaseModel):
    total_pipeline: int
    stages: list[FunnelStageMetric]
    avg_time_to_hire_days: float
    offer_acceptance_rate_pct: float


class SkillShortageItem(BaseModel):
    skill_name: str
    gap_count: int
    severity: str  # "high", "medium", "low"
    percentage_of_pool: float


class SkillShortageResponse(BaseModel):
    total_candidates_analyzed: int
    shortages: list[SkillShortageItem]


class LearningImpactResponse(BaseModel):
    total_plans_generated: int
    completed_plans: int
    in_progress_plans: int
    completion_rate_pct: float
    avg_pre_reassessment_score: float
    avg_post_reassessment_score: float
    avg_score_improvement_pct: float


class TalentSupplyDemandItem(BaseModel):
    skill_name: str
    candidate_supply_count: int
    requisition_demand_count: int
    supply_demand_ratio: float
    shortage_level: str  # "critical", "moderate", "balanced", "surplus"
    projected_time_to_fill_days: int


class TalentSupplyDemandResponse(BaseModel):
    total_skills_tracked: int
    critical_shortage_count: int
    skills: list[TalentSupplyDemandItem]


class EnterpriseRoiMetricsResponse(BaseModel):
    total_interviews_conducted: int
    recruiter_hours_saved: float
    cost_savings_usd: float
    ai_infrastructure_cost_usd: float
    net_roi_multiple: float
    avg_candidate_score_lift: float
    time_to_fill_reduction_pct: float
    department_metrics: dict[str, dict[str, Any]]
