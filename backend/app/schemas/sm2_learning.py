from __future__ import annotations

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class SpacedCardResponse(BaseModel):
    id: UUID
    user_id: UUID
    skill_id: str
    concept_key: str
    title: str
    question_prompt: str
    answer_explanation: str
    key_takeaway: str
    category: str
    tier: int
    repetition_count: int
    easiness_factor: float
    interval_days: int
    retention_score: float
    last_quality: int | None
    last_reviewed_at: datetime | None
    next_review_due: datetime

    class Config:
        from_attributes = True


class SM2ReviewSubmitRequest(BaseModel):
    card_id: UUID
    quality: int = Field(
        ...,
        ge=0,
        le=5,
        description="Rating from 0 (Blackout) to 5 (Perfect instant recall)",
    )


class SM2ReviewResultResponse(BaseModel):
    card_id: str
    concept_key: str
    title: str
    quality: int
    repetition_count: int
    interval_days: int
    easiness_factor: float
    retention_score: float
    next_review_due: str
    mastery_boost_applied: float


class SM2DeckStatsResponse(BaseModel):
    total_cards: int
    due_today_count: int
    mature_cards_count: int
    young_cards_count: int
    new_cards_count: int
    average_retention_pct: float
    total_reviews_completed: int
    current_streak_days: int


class SM2SeedRequest(BaseModel):
    skill_ids: list[str] | None = None


class SM2SeedResponse(BaseModel):
    cards_seeded: int
    message: str
