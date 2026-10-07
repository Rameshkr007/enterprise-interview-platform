from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, RequireRole
from app.core.exceptions import BadRequestException, NotFoundException
from app.database import get_db
from app.models.ai_governance import HardLimitAction, ModelTier
from app.models.user import UserRole
from app.schemas.ai_governance import (
    AIUsageSummaryResponse,
    BudgetStatusResponse,
    BudgetUpdateRequest,
    PricingMatrixResponse,
)
from app.services.ai_cost_controller import AICostController, PRICING_RATES
from app.services.audit_service import record_audit_event

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/ai-governance", tags=["AI Governance & Cost Control"])


@router.get("/pricing", response_model=PricingMatrixResponse)
async def get_model_pricing() -> PricingMatrixResponse:
    """Returns the platform's multi-tier LLM pricing matrix and model recommendations."""
    return PricingMatrixResponse(pricing=list(PRICING_RATES.values()))


@router.get("/usage/my", response_model=AIUsageSummaryResponse)
async def get_my_ai_usage(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AIUsageSummaryResponse:
    """Returns cumulative AI token consumption and cost incurred by the authenticated user."""
    controller = AICostController(db)
    data = await controller.get_usage_summary(user_id=current_user.id)
    return AIUsageSummaryResponse(**data)


@router.get(
    "/usage/org",
    response_model=AIUsageSummaryResponse,
    dependencies=[Depends(RequireRole([UserRole.recruiter, UserRole.org_admin, UserRole.platform_admin, UserRole.admin]))],
)
async def get_org_ai_usage(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AIUsageSummaryResponse:
    """Returns cumulative AI token consumption and cost for the user's organization."""
    if not current_user.org_id:
        raise BadRequestException("User does not belong to an organization")

    controller = AICostController(db)
    data = await controller.get_usage_summary(org_id=current_user.org_id)
    return AIUsageSummaryResponse(**data)


@router.get(
    "/budget",
    response_model=BudgetStatusResponse,
    dependencies=[Depends(RequireRole([UserRole.recruiter, UserRole.org_admin, UserRole.platform_admin, UserRole.admin]))],
)
async def get_org_budget(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BudgetStatusResponse:
    """Retrieves current AI budget utilization and alert thresholds."""
    if not current_user.org_id:
        raise BadRequestException("User does not belong to an organization")

    controller = AICostController(db)
    b = await controller.get_or_create_budget(current_user.org_id)

    util_pct = round(b.current_spend_usd / b.monthly_budget_usd * 100.0, 2) if b.monthly_budget_usd > 0 else 0.0
    alert_trig = (util_pct / 100.0) >= b.alert_threshold_pct
    hard_trig = (util_pct / 100.0) >= 1.0
    remaining = max(round(b.monthly_budget_usd - b.current_spend_usd, 4), 0.0)

    return BudgetStatusResponse(
        id=b.id,
        org_id=b.org_id,
        monthly_budget_usd=b.monthly_budget_usd,
        current_spend_usd=round(b.current_spend_usd, 4),
        remaining_budget_usd=remaining,
        utilization_pct=util_pct,
        is_alert_triggered=alert_trig,
        is_hard_limit_reached=hard_trig,
        hard_limit_action=b.hard_limit_action,
        billing_cycle_start=b.billing_cycle_start,
        updated_at=b.updated_at,
    )


@router.post(
    "/budget",
    response_model=BudgetStatusResponse,
    dependencies=[Depends(RequireRole([UserRole.org_admin, UserRole.platform_admin, UserRole.admin]))],
)
async def update_org_budget(
    body: BudgetUpdateRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BudgetStatusResponse:
    """Configures organization monthly AI spending quota and threshold behavior."""
    if not current_user.org_id:
        raise BadRequestException("User does not belong to an organization")

    controller = AICostController(db)
    b = await controller.get_or_create_budget(current_user.org_id)
    b.monthly_budget_usd = body.monthly_budget_usd
    b.alert_threshold_pct = body.alert_threshold_pct
    b.hard_limit_action = body.hard_limit_action.value
    db.add(b)
    await db.flush()

    await record_audit_event(
        db=db,
        action="ai_budget.updated",
        entity_type="organization_budget",
        org_id=current_user.org_id,
        user_id=current_user.id,
        entity_id=str(b.id),
        payload={"monthly_budget_usd": body.monthly_budget_usd, "action": body.hard_limit_action.value},
    )
    await db.refresh(b)

    util_pct = round(b.current_spend_usd / b.monthly_budget_usd * 100.0, 2) if b.monthly_budget_usd > 0 else 0.0
    alert_trig = (util_pct / 100.0) >= b.alert_threshold_pct
    hard_trig = (util_pct / 100.0) >= 1.0
    remaining = max(round(b.monthly_budget_usd - b.current_spend_usd, 4), 0.0)

    return BudgetStatusResponse(
        id=b.id,
        org_id=b.org_id,
        monthly_budget_usd=b.monthly_budget_usd,
        current_spend_usd=round(b.current_spend_usd, 4),
        remaining_budget_usd=remaining,
        utilization_pct=util_pct,
        is_alert_triggered=alert_trig,
        is_hard_limit_reached=hard_trig,
        hard_limit_action=b.hard_limit_action,
        billing_cycle_start=b.billing_cycle_start,
        updated_at=b.updated_at,
    )
