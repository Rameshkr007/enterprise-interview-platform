from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID, uuid4

from app.models.vector_type import CompatibleVector
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSON, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import get_settings
from app.database import Base

settings = get_settings()


class QuestionCategory(str, enum.Enum):
    behavioral = "behavioral"
    technical = "technical"
    system_design = "system_design"
    situational = "situational"
    culture_fit = "culture_fit"
    domain_specific = "domain_specific"


class InterviewTurn(Base):
    __tablename__ = "interview_turns"
    __table_args__ = (
        UniqueConstraint("session_id", "turn_index", name="uq_turn_session_index"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_category: Mapped[QuestionCategory] = mapped_column(
        Enum(QuestionCategory, name="question_category"), nullable=False
    )
    question_difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    question_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrected_transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    eval_scores: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    eval_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    eval_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    answer_embedding: Mapped[list[float] | None] = mapped_column(
        CompatibleVector(settings.OPENAI_EMBEDDING_DIMENSIONS), nullable=True
    )
    s3_audio_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    session: Mapped["InterviewSession"] = relationship(back_populates="turns", lazy="noload")  # noqa: F821
