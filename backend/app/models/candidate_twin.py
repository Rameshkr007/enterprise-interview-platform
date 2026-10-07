from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.vector_type import CompatibleVector


class CandidateTwin(Base):
    __tablename__ = "candidate_twins"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    overall_readiness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    technical_mastery: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    communication_metrics: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    system_design_mastery: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    coding_mastery: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    behavioral_mastery: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    weak_areas: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    strong_areas: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    historical_trajectory: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    growth_velocity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    talent_embedding: Mapped[list[float]] = mapped_column(
        CompatibleVector(dimensions=3072), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
