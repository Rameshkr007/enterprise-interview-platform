from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, func
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String

from app.database import Base


class SessionReport(Base):
    __tablename__ = "session_reports"
    __table_args__ = (
        CheckConstraint("final_score BETWEEN 0.0 AND 100.0", name="ck_final_score"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    overall_audio_metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    category_scores: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    difficulty_progression: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    skill_coverage_delta: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    strengths: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    improvement_areas: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    recommended_resources: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    final_score: Mapped[float] = mapped_column(Float, nullable=False)
    percentile_rank: Mapped[float | None] = mapped_column(Float, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    session: Mapped["InterviewSession"] = relationship(back_populates="report", lazy="noload")  # noqa: F821
