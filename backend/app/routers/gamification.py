from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.database import get_db
from app.services.company_service import CompanyInterviewService, COMPANY_PROFILES
from app.services.gamification_service import GamificationService, ACHIEVEMENTS, LEVEL_THRESHOLDS
from app.services.llm_service import LLMService

router = APIRouter(prefix="/game", tags=["Gamification & Company Mode"])


class CultureFitRequest(BaseModel):
    company: str
    question: str
    answer: str


class CompanyQuestionRequest(BaseModel):
    company: str
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    focus_area: str = "behavioral"
    skill_gaps: list[dict] = Field(default_factory=list)


# ── Company Interview ─────────────────────────────────────────────────────────
@router.get("/companies")
async def list_companies() -> list[dict]:
    """List all supported company interview modes."""
    svc = CompanyInterviewService(LLMService())
    return svc.list_companies()


@router.get("/company/{company_key}")
async def get_company_profile(company_key: str) -> dict[str, Any]:
    """Get full company interview profile with culture signals."""
    svc = CompanyInterviewService(LLMService())
    profile = svc.get_company_profile(company_key)
    return {
        "key": company_key,
        **profile,
    }


@router.post("/company/question")
async def generate_company_question(
    body: CompanyQuestionRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Generate a hyper-realistic company-specific interview question."""
    svc = CompanyInterviewService(LLMService())
    return await svc.generate_company_question(
        company_key=body.company,
        difficulty=body.difficulty,
        focus_area=body.focus_area,
        skill_gaps=body.skill_gaps,
    )


@router.post("/company/culture-fit")
async def score_culture_fit(
    body: CultureFitRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Score candidate's answer against company's leadership principles."""
    svc = CompanyInterviewService(LLMService())
    return await svc.score_culture_fit(
        company_key=body.company,
        question=body.question,
        answer=body.answer,
    )


# ── Gamification ──────────────────────────────────────────────────────────────
@router.get("/xp/level/{total_xp}")
async def get_level_info(total_xp: int) -> dict[str, Any]:
    """Compute level, title, emoji, and progress from total XP."""
    svc = GamificationService(None)  # type: ignore[arg-type]
    return svc.compute_level(total_xp)


@router.get("/achievements")
async def list_achievements(current_user: CurrentUser) -> list[dict]:
    """List all achievements with unlock status."""
    return [
        {
            "id": a["id"],
            "name": a["name"],
            "icon": a["icon"],
            "description": a["desc"],
            "xp_reward": a["xp"],
        }
        for a in ACHIEVEMENTS
    ]


@router.get("/daily-challenge")
async def get_daily_challenge(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Get today's daily challenge question configuration."""
    svc = GamificationService(db)
    return await svc.get_daily_challenge(current_user.id)


@router.get("/review-queue")
async def get_review_queue(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """SM-2 spaced repetition: get questions due for practice today."""
    svc = GamificationService(db)
    queue = await svc.get_review_queue(current_user.id)
    return {
        "due_count": len(queue),
        "review_items": queue,
        "estimated_minutes": len(queue) * 3,
    }


@router.get("/levels")
async def get_level_table() -> list[dict]:
    """Return the full level progression table."""
    return [
        {"level": i + 1, "title": title, "emoji": emoji, "xp_required": threshold}
        for i, (threshold, title, emoji) in enumerate(LEVEL_THRESHOLDS)
    ]
