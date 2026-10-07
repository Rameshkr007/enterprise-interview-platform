from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LearningPlanStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    paused = "paused"
    abandoned = "abandoned"


class LearningPlan(Base):
    __tablename__ = "learning_plans"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    detected_gap: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_session_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="technical")
    status: Mapped[LearningPlanStatus] = mapped_column(
        String(20), nullable=False, default=LearningPlanStatus.active.value
    )
    target_completion_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    current_day: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    daily_schedule: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    reassessment_quiz: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    reassessment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reassessment_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
