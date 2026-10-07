from __future__ import annotations

import structlog
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import QuotaExceededException
from app.models.ai_governance import AIUsageLog, HardLimitAction, ModelTier, OrganizationBudget
from app.schemas.ai_governance import ModelPricingRate

log = structlog.get_logger(__name__)

# Standardized enterprise LLM cost matrix (USD per 1,000,000 tokens)
PRICING_RATES: dict[str, ModelPricingRate] = {
    ModelTier.fast.value: ModelPricingRate(
        tier=ModelTier.fast.value,
        recommended_model="gpt-4o-mini",
        prompt_per_1m_usd=0.15,
        completion_per_1m_usd=0.60,
        description="High-speed, cost-effective tier for extraction, quizzes, and formatting.",
    ),
    ModelTier.balanced.value: ModelPricingRate(
        tier=ModelTier.balanced.value,
        recommended_model="gpt-4o",
        prompt_per_1m_usd=2.50,
        completion_per_1m_usd=10.00,
        description="Balanced standard tier for interview question generation and turn evaluation.",
    ),
    ModelTier.reasoning.value: ModelPricingRate(
        tier=ModelTier.reasoning.value,
        recommended_model="gpt-4o",
        prompt_per_1m_usd=5.00,
        completion_per_1m_usd=15.00,
        description="Deep reasoning tier for complex system design, algorithm grading, and AI twin synthesis.",
    ),
}


def calculate_token_cost(tier: str, prompt_tokens: int, completion_tokens: int) -> float:
    rate = PRICING_RATES.get(tier, PRICING_RATES[ModelTier.balanced.value])
    prompt_cost = (prompt_tokens / 1_000_000.0) * rate.prompt_per_1m_usd
    completion_cost = (completion_tokens / 1_000_000.0) * rate.completion_per_1m_usd
    return round(prompt_cost + completion_cost, 6)


class AICostController:
    """Enterprise AI Cost Control & Model Tier Governor."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_or_create_budget(self, org_id: UUID) -> OrganizationBudget:
        result = await self.db.execute(
            select(OrganizationBudget).where(OrganizationBudget.org_id == org_id)
        )
        budget = result.scalar_one_or_none()
        if budget is None:
            budget = OrganizationBudget(
                org_id=org_id,
                monthly_budget_usd=500.0,
                current_spend_usd=0.0,
                alert_threshold_pct=0.80,
                hard_limit_action=HardLimitAction.degrade_to_cheap.value,
            )
            self.db.add(budget)
            await self.db.flush()
        return budget

    async def authorize_tier(self, org_id: UUID | None, requested_tier: str) -> str:
        """Enforces organization AI budget quotas.

        Downgrades to 'fast' tier if degraded, or raises QuotaExceededException if blocked.
        """
        if org_id is None:
            return requested_tier

        budget = await self.get_or_create_budget(org_id)
        utilization = budget.current_spend_usd / budget.monthly_budget_usd if budget.monthly_budget_usd > 0 else 0.0

        if utilization >= 1.0:
            if budget.hard_limit_action == HardLimitAction.block.value:
                log.error("ai_budget_quota_blocked", org_id=str(org_id), spend=budget.current_spend_usd, limit=budget.monthly_budget_usd)
                raise QuotaExceededException(
                    f"Monthly AI budget limit of ${budget.monthly_budget_usd:.2f} reached. Further reasoning calls are blocked."
                )
            else:
                log.warning("ai_budget_degraded_to_fast", org_id=str(org_id), requested_tier=requested_tier)
                return ModelTier.fast.value

        return requested_tier

    async def record_invocation(
        self,
        operation: str,
        model_name: str,
        model_tier: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        org_id: UUID | None = None,
        user_id: UUID | None = None,
        requisition_id: UUID | None = None,
    ) -> AIUsageLog:
        total_tokens = prompt_tokens + completion_tokens
        cost_usd = calculate_token_cost(model_tier, prompt_tokens, completion_tokens)

        entry = AIUsageLog(
            org_id=org_id,
            user_id=user_id,
            requisition_id=requisition_id,
            operation=operation,
            model_name=model_name,
            model_tier=model_tier,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=cost_usd,
            latency_ms=latency_ms,
        )
        self.db.add(entry)

        if org_id is not None:
            budget = await self.get_or_create_budget(org_id)
            budget.current_spend_usd += cost_usd
            budget.updated_at = datetime.now(UTC)
            self.db.add(budget)

        await self.db.flush()
        log.info(
            "ai_usage_logged",
            operation=operation,
            tier=model_tier,
            tokens=total_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            org_id=str(org_id) if org_id else None,
        )
        return entry

    async def get_usage_summary(
        self,
        org_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> dict[str, Any]:
        query = select(AIUsageLog)
        if org_id is not None:
            query = query.where(AIUsageLog.org_id == org_id)
        if user_id is not None:
            query = query.where(AIUsageLog.user_id == user_id)

        result = await self.db.execute(query)
        logs = list(result.scalars().all())

        total_calls = len(logs)
        total_prompt = sum(l.prompt_tokens for l in logs)
        total_comp = sum(l.completion_tokens for l in logs)
        total_tokens = sum(l.total_tokens for l in logs)
        total_cost = sum(l.estimated_cost_usd for l in logs)

        by_tier: dict[str, dict[str, float]] = {}
        for l in logs:
            if l.model_tier not in by_tier:
                by_tier[l.model_tier] = {"calls": 0, "tokens": 0, "cost_usd": 0.0}
            by_tier[l.model_tier]["calls"] += 1
            by_tier[l.model_tier]["tokens"] += l.total_tokens
            by_tier[l.model_tier]["cost_usd"] = round(by_tier[l.model_tier]["cost_usd"] + l.estimated_cost_usd, 6)

        by_operation: dict[str, dict[str, float]] = {}
        for l in logs:
            if l.operation not in by_operation:
                by_operation[l.operation] = {"calls": 0, "tokens": 0, "cost_usd": 0.0}
            by_operation[l.operation]["calls"] += 1
            by_operation[l.operation]["tokens"] += l.total_tokens
            by_operation[l.operation]["cost_usd"] = round(by_operation[l.operation]["cost_usd"] + l.estimated_cost_usd, 6)

        return {
            "total_calls": total_calls,
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_comp,
            "total_tokens": total_tokens,
            "total_estimated_cost_usd": round(total_cost, 6),
            "by_tier": by_tier,
            "by_operation": by_operation,
        }
