from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SessionStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    completed = "completed"
    error = "error"


class QuestionDifficulty(str, enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"
    expert = "expert"


class InterviewSession(Base):
    __tablename__ = "interview_sessions"
    __table_args__ = (
        CheckConstraint(
            "target_question_count BETWEEN 1 AND 50", name="ck_question_count"
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    org_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    resume_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True
    )
    jd_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("job_descriptions.id", ondelete="SET NULL"), nullable=True
    )
    ats_analysis_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ats_analyses.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="session_status"), nullable=False, default=SessionStatus.pending, index=True
    )
    current_topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    langgraph_thread_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    target_question_count: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    current_question_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_difficulty: Mapped[QuestionDifficulty] = mapped_column(
        Enum(QuestionDifficulty, name="question_difficulty"), nullable=False, default=QuestionDifficulty.medium
    )
    session_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    aggregate_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="sessions", lazy="noload")  # noqa: F821
    turns: Mapped[list["InterviewTurn"]] = relationship(back_populates="session", lazy="noload", order_by="InterviewTurn.turn_index")  # noqa: F821
    report: Mapped["SessionReport | None"] = relationship(back_populates="session", lazy="noload")  # noqa: F821
