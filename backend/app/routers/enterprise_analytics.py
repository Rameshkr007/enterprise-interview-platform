from __future__ import annotations

from typing import Annotated
import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, RequireRole
from app.database import get_db
from app.models.user import UserRole
from app.schemas.enterprise_analytics import (
    EnterpriseOverviewResponse,
    LearningImpactResponse,
    RecruiterFunnelResponse,
    SkillShortageResponse,
    TalentSupplyDemandResponse,
    EnterpriseRoiMetricsResponse,
)
from app.services.enterprise_analytics_service import EnterpriseAnalyticsService

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/analytics/enterprise", tags=["Enterprise Analytics"])


@router.get(
    "/overview",
    response_model=EnterpriseOverviewResponse,
    dependencies=[Depends(RequireRole([UserRole.recruiter, UserRole.org_admin, UserRole.platform_admin, UserRole.admin]))],
)
async def get_enterprise_overview(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EnterpriseOverviewResponse:
    """Returns organization-level talent readiness, domain mastery scores, and hiring velocity."""
    svc = EnterpriseAnalyticsService(db)
    return await svc.get_overview(org_id=current_user.org_id)


@router.get(
    "/recruiter-funnel",
    response_model=RecruiterFunnelResponse,
    dependencies=[Depends(RequireRole([UserRole.recruiter, UserRole.org_admin, UserRole.platform_admin, UserRole.admin]))],
)
async def get_recruiter_funnel(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecruiterFunnelResponse:
    """Returns candidate stage progression, conversion rates, and offer acceptance statistics."""
    svc = EnterpriseAnalyticsService(db)
    return await svc.get_recruiter_funnel(org_id=current_user.org_id)


@router.get(
    "/skill-shortages",
    response_model=SkillShortageResponse,
    dependencies=[Depends(RequireRole([UserRole.recruiter, UserRole.org_admin, UserRole.platform_admin, UserRole.admin]))],
)
async def get_skill_shortages(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SkillShortageResponse:
    """Identifies top talent skill shortages and gap frequencies across candidate evaluations."""
    svc = EnterpriseAnalyticsService(db)
    return await svc.get_skill_shortages(org_id=current_user.org_id)


@router.get(
    "/learning-impact",
    response_model=LearningImpactResponse,
    dependencies=[Depends(RequireRole([UserRole.recruiter, UserRole.org_admin, UserRole.platform_admin, UserRole.admin]))],
)
async def get_learning_impact(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LearningImpactResponse:
    """Measures skill gap resolution and score improvement resulting from AI learning plans."""
    svc = EnterpriseAnalyticsService(db)
    return await svc.get_learning_impact(org_id=current_user.org_id)


@router.get(
    "/supply-demand",
    response_model=TalentSupplyDemandResponse,
    dependencies=[Depends(RequireRole([UserRole.recruiter, UserRole.org_admin, UserRole.platform_admin, UserRole.admin]))],
)
async def get_talent_supply_demand(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TalentSupplyDemandResponse:
    """Computes live supply vs demand intelligence across candidate verified masteries and requisition skills."""
    svc = EnterpriseAnalyticsService(db)
    return await svc.get_supply_demand_intelligence(org_id=current_user.org_id)


@router.get(
    "/roi-metrics",
    response_model=EnterpriseRoiMetricsResponse,
    dependencies=[Depends(RequireRole([UserRole.recruiter, UserRole.org_admin, UserRole.platform_admin, UserRole.admin]))],
)
async def get_enterprise_roi_metrics(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EnterpriseRoiMetricsResponse:
    """Calculates executive ROI, recruiter time savings, and candidate score lift."""
    svc = EnterpriseAnalyticsService(db)
    return await svc.get_roi_metrics(org_id=current_user.org_id)

