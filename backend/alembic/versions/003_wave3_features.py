"""003 wave3 features - job_applications table

Revision ID: 003
Revises: 002
Create Date: 2026-09-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("role_title", sa.String(512), nullable=False),
        sa.Column("job_url", sa.String(2048), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="wishlist"),
        sa.Column("salary_min", sa.Integer, nullable=True),
        sa.Column("salary_max", sa.Integer, nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("is_remote", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("contact_name", sa.String(255), nullable=True),
        sa.Column("contact_email", sa.String(320), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("timeline", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("tags", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column("priority", sa.Integer, nullable=False, server_default="2"),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("follow_up_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_job_applications_user_id", "job_applications", ["user_id"])
    op.create_index("ix_job_applications_status", "job_applications", ["status"])


def downgrade() -> None:
    op.drop_table("job_applications")
