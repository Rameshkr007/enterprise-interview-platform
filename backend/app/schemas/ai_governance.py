from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.ai_governance import HardLimitAction, ModelTier


class AIUsageLogResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    org_id: UUID | None
    user_id: UUID | None
    requisition_id: UUID | None
    operation: str
    model_name: str
    model_tier: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    latency_ms: float
    created_at: datetime


class AIUsageSummaryResponse(BaseModel):
    total_calls: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    total_estimated_cost_usd: float
    by_tier: dict[str, dict[str, float]]
    by_operation: dict[str, dict[str, float]]


class BudgetUpdateRequest(BaseModel):
    monthly_budget_usd: float = Field(..., gt=0.0, description="Monthly AI spending limit in USD")
    alert_threshold_pct: float = Field(default=0.80, ge=0.1, le=1.0, description="Fraction at which alert triggers")
    hard_limit_action: HardLimitAction = Field(
        default=HardLimitAction.degrade_to_cheap,
        description="Action when 100% budget reached (degrade_to_cheap or block)",
    )


class BudgetStatusResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    org_id: UUID
    monthly_budget_usd: float
    current_spend_usd: float
    remaining_budget_usd: float
    utilization_pct: float
    is_alert_triggered: bool
    is_hard_limit_reached: bool
    hard_limit_action: str
    billing_cycle_start: datetime
    updated_at: datetime


class ModelPricingRate(BaseModel):
    tier: str
    recommended_model: str
    prompt_per_1m_usd: float
    completion_per_1m_usd: float
    description: str


class PricingMatrixResponse(BaseModel):
    pricing: list[ModelPricingRate]
