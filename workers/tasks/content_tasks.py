import logging
import asyncio
import os
import uuid


from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.tasks.content_tasks.generate_daily_content_suggestions")
def generate_daily_content_suggestions():
    """Generate daily LinkedIn post drafts."""
    asyncio.run(_generate_daily_async())


async def _generate_daily_async():
    from engines.content.generator import ContentGenerator
    from workers.db_utils import get_sync_session
    from sqlalchemy import text

    logger.info("Generating daily content suggestions...")

    generator = ContentGenerator()

    with get_sync_session() as session:
        profile = session.execute(
            text("SELECT full_name, current_title, experience_years, skills FROM user_profile LIMIT 1")
        ).fetchone()

    if not profile:
        return

    name, title, years, skills = profile

    try:
        result = await generator.generate(
            content_type="linkedin_post",
            tone="professional",
            additional_context="career growth, technology trends, job search",
        )

        with get_sync_session() as session:
            session.execute(
                text("""
                INSERT INTO generated_content (id, type, content_body, status, tone, created_at, updated_at)
                VALUES (:id, 'linkedin_post', :body, 'draft', 'professional', NOW(), NOW())
                """),
                {
                    "id": str(uuid.uuid4()),
                    "body": result.get("body", ""),
                },
            )
            session.commit()

        logger.info("Daily LinkedIn post draft generated")
    except Exception as e:
        logger.error(f"Content generation failed: {e}")
