import uuid
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.session import AsyncSessionLocal, engine
from backend.db.base import Base
from backend.core.config import settings
from backend.core.logging import get_logger

log = get_logger(__name__)


async def create_tables() -> None:
    """Create all tables (dev only — use Alembic in production)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("Database tables created.")


async def run_seed() -> None:
    """Insert default user profile if not present."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("SELECT id FROM user_profile WHERE id = :uid"),
            {"uid": settings.single_user_id},
        )
        if result.fetchone():
            log.info("Seed data already present, skipping.")
            return

        await session.execute(
            text("""
                INSERT INTO user_profile (
                    id, full_name, current_title, target_titles, skills,
                    experience_years, location, remote_preference,
                    target_salary_min, target_salary_max,
                    linkedin_url, github_url, preferences, created_at, updated_at
                ) VALUES (
                    :id, :full_name, :current_title, :target_titles, :skills::jsonb,
                    :experience_years, :location, :remote_preference,
                    :target_salary_min, :target_salary_max,
                    :linkedin_url, :github_url, :preferences::jsonb, NOW(), NOW()
                ) ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": settings.single_user_id,
                "full_name": "Job Seeker",
                "current_title": "Software Engineer",
                "target_titles": ["Software Engineer", "Senior Software Engineer", "Full Stack Developer"],
                "skills": '[{"name":"Python","level":"expert","years":5},{"name":"React","level":"intermediate","years":3}]',
                "experience_years": 5,
                "location": "Remote",
                "remote_preference": "remote",
                "target_salary_min": 100000,
                "target_salary_max": 180000,
                "linkedin_url": "",
                "github_url": "",
                "preferences": '{"notify_high_match":true,"notify_digest":true,"min_match_score":50}',
            },
        )
        await session.commit()
        log.info("Default user profile seeded.")
