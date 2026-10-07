from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SpacedRepetitionCard(Base):
    """
    SuperMemo-2 (SM-2) Spaced Repetition flashcard item for interview mastery.
    Tracks repetitions, interval, easiness factor (EF), and review history.
    """
    __tablename__ = "spaced_repetition_cards"
    __table_args__ = (
        UniqueConstraint("user_id", "concept_key", name="uq_user_concept_card"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    concept_key: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    question_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    answer_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    key_takeaway: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    tier: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # SM-2 Core Parameters
    repetition_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    easiness_factor: Mapped[float] = mapped_column(Float, nullable=False, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    retention_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    last_quality: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Timestamps & Scheduling
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_review_due: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), index=True
    )
    review_history: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
