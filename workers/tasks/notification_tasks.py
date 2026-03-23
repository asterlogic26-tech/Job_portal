import logging
import asyncio
import os


from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.tasks.notification_tasks.send_digest")
def send_digest():
    """Send daily digest email/notification."""
    from workers.db_utils import get_sync_session
    from sqlalchemy import text
    import uuid

    logger.info("Sending daily digest...")

    with get_sync_session() as session:
        # Get stats
        new_jobs = session.execute(
            text("SELECT COUNT(*) FROM jobs WHERE discovered_at >= NOW() - INTERVAL '24 hours'")
        ).scalar()
        high_match = session.execute(
            text("SELECT COUNT(*) FROM job_matches WHERE match_score >= 75 AND computed_at >= NOW() - INTERVAL '24 hours'")
        ).scalar()
        active_apps = session.execute(
            text("SELECT COUNT(*) FROM applications WHERE status IN ('submitted', 'phone_screen', 'interview')")
        ).scalar()
        pending_tasks = session.execute(
            text("SELECT COUNT(*) FROM manual_tasks WHERE status = 'pending'")
        ).scalar()

        # Create in-app digest notification
        session.execute(
            text("""
            INSERT INTO notifications (id, type, title, body, channel, is_read, priority, created_at, updated_at)
            VALUES (:id, 'daily_digest', :title, :body, 'in_app', false, 'low', NOW(), NOW())
            """),
            {
                "id": str(uuid.uuid4()),
                "title": "Daily Job Search Digest",
                "body": f"{new_jobs} new jobs found. {high_match} high matches. {active_apps} active applications. {pending_tasks} pending tasks.",
            },
        )
        session.commit()

    # Send email if configured
    email_enabled = os.environ.get("ENABLE_EMAIL_NOTIFICATIONS", "false").lower() == "true"
    if email_enabled:
        try:
            from integrations.email.email_client import EmailClient
            email = EmailClient(
                host=os.environ.get("SMTP_HOST", ""),
                port=int(os.environ.get("SMTP_PORT", 587)),
                username=os.environ.get("SMTP_USER", ""),
                password=os.environ.get("SMTP_PASSWORD", ""),
            )
            email.send_digest(
                to=os.environ.get("NOTIFICATION_EMAIL", ""),
                stats={
                    "new_jobs": new_jobs,
                    "high_match": high_match,
                    "active_apps": active_apps,
                    "pending_tasks": pending_tasks,
                },
            )
        except Exception as e:
            logger.error(f"Email digest failed: {e}")

    logger.info("Daily digest sent")


@celery_app.task(name="workers.tasks.notification_tasks.send_followup_reminders")
def send_followup_reminders():
    """Send follow-up reminders for applications due today."""
    from workers.db_utils import get_sync_session
    from sqlalchemy import text
    import uuid

    logger.info("Checking follow-up reminders...")

    with get_sync_session() as session:
        due = session.execute(
            text("""
            SELECT a.id, a.job_id, j.title, j.company_name
            FROM applications a
            JOIN jobs j ON j.id = a.job_id
            WHERE a.follow_up_date <= CURRENT_DATE
              AND a.status = 'submitted'
            """)
        ).fetchall()

        for app_id, job_id, title, company in due:
            session.execute(
                text("""
                INSERT INTO notifications (id, type, title, body, channel, is_read, priority, related_job_id, action_url, created_at, updated_at)
                VALUES (:id, 'follow_up_reminder', :title, :body, 'in_app', false, 'medium', :job_id, :url, NOW(), NOW())
                """),
                {
                    "id": str(uuid.uuid4()),
                    "title": f"Follow-up: {title} at {company}",
                    "body": "Time to send a follow-up message for this application.",
                    "job_id": str(job_id),
                    "url": f"/pipeline",
                },
            )

        session.commit()

    logger.info(f"Follow-up reminders sent for {len(due)} applications")
