"""Initial schema with pgvector, all tables and HNSW indexes

Revision ID: 001
Revises:
Create Date: 2026-07-12 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 3072


def upgrade() -> None:
    # Extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')

    # Enums
    user_role = postgresql.ENUM("candidate", "recruiter", "admin", name="user_role")
    session_status = postgresql.ENUM("pending", "active", "completed", "error", name="session_status")
    question_difficulty = postgresql.ENUM("easy", "medium", "hard", "expert", name="question_difficulty")
    question_category = postgresql.ENUM(
        "behavioral", "technical", "system_design", "situational", "culture_fit", "domain_specific",
        name="question_category",
    )
    ats_match_tier = postgresql.ENUM("poor", "fair", "good", "excellent", name="ats_match_tier")

    user_role.create(op.get_bind(), checkfirst=True)
    session_status.create(op.get_bind(), checkfirst=True)
    question_difficulty.create(op.get_bind(), checkfirst=True)
    question_category.create(op.get_bind(), checkfirst=True)
    ats_match_tier.create(op.get_bind(), checkfirst=True)

    # users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("candidate", "recruiter", "admin", name="user_role"), nullable=False, server_default="candidate"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_users_email", "users", ["email"])

    # resumes
    op.create_table(
        "resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_name", sa.String(512), nullable=False),
        sa.Column("s3_key", sa.String(1024), nullable=False, unique=True),
        sa.Column("parsed_text", sa.Text, nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
        sa.Column("metadata", postgresql.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_resumes_user_id", "resumes", ["user_id"])
    op.execute(
        "CREATE INDEX idx_resumes_embedding_hnsw ON resumes USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)"
    )

    # job_descriptions
    op.create_table(
        "job_descriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("company", sa.String(255), nullable=True),
        sa.Column("raw_text", sa.Text, nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
        sa.Column("structured_skills", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.execute(
        "CREATE INDEX idx_jd_embedding_hnsw ON job_descriptions USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)"
    )

    # ats_analyses
    op.create_table(
        "ats_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("jd_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cosine_similarity", sa.Float, nullable=False),
        sa.Column("match_tier", sa.Enum("poor", "fair", "good", "excellent", name="ats_match_tier"), nullable=False),
        sa.Column("skill_gaps", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("matched_skills", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("section_scores", postgresql.JSON, nullable=False, server_default="{}"),
        sa.Column("overall_score", sa.Float, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("resume_id", "jd_id", name="uq_ats_resume_jd"),
        sa.CheckConstraint("cosine_similarity BETWEEN 0.0 AND 1.0", name="ck_cosine_range"),
        sa.CheckConstraint("overall_score BETWEEN 0.0 AND 100.0", name="ck_overall_range"),
    )
    op.create_index("idx_ats_resume_jd", "ats_analyses", ["resume_id", "jd_id"])

    # interview_sessions
    op.create_table(
        "interview_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("jd_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_descriptions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("ats_analysis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ats_analyses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.Enum("pending", "active", "completed", "error", name="session_status"), nullable=False, server_default="pending"),
        sa.Column("langgraph_thread_id", sa.String(255), nullable=True, unique=True),
        sa.Column("target_question_count", sa.Integer, nullable=False, server_default="10"),
        sa.Column("current_question_index", sa.Integer, nullable=False, server_default="0"),
        sa.Column("current_difficulty", sa.Enum("easy", "medium", "hard", "expert", name="question_difficulty"), nullable=False, server_default="medium"),
        sa.Column("session_config", postgresql.JSON, nullable=False, server_default="{}"),
        sa.Column("aggregate_score", sa.Float, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("target_question_count BETWEEN 1 AND 50", name="ck_question_count"),
    )
    op.create_index("idx_sessions_user_id", "interview_sessions", ["user_id"])
    op.create_index("idx_sessions_status", "interview_sessions", ["status"])
    op.create_index("idx_sessions_thread", "interview_sessions", ["langgraph_thread_id"])

    # interview_turns
    op.create_table(
        "interview_turns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("turn_index", sa.Integer, nullable=False),
        sa.Column("question_text", sa.Text, nullable=False),
        sa.Column("question_category", sa.Enum("behavioral", "technical", "system_design", "situational", "culture_fit", "domain_specific", name="question_category"), nullable=False),
        sa.Column("question_difficulty", sa.String(20), nullable=False),
        sa.Column("question_rationale", sa.Text, nullable=True),
        sa.Column("raw_transcript", sa.Text, nullable=True),
        sa.Column("corrected_transcript", sa.Text, nullable=True),
        sa.Column("audio_metrics", postgresql.JSON, nullable=True),
        sa.Column("eval_scores", postgresql.JSON, nullable=True),
        sa.Column("eval_feedback", sa.Text, nullable=True),
        sa.Column("eval_model", sa.String(100), nullable=True),
        sa.Column("answer_embedding", Vector(EMBEDDING_DIM), nullable=True),
        sa.Column("s3_audio_key", sa.String(1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("session_id", "turn_index", name="uq_turn_session_index"),
    )
    op.create_index("idx_turns_session_id", "interview_turns", ["session_id"])
    op.execute(
        "CREATE INDEX idx_turns_answer_embedding_hnsw ON interview_turns USING hnsw (answer_embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)"
    )

    # session_reports
    op.create_table(
        "session_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("overall_audio_metrics", postgresql.JSON, nullable=False, server_default="{}"),
        sa.Column("category_scores", postgresql.JSON, nullable=False, server_default="{}"),
        sa.Column("difficulty_progression", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("skill_coverage_delta", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("strengths", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("improvement_areas", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("recommended_resources", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("final_score", sa.Float, nullable=False),
        sa.Column("percentile_rank", sa.Float, nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("final_score BETWEEN 0.0 AND 100.0", name="ck_final_score"),
    )
    op.create_index("idx_reports_session_id", "session_reports", ["session_id"])
    op.create_index("idx_reports_user_id", "session_reports", ["user_id"])

    # updated_at trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER trg_users_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_users_updated_at ON users")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at")
    op.drop_table("session_reports")
    op.drop_table("interview_turns")
    op.drop_table("interview_sessions")
    op.drop_table("ats_analyses")
    op.drop_table("job_descriptions")
    op.drop_table("resumes")
    op.drop_table("users")
    for enum_name in ["user_role", "session_status", "question_difficulty", "question_category", "ats_match_tier"]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
