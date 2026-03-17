"""Add agent_logs table

Revision ID: 002
Revises: 001
Create Date: 2026-03-17 00:01:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("version", sa.String(20), nullable=False, server_default="1.0.0"),
        sa.Column("pipeline_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("input_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("output_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("success", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_agent_logs_agent_name", "agent_logs", ["agent_name"])
    op.create_index("ix_agent_logs_pipeline_run_id", "agent_logs", ["pipeline_run_id"])
    op.create_index("ix_agent_logs_job_id", "agent_logs", ["job_id"])
    op.create_index("ix_agent_logs_user_id", "agent_logs", ["user_id"])
    op.create_index("ix_agent_logs_created_at", "agent_logs", ["created_at"])
    op.create_index("ix_agent_logs_success", "agent_logs", ["success"])


def downgrade() -> None:
    op.drop_table("agent_logs")
