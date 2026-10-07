from __future__ import annotations

import enum
import random
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy import DateTime, Float, Integer, String, Text, func, select
from sqlalchemy.dialects.postgresql import JSON, UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.interview_session import InterviewSession

log = structlog.get_logger(__name__)


class ChallengeLanguage(str, enum.Enum):
    python = "python"
    javascript = "javascript"
    typescript = "typescript"
    java = "java"
    cpp = "cpp"
    go = "go"
    sql = "sql"


class ChallengeDifficulty(str, enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class CodingChallenge(Base):
    __tablename__ = "coding_challenges"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    language: Mapped[str] = mapped_column(String(30), nullable=False, default="python")
    starter_code: Mapped[str] = mapped_column(Text, nullable=False, default="")
    solution_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    test_cases: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    constraints: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    hints: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    time_limit_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    submission_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    submission_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ai_feedback: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


# ─── Leaderboard Model ────────────────────────────────────────────────────────
class LeaderboardEntry(Base):
    __tablename__ = "leaderboard"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    user_name: Mapped[str] = mapped_column(String(255), nullable=False)
    session_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    final_score: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="general")
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    percentile: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


# ─── Progress Tracker Model ───────────────────────────────────────────────────
class ProgressTracker(Base):
    __tablename__ = "progress_tracker"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, unique=True, index=True)
    total_sessions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_questions_answered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    best_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    streak_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skill_heatmap: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    score_history: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    badges_earned: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    weak_categories: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    strong_categories: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    last_session_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


# ─── Notification Model ───────────────────────────────────────────────────────
class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(nullable=False, default=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
