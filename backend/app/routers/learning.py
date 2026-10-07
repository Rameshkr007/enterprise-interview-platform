from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.core.exceptions import NotFoundException
from app.database import get_db
from app.models.learning_plan import LearningPlan
from app.models.sm2_card import SpacedRepetitionCard
from app.schemas.learning import (
    DayCompleteRequest,
    LearningPlanResponse,
    PlanCreateRequest,
    ReassessmentResultResponse,
    ReassessmentSubmitRequest,
)
from app.schemas.sm2_learning import (
    SM2DeckStatsResponse,
    SM2ReviewResultResponse,
    SM2ReviewSubmitRequest,
    SM2SeedRequest,
    SM2SeedResponse,
    SpacedCardResponse,
)
from app.services.audit_service import record_audit_event
from app.services.candidate_twin_service import CandidateTwinEngine
from app.services.learning_engine import PersonalizedLearningEngine
from app.services.sm2_learning_service import SM2LearningService

router = APIRouter(prefix="/learning", tags=["Personalized Learning Engine"])

_learning_engine = PersonalizedLearningEngine()
_twin_engine = CandidateTwinEngine()
_sm2_service = SM2LearningService()



@router.post("/plans/generate", response_model=LearningPlanResponse, status_code=status.HTTP_201_CREATED)
async def generate_learning_plan(
    body: PlanCreateRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LearningPlan:
    """
    Feature 12: Generates a 7-day day-by-day milestone learning plan
    connected to a detected weakness or skill gap.
    """
    plan = await _learning_engine.create_plan_for_gap(
        db=db,
        user_id=current_user.id,
        gap_name=body.gap_name,
        source_session_id=body.source_session_id,
        category=body.category,
        target_days=body.target_days,
    )

    await record_audit_event(
        db=db,
        action="learning.plan_generated",
        entity_type="learning_plan",
        entity_id=str(plan.id),
        user_id=current_user.id,
        payload={"gap": body.gap_name, "category": body.category},
    )

    return plan



@router.get("/plans/my", response_model=list[LearningPlanResponse])
async def get_my_learning_plans(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[LearningPlan]:
    """
    Retrieves all learning plans for the logged-in candidate.
    """
    return await _learning_engine.get_user_plans(db=db, user_id=current_user.id)


@router.get("/plans/{plan_id}", response_model=LearningPlanResponse)
async def get_learning_plan(
    plan_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LearningPlan:
    """
    Retrieves detailed breakdown of a specific learning plan.
    """
    plan = await db.get(LearningPlan, plan_id)
    if plan is None or plan.user_id != current_user.id:
        raise NotFoundException("Learning plan not found")
    return plan


@router.post("/plans/{plan_id}/complete-day", response_model=LearningPlanResponse)
async def complete_daily_milestone(
    plan_id: UUID,
    body: DayCompleteRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LearningPlan:
    """
    Marks a daily milestone as completed and advances plan progress.
    """
    plan = await _learning_engine.complete_day_milestone(
        db=db,
        plan_id=plan_id,
        day_number=body.day_number,
        user_id=current_user.id,
    )

    await record_audit_event(
        db=db,
        action="learning.day_completed",
        entity_type="learning_plan",
        entity_id=str(plan.id),
        user_id=current_user.id,
        payload={"day_number": body.day_number},
    )

    return plan


@router.post("/plans/{plan_id}/milestone/{day}", response_model=LearningPlanResponse)
async def complete_milestone_by_day(
    plan_id: UUID,
    day: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LearningPlan:
    """
    Direct milestone day completion route.
    """
    plan = await _learning_engine.complete_day_milestone(
        db=db,
        plan_id=plan_id,
        day_number=day,
        user_id=current_user.id,
    )

    await record_audit_event(
        db=db,
        action="learning.day_completed",
        entity_type="learning_plan",
        entity_id=str(plan.id),
        user_id=current_user.id,
        payload={"day_number": day},
    )

    return plan


@router.post("/plans/{plan_id}/reassess", response_model=ReassessmentResultResponse)
async def submit_plan_reassessment(
    plan_id: UUID,
    body: ReassessmentSubmitRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Submits answers to the 5-question mastery quiz to resolve the detected weakness.
    If score >= 70%, marks gap as resolved and triggers Candidate AI Twin update.
    """
    result = await _learning_engine.submit_reassessment(
        db=db,
        plan_id=plan_id,
        answers=[a.model_dump() for a in body.answers],
        user_id=current_user.id,
    )

    # Sync candidate twin upon reassessment completion
    if result.get("passed"):
        await _twin_engine.sync_twin_from_history(db, current_user.id)
        await record_audit_event(
            db=db,
            action="learning.gap_resolved",
            entity_type="learning_plan",
            entity_id=str(plan_id),
            user_id=current_user.id,
            payload={"score": result.get("reassessment_score")},
        )

    return result


# ── SuperMemo-2 (SM-2) Spaced Repetition Routes ───────────────────────────────

@router.post("/sm2/seed", response_model=SM2SeedResponse)
async def seed_sm2_deck(
    body: SM2SeedRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SM2SeedResponse:
    """
    Seeds canonical flashcards linked to Skill DAG nodes for the logged-in candidate.
    """
    svc = SM2LearningService(db=db)
    seeded = await svc.seed_user_deck(user_id=current_user.id, skill_ids=body.skill_ids)
    return SM2SeedResponse(
        cards_seeded=len(seeded),
        message=f"Successfully seeded {len(seeded)} flashcards for candidate review queue.",
    )


@router.get("/sm2/cards/due", response_model=list[SpacedCardResponse])
async def get_sm2_due_cards(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 20,
) -> list[SpacedRepetitionCard]:
    """
    Retrieves the candidate's active daily review queue of due cards,
    ordered by overdue priority and DAG difficulty tier.
    """
    svc = SM2LearningService(db=db)
    # Auto-seed if user has 0 cards
    from sqlalchemy import func, select
    count_res = await db.execute(
        select(func.count(SpacedRepetitionCard.id)).where(SpacedRepetitionCard.user_id == current_user.id)
    )
    if (count_res.scalar_one() or 0) == 0:
        await svc.seed_user_deck(user_id=current_user.id)

    return await svc.get_due_cards(user_id=current_user.id, limit=limit)


@router.post("/sm2/cards/review", response_model=SM2ReviewResultResponse)
async def submit_sm2_review(
    body: SM2ReviewSubmitRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Processes candidate recall quality rating (0-5) using SuperMemo-2 algorithm,
    updates interval & easiness factor, and awards mastery points.
    """
    svc = SM2LearningService(db=db)
    result = await svc.submit_card_review(
        user_id=current_user.id,
        card_id=body.card_id,
        quality=body.quality,
    )
    return result


@router.get("/sm2/stats", response_model=SM2DeckStatsResponse)
async def get_sm2_deck_stats(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Retrieves overall memory retention stats, mature vs young card counts, and review streak.
    """
    svc = SM2LearningService(db=db)
    return await svc.get_deck_stats(user_id=current_user.id)


@router.get("/sm2/deck", response_model=list[SpacedCardResponse])
async def get_sm2_deck(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    tier: int | None = None,
    skill_id: str | None = None,
) -> list[SpacedRepetitionCard]:
    """
    Lists all cards in the candidate's personal collection with optional filtering.
    """
    from sqlalchemy import select
    query = select(SpacedRepetitionCard).where(SpacedRepetitionCard.user_id == current_user.id)
    if tier is not None:
        query = query.where(SpacedRepetitionCard.tier == tier)
    if skill_id:
        query = query.where(SpacedRepetitionCard.skill_id == skill_id)
    query = query.order_by(SpacedRepetitionCard.tier.asc(), SpacedRepetitionCard.concept_key.asc())

    res = await db.execute(query)
    return list(res.scalars().all())


@router.get("/sm2/cards/{card_id}", response_model=SpacedCardResponse)
async def get_sm2_card_detail(
    card_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SpacedRepetitionCard:
    """
    Retrieves detailed breakdown for a specific flashcard.
    """
    card = await db.get(SpacedRepetitionCard, card_id)
    if not card or card.user_id != current_user.id:
        raise NotFoundException("Flashcard not found")
    return card

