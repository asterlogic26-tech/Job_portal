"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-17 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Extensions ────────────────────────────────────────────────────────────
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gin")

    # ── user_profile ──────────────────────────────────────────────────────────
    op.create_table(
        "user_profile",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("current_title", sa.String(255), nullable=False, server_default=""),
        sa.Column(
            "target_titles",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("skills", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("experience_years", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("location", sa.String(255), nullable=False, server_default="Remote"),
        sa.Column(
            "remote_preference", sa.String(50), nullable=False, server_default="remote"
        ),
        sa.Column("target_salary_min", sa.Integer(), nullable=True),
        sa.Column("target_salary_max", sa.Integer(), nullable=True),
        sa.Column("linkedin_url", sa.Text(), nullable=False, server_default=""),
        sa.Column("github_url", sa.Text(), nullable=False, server_default=""),
        sa.Column("resume_url", sa.Text(), nullable=True),
        sa.Column("bio", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "preferences", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
        sa.Column("profile_embedding_id", sa.String(255), nullable=True),
        sa.Column("health_score", sa.Integer(), nullable=False, server_default="0"),
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

    # ── companies ─────────────────────────────────────────────────────────────
    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("normalized_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("domain", sa.String(255), nullable=False, server_default=""),
        sa.Column("website", sa.Text(), nullable=False, server_default=""),
        sa.Column("linkedin_url", sa.Text(), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("industry", sa.String(255), nullable=False, server_default=""),
        sa.Column("size_range", sa.String(50), nullable=False, server_default=""),
        sa.Column("stage", sa.String(50), nullable=False, server_default=""),
        sa.Column("founded_year", sa.Integer(), nullable=True),
        sa.Column("headquarters", sa.String(255), nullable=False, server_default=""),
        sa.Column(
            "hiring_score", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column(
            "job_velocity", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column(
            "is_watched", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("total_funding_usd", sa.Integer(), nullable=True),
        sa.Column(
            "last_funding_round", sa.String(100), nullable=False, server_default=""
        ),
        sa.Column("last_funding_amount_usd", sa.Integer(), nullable=True),
        sa.Column(
            "metadata", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
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
    op.create_index("ix_companies_name_trgm", "companies", ["name"], postgresql_using="gin",
                    postgresql_ops={"name": "gin_trgm_ops"})

    # ── company_signals ───────────────────────────────────────────────────────
    op.create_table(
        "company_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("signal_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(512), nullable=False, server_default=""),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("source_url", sa.Text(), nullable=False, server_default=""),
        sa.Column("amount_usd", sa.Integer(), nullable=True),
        sa.Column("signal_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "raw_data", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
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
    op.create_index("ix_company_signals_company_id", "company_signals", ["company_id"])
    op.create_index("ix_company_signals_type", "company_signals", ["signal_type"])

    # ── jobs ──────────────────────────────────────────────────────────────────
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("external_id", sa.String(512), nullable=False, unique=True),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("normalized_title", sa.String(512), nullable=False, server_default=""),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("description_html", sa.Text(), nullable=False, server_default=""),
        sa.Column("location", sa.String(255), nullable=False, server_default=""),
        sa.Column(
            "remote_policy", sa.String(50), nullable=False, server_default="unknown"
        ),
        sa.Column(
            "seniority_level", sa.String(50), nullable=False, server_default="unknown"
        ),
        sa.Column("salary_min", sa.Integer(), nullable=True),
        sa.Column("salary_max", sa.Integer(), nullable=True),
        sa.Column(
            "salary_currency", sa.String(10), nullable=False, server_default="USD"
        ),
        sa.Column(
            "required_skills", postgresql.JSONB(), nullable=False, server_default="[]"
        ),
        sa.Column(
            "preferred_skills", postgresql.JSONB(), nullable=False, server_default="[]"
        ),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("apply_url", sa.Text(), nullable=False, server_default=""),
        sa.Column("posted_at", sa.String(100), nullable=True),
        sa.Column(
            "raw_data", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
        sa.Column("embedding_id", sa.String(255), nullable=True),
        sa.Column(
            "is_hidden", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "is_saved", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "is_applied", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "is_duplicate", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "content_hash", sa.String(64), nullable=False, server_default=""
        ),
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
    op.create_index("ix_jobs_source", "jobs", ["source"])
    op.create_index("ix_jobs_company_id", "jobs", ["company_id"])
    op.create_index("ix_jobs_is_hidden", "jobs", ["is_hidden"])
    op.create_index("ix_jobs_is_saved", "jobs", ["is_saved"])
    op.create_index("ix_jobs_created_at", "jobs", ["created_at"])
    op.create_index(
        "ix_jobs_title_trgm", "jobs", ["title"],
        postgresql_using="gin", postgresql_ops={"title": "gin_trgm_ops"}
    )
    op.create_index(
        "ix_jobs_company_name_trgm", "jobs", ["company_name"],
        postgresql_using="gin", postgresql_ops={"company_name": "gin_trgm_ops"}
    )

    # ── job_matches ───────────────────────────────────────────────────────────
    op.create_table(
        "job_matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("total_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("skill_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column(
            "seniority_score", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column("salary_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("recency_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("culture_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column(
            "company_growth_score", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column(
            "interview_probability", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column(
            "matching_skills", postgresql.JSONB(), nullable=False, server_default="[]"
        ),
        sa.Column(
            "missing_skills", postgresql.JSONB(), nullable=False, server_default="[]"
        ),
        sa.Column(
            "score_breakdown", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
        sa.Column("user_rating", sa.Integer(), nullable=True),
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
    op.create_index("ix_job_matches_user_id", "job_matches", ["user_id"])
    op.create_index("ix_job_matches_total_score", "job_matches", ["total_score"])

    # ── applications ──────────────────────────────────────────────────────────
    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="saved"),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "last_activity_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("follow_up_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("resume_version_url", sa.Text(), nullable=False, server_default=""),
        sa.Column("cover_letter_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("interview_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("offer_amount", sa.Integer(), nullable=True),
        sa.Column(
            "custom_fields", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
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
    op.create_index("ix_applications_user_id", "applications", ["user_id"])
    op.create_index("ix_applications_status", "applications", ["status"])
    op.create_index("ix_applications_job_id", "applications", ["job_id"])

    # ── content ───────────────────────────────────────────────────────────────
    op.create_table(
        "content",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("title", sa.String(512), nullable=False, server_default=""),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column("subject", sa.String(512), nullable=False, server_default=""),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("prompt_used", sa.Text(), nullable=False, server_default=""),
        sa.Column("model_used", sa.String(100), nullable=False, server_default=""),
        sa.Column(
            "generation_metadata",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "is_approved", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("approved_at", sa.String(100), nullable=True),
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
    op.create_index("ix_content_user_id", "content", ["user_id"])
    op.create_index("ix_content_type", "content", ["content_type"])
    op.create_index("ix_content_status", "content", ["status"])

    # ── notifications ─────────────────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("notification_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "is_read", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "priority", sa.String(20), nullable=False, server_default="normal"
        ),
        sa.Column("action_url", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "metadata", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
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
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])

    # ── manual_tasks ──────────────────────────────────────────────────────────
    op.create_table(
        "manual_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("site_url", sa.Text(), nullable=False, server_default=""),
        sa.Column("instructions", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "context_data", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "completion_notes", sa.Text(), nullable=False, server_default=""
        ),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=True),
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
    op.create_index("ix_manual_tasks_user_id", "manual_tasks", ["user_id"])
    op.create_index("ix_manual_tasks_status", "manual_tasks", ["status"])

    # ── recruiter_contacts ────────────────────────────────────────────────────
    op.create_table(
        "recruiter_contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("title", sa.String(255), nullable=False, server_default=""),
        sa.Column("company_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("email", sa.String(255), nullable=False, server_default=""),
        sa.Column("linkedin_url", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "is_outreached", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "extra", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
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
    op.create_index("ix_recruiter_contacts_user_id", "recruiter_contacts", ["user_id"])

    # ── network_connections ───────────────────────────────────────────────────
    op.create_table(
        "network_connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("current_company", sa.String(255), nullable=False, server_default=""),
        sa.Column("title", sa.String(255), nullable=False, server_default=""),
        sa.Column("linkedin_url", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "relationship_strength", sa.Float(), nullable=False, server_default="0.5"
        ),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "can_refer", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "extra", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
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
    op.create_index(
        "ix_network_connections_user_id", "network_connections", ["user_id"]
    )

    # ── Seed single user row ──────────────────────────────────────────────────
    op.execute(
        """
        INSERT INTO user_profile (id, full_name, created_at, updated_at)
        VALUES (
            '00000000-0000-0000-0000-000000000001',
            'Job Seeker',
            now(),
            now()
        )
        ON CONFLICT (id) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_table("network_connections")
    op.drop_table("recruiter_contacts")
    op.drop_table("manual_tasks")
    op.drop_table("notifications")
    op.drop_table("content")
    op.drop_table("applications")
    op.drop_table("job_matches")
    op.drop_table("jobs")
    op.drop_table("company_signals")
    op.drop_table("companies")
    op.drop_table("user_profile")
