"""004 phase1 foundation - organizations, audit_logs, tenant user link

Revision ID: 004
Revises: 003
Create Date: 2026-10-05
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── organizations ────────────────────────────────────────────────────────
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column(
            "tier",
            sa.Enum("free", "starter", "growth", "enterprise", name="organization_tier"),
            nullable=False,
            server_default="free",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)

    # ── update users with org_id ─────────────────────────────────────────────
    op.add_column("users", sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_users_organization_id",
        "users",
        "organizations",
        ["org_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_users_org_id", "users", ["org_id"])

    # ── audit_logs ───────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(100), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_foreign_key("fk_audit_logs_org_id", "audit_logs", "organizations", ["org_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_audit_logs_user_id", "audit_logs", "users", ["user_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_audit_logs_org_id", "audit_logs", ["org_id"])
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_constraint("fk_users_organization_id", "users", type_="foreignkey")
    op.drop_index("ix_users_org_id", table_name="users")
    op.drop_column("users", "org_id")
    op.drop_index("ix_organizations_slug", table_name="organizations")
    op.drop_table("organizations")
    op.execute("DROP TYPE IF EXISTS organization_tier")
