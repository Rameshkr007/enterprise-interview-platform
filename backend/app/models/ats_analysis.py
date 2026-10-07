from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Enum, Float, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSON, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AtsMatchTier(str, enum.Enum):
    poor = "poor"
    fair = "fair"
    good = "good"
    excellent = "excellent"


class AtsRecommendation(str, enum.Enum):
    apply = "APPLY"
    improve_then_apply = "IMPROVE_THEN_APPLY"
    low_priority = "LOW_PRIORITY"


class AtsAnalysis(Base):
    __tablename__ = "ats_analyses"
    __table_args__ = (
        UniqueConstraint("resume_id", "jd_id", name="uq_ats_resume_jd"),
        CheckConstraint("cosine_similarity BETWEEN 0.0 AND 1.0", name="ck_cosine_range"),
        CheckConstraint("overall_score BETWEEN 0.0 AND 100.0", name="ck_overall_range"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    resume_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    jd_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("job_descriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cosine_similarity: Mapped[float] = mapped_column(Float, nullable=False)
    match_tier: Mapped[AtsMatchTier] = mapped_column(
        Enum(AtsMatchTier, name="ats_match_tier"), nullable=False
    )
    recommendation: Mapped[str] = mapped_column(String(50), nullable=False, default="APPLY")
    technical_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    experience_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    education_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    project_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    seniority_fit: Mapped[str] = mapped_column(String(50), nullable=False, default="matching")
    skill_gaps: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    matched_skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    skill_gap_details: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    section_scores: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    explainable_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    resume: Mapped["Resume"] = relationship(back_populates="ats_analyses", lazy="noload")  # noqa: F821
    job_description: Mapped["JobDescription"] = relationship(back_populates="ats_analyses", lazy="noload")  # noqa: F821
