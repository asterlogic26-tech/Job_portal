"""Add auto-apply fields to applications table

Revision ID: 003
Revises: 002
Create Date: 2026-03-18 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # New columns on applications
    op.add_column("applications", sa.Column("is_auto_applied", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("applications", sa.Column("apply_method", sa.String(50), nullable=True))
    op.add_column("applications", sa.Column("blocked_reason", sa.Text(), nullable=True))
    op.add_column("applications", sa.Column("direct_apply_url", sa.Text(), server_default="", nullable=False))
    op.add_column("applications", sa.Column("timeline", postgresql.JSONB(), server_default="[]", nullable=False))

    # Indexes for common filter queries
    op.create_index("ix_applications_is_auto_applied", "applications", ["is_auto_applied"])
    op.create_index("ix_applications_status", "applications", ["status"])
    op.create_index("ix_applications_user_id", "applications", ["user_id"])

    # Add new statuses to notifications (no schema change needed — status is free-form text)
    # Ensure ManualTask has action_url column (in case it doesn't)
    try:
        op.add_column("manual_tasks", sa.Column("action_url", sa.Text(), server_default="", nullable=True))
    except Exception:
        pass  # already exists


def downgrade() -> None:
    op.drop_index("ix_applications_status", "applications")
    op.drop_index("ix_applications_is_auto_applied", "applications")
    op.drop_index("ix_applications_user_id", "applications")
    op.drop_column("applications", "timeline")
    op.drop_column("applications", "direct_apply_url")
    op.drop_column("applications", "blocked_reason")
    op.drop_column("applications", "apply_method")
    op.drop_column("applications", "is_auto_applied")
