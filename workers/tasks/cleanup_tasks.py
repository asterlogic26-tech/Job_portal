import logging
import os


from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.tasks.cleanup_tasks.remove_stale_jobs")
def remove_stale_jobs():
    """Remove expired jobs and old notifications."""
    from db_utils import get_sync_session
    from sqlalchemy import text

    logger.info("Running cleanup...")

    with get_sync_session() as session:
        # Mark jobs older than 90 days as expired
        result = session.execute(
            text("""
            UPDATE jobs SET status = 'expired', updated_at = NOW()
            WHERE discovered_at < NOW() - INTERVAL '90 days'
              AND status NOT IN ('expired', 'hidden')
            """)
        )
        expired_count = result.rowcount

        # Delete read notifications older than 7 days
        result = session.execute(
            text("""
            DELETE FROM notifications
            WHERE is_read = true
              AND created_at < NOW() - INTERVAL '7 days'
            """)
        )
        deleted_notifs = result.rowcount

        # Delete duplicate jobs
        result = session.execute(
            text("""
            DELETE FROM jobs WHERE is_duplicate = true
              AND created_at < NOW() - INTERVAL '30 days'
            """)
        )
        deleted_dupes = result.rowcount

        session.commit()

    logger.info(f"Cleanup: {expired_count} expired, {deleted_notifs} notifications deleted, {deleted_dupes} dupes removed")
    return {
        "expired_jobs": expired_count,
        "deleted_notifications": deleted_notifs,
        "deleted_duplicates": deleted_dupes,
    }
