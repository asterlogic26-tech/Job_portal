"""Add auto-apply fields to applications table

Revision ID: 004
Revises: 003
Create Date: 2026-03-18 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create auth_users if missing (old conflicting migration 003 may have skipped it)
    op.execute("""
        CREATE TABLE IF NOT EXISTS auth_users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_auth_users_email ON auth_users (email)")

    # New columns on applications (skip if already exist)
    op.execute("ALTER TABLE applications ADD COLUMN IF NOT EXISTS is_auto_applied BOOLEAN NOT NULL DEFAULT false")
    op.execute("ALTER TABLE applications ADD COLUMN IF NOT EXISTS apply_method VARCHAR(50)")
    op.execute("ALTER TABLE applications ADD COLUMN IF NOT EXISTS blocked_reason TEXT")
    op.execute("ALTER TABLE applications ADD COLUMN IF NOT EXISTS direct_apply_url TEXT NOT NULL DEFAULT ''")
    op.execute("ALTER TABLE applications ADD COLUMN IF NOT EXISTS timeline JSONB NOT NULL DEFAULT '[]'")

    # Indexes — IF NOT EXISTS avoids transaction-aborting duplicates
    op.execute("CREATE INDEX IF NOT EXISTS ix_applications_is_auto_applied ON applications (is_auto_applied)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_applications_status ON applications (status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_applications_user_id ON applications (user_id)")

    # action_url on manual_tasks
    op.execute("ALTER TABLE manual_tasks ADD COLUMN IF NOT EXISTS action_url TEXT DEFAULT ''")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_applications_status")
    op.execute("DROP INDEX IF EXISTS ix_applications_is_auto_applied")
    op.execute("DROP INDEX IF EXISTS ix_applications_user_id")
    op.drop_column("applications", "timeline")
    op.drop_column("applications", "direct_apply_url")
    op.drop_column("applications", "blocked_reason")
    op.drop_column("applications", "apply_method")
    op.drop_column("applications", "is_auto_applied")
