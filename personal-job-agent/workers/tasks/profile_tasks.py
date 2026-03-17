import logging
import os


from workers.celery_app import celery_app

logger = logging.getLogger(__name__)

SINGLE_USER_ID = "00000000-0000-0000-0000-000000000001"


@celery_app.task(name="workers.tasks.profile_tasks.check_profile_health")
def check_profile_health():
    """Check profile health and create refresh suggestions."""
    from db_utils import get_sync_session
    from sqlalchemy import text
    import uuid

    logger.info("Checking profile health...")

    with get_sync_session() as session:
        profile = session.execute(
            text("""
            SELECT full_name, current_title, skills, summary, linkedin_url,
                   target_titles, experience_years, updated_at
            FROM user_profile WHERE id = :id
            """),
            {"id": SINGLE_USER_ID},
        ).fetchone()

        if not profile:
            return

        name, title, skills, summary, linkedin, targets, years, updated_at = profile
        issues = []

        if not summary:
            issues.append("summary")
        if not linkedin:
            issues.append("linkedin_url")
        if not skills or len(skills or []) < 5:
            issues.append("skills")
        if not targets or len(targets or []) == 0:
            issues.append("target_titles")

        # Check staleness (30+ days since update)
        if updated_at:
            from datetime import datetime, timezone
            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=timezone.utc)
            days_since_update = (datetime.now(timezone.utc) - updated_at).days
            if days_since_update >= 30:
                issues.append("staleness")

        if issues:
            body = f"Profile needs attention: {', '.join(issues)}"
            session.execute(
                text("""
                INSERT INTO notifications (id, type, title, body, channel, is_read, priority, action_url, created_at, updated_at)
                VALUES (:id, 'profile_refresh', :title, :body, 'in_app', false, 'low', '/profile', NOW(), NOW())
                """),
                {
                    "id": str(uuid.uuid4()),
                    "title": "Profile Refresh Suggested",
                    "body": body,
                },
            )
            session.commit()

    logger.info(f"Profile health check complete. Issues: {issues}")


@celery_app.task(name="workers.tasks.profile_tasks.refresh_profile_vector")
def refresh_profile_vector():
    """Regenerate the user profile embedding vector."""
    from db_utils import get_sync_session
    from sqlalchemy import text
    from engines.embedding.embedder import embed_text
    from engines.embedding.vector_store import VectorStore
    import os

    logger.info("Refreshing profile vector...")

    with get_sync_session() as session:
        profile = session.execute(
            text("""
            SELECT full_name, current_title, skills, summary, target_titles, experience_years
            FROM user_profile WHERE id = :id
            """),
            {"id": SINGLE_USER_ID},
        ).fetchone()

        if not profile:
            return

        name, title, skills, summary, targets, years = profile
        skill_names = []
        if skills:
            for s in skills:
                if isinstance(s, dict):
                    skill_names.append(s.get("name", ""))
                else:
                    skill_names.append(str(s))

        profile_text = (
            f"{name} {title} {years} years experience "
            f"Skills: {' '.join(skill_names)} "
            f"Targets: {' '.join(targets or [])} "
            f"{summary or ''}"
        )

        vector = embed_text(profile_text)

        store = VectorStore(
            url=os.environ.get("QDRANT_URL", "http://localhost:6333"),
            collection_name="profile_embeddings",
        )
        store.upsert(
            id=SINGLE_USER_ID,
            vector=vector,
            payload={"user_id": SINGLE_USER_ID, "title": title},
        )

        session.execute(
            text("UPDATE user_profile SET profile_vector_id = :vid WHERE id = :id"),
            {"vid": SINGLE_USER_ID, "id": SINGLE_USER_ID},
        )
        session.commit()

    logger.info("Profile vector refreshed")
