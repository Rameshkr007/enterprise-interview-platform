from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RequisitionStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    paused = "paused"
    closed = "closed"


class CandidateStage(str, enum.Enum):
    invited = "invited"
    in_progress = "in_progress"
    interviewed = "interviewed"
    review_required = "review_required"
    offer = "offer"
    rejected = "rejected"


class RecruiterRequisition(Base):
    __tablename__ = "recruiter_requisitions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_by: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    department: Mapped[str] = mapped_column(String(255), nullable=False, default="Engineering")
    seniority_level: Mapped[str] = mapped_column(String(50), nullable=False, default="senior")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    required_skills: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    rubric_weights: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: {
            "technical": 0.30,
            "system_design": 0.25,
            "coding": 0.25,
            "behavioral": 0.20,
        },
    )
    hiring_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=75.0)
    status: Mapped[RequisitionStatus] = mapped_column(
        String(20), nullable=False, default=RequisitionStatus.active.value
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

    candidates: Mapped[list["RequisitionCandidate"]] = relationship(
        back_populates="requisition", cascade="all, delete-orphan", lazy="noload"
    )


class RequisitionCandidate(Base):
    __tablename__ = "requisition_candidates"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    requisition_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("recruiter_requisitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[CandidateStage] = mapped_column(
        String(30), nullable=False, default=CandidateStage.invited.value
    )
    stage_evaluations: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    composite_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    hiring_recommendation: Mapped[str | None] = mapped_column(String(50), nullable=True)
    evidence_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    recruiter_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    invited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    requisition: Mapped["RecruiterRequisition"] = relationship(
        back_populates="candidates", lazy="noload"
    )
