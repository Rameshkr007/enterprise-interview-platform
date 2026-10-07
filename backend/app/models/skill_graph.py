from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SkillRelationType(str, enum.Enum):
    prerequisite = "prerequisite"
    specialization = "specialization"
    complementary = "complementary"
    equivalent = "equivalent"


class CandidateSkillMastery(Base):
    """Tracks a candidate's verified or transitively inferred mastery score for each skill node."""
    __tablename__ = "candidate_skill_masteries"
    __table_args__ = (
        UniqueConstraint("user_id", "skill_id", name="uq_user_skill_mastery"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    mastery_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    is_inferred: Mapped[bool] = mapped_column(default=False)
    verified_via: Mapped[str] = mapped_column(String(50), nullable=False, default="assessment")
    assessment_history: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    last_assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
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


class CustomSkillNode(Base):
    """Enterprise/organization-defined custom skill nodes added to the universal DAG taxonomy."""
    __tablename__ = "custom_skill_nodes"
    __table_args__ = (
        UniqueConstraint("org_id", "slug", name="uq_org_skill_slug"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    tier: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    prerequisites: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    complements: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
