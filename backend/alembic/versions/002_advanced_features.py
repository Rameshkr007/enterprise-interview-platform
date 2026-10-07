"""002 advanced features - coding challenges, leaderboard, progress tracker, notifications

Revision ID: 002
Revises: 001
Create Date: 2026-09-28
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── coding_challenges ────────────────────────────────────────────────────
    op.create_table(
        "coding_challenges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("language", sa.String(30), nullable=False, server_default="python"),
        sa.Column("starter_code", sa.Text, nullable=False, server_default=""),
        sa.Column("solution_code", sa.Text, nullable=True),
        sa.Column("test_cases", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("constraints", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("hints", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("time_limit_minutes", sa.Integer, nullable=False, server_default="30"),
        sa.Column("submission_code", sa.Text, nullable=True),
        sa.Column("submission_result", postgresql.JSON, nullable=True),
        sa.Column("ai_feedback", postgresql.JSON, nullable=True),
        sa.Column("score", sa.Float, nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_coding_challenges_session_id", "coding_challenges", ["session_id"])

    # ── leaderboard ──────────────────────────────────────────────────────────
    op.create_table(
        "leaderboard",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("user_name", sa.String(255), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("final_score", sa.Float, nullable=False),
        sa.Column("category", sa.String(100), nullable=False, server_default="general"),
        sa.Column("rank", sa.Integer, nullable=True),
        sa.Column("percentile", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── progress_tracker ─────────────────────────────────────────────────────
    op.create_table(
        "progress_tracker",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True, index=True),
        sa.Column("total_sessions", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_questions_answered", sa.Integer, nullable=False, server_default="0"),
        sa.Column("avg_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("best_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("streak_days", sa.Integer, nullable=False, server_default="0"),
        sa.Column("skill_heatmap", postgresql.JSON, nullable=False, server_default="{}"),
        sa.Column("score_history", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("badges_earned", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("weak_categories", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("strong_categories", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("last_session_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── notifications ─────────────────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("metadata", postgresql.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("progress_tracker")
    op.drop_table("leaderboard")
    op.drop_table("coding_challenges")
