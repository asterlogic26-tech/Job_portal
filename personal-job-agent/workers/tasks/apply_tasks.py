"""
Auto-apply Celery tasks.

Flow:
  1. ``auto_apply_job`` is queued by matching_tasks when match >= 75.
  2. It runs the full auto-apply pipeline:
       a. Load job + profile from DB
       b. Generate cover letter via ContentGenerator
       c. Attempt Playwright form-fill
       d. Store cover letter in content table
       e. Update application status
       f. If blocked → create ManualTask + high-priority Notification
  3. All DB access is synchronous (Celery context).
"""
import asyncio
import logging
import uuid

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)

SINGLE_USER_ID = "00000000-0000-0000-0000-000000000001"
AUTO_APPLY_THRESHOLD = 75.0


@celery_app.task(
    name="workers.tasks.apply_tasks.auto_apply_job",
    bind=True,
)
def auto_apply_job(self, job_id: str, match_score: float = 0.0):
    """Attempt to auto-apply for a high-match job.

    Creates or updates an Application record, runs the auto-apply engine,
    and dispatches a ManualTask + Notification if blocked.
    """
    try:
        asyncio.run(_auto_apply_async(job_id, match_score))
    except Exception as exc:
        logger.error("auto_apply_job failed for %s: %s", job_id, exc)
        raise self.retry(exc=exc, countdown=120)


# ── Async implementation ──────────────────────────────────────────────────────

async def _auto_apply_async(job_id: str, match_score: float):
    import os
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/job_agent",
    )
    if not db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url, pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as db:
        await _run_apply_pipeline(db, job_id, match_score)

    await engine.dispose()


async def _run_apply_pipeline(db, job_id: str, match_score: float):
    from sqlalchemy import select, text
    from datetime import datetime, timezone

    from backend.models.job import Job
    from backend.models.application import Application
    from backend.models.user_profile import UserProfile
    from backend.models.manual_task import ManualTask
    from backend.models.notification import Notification
    from engines.apply.auto_apply_engine import run_auto_apply
    from engines.content.generator import ContentGenerator

    user_id = uuid.UUID(SINGLE_USER_ID)
    job_uuid = uuid.UUID(job_id)
    now = datetime.now(timezone.utc)

    # ── Load data ─────────────────────────────────────────────────────────────
    job = await db.get(Job, job_uuid)
    if not job:
        logger.warning("Job %s not found, skipping auto-apply", job_id)
        return

    profile = await db.get(UserProfile, user_id)
    if not profile:
        logger.warning("Profile not found, skipping auto-apply for %s", job_id)
        return

    apply_url = job.apply_url or job.url or ""

    # ── Get or create Application record ─────────────────────────────────────
    stmt = select(Application).where(
        Application.job_id == job_uuid,
        Application.user_id == user_id,
    )
    result = await db.execute(stmt)
    app = result.scalar_one_or_none()

    if app is None:
        app = Application(
            id=uuid.uuid4(),
            job_id=job_uuid,
            user_id=user_id,
            status="auto_applying",
        )
        db.add(app)
    else:
        # Don't re-apply if already applied or auto-applied
        if app.status in ("auto_applied", "applied", "interview", "offer", "accepted"):
            logger.info("Job %s already applied, skipping", job_id)
            return
        app.status = "auto_applying"

    app.last_activity_at = now
    _add_timeline_event(app, "auto_apply_queued", f"Match score: {match_score:.0f}%")
    await db.commit()

    # ── Generate cover letter ──────────────────────────────────────────────────
    cover_letter_text = await _generate_cover_letter(job, profile)
    cover_letter_id = await _save_cover_letter(db, cover_letter_text, job_uuid, user_id)

    # ── Run auto-apply engine ─────────────────────────────────────────────────
    profile_dict = {
        "full_name": profile.full_name or "",
        "email": getattr(profile, "email", "") or "",
        "phone": getattr(profile, "phone", "") or "",
        "linkedin_url": profile.linkedin_url or "",
        "resume_url": profile.resume_url or None,
    }
    job_dict = {
        "title": job.title,
        "company_name": job.company_name,
        "description": job.description or "",
    }

    apply_result = await run_auto_apply(
        apply_url=apply_url,
        profile=profile_dict,
        job=job_dict,
        cover_letter=cover_letter_text,
    )

    # ── Update Application based on result ────────────────────────────────────
    if apply_result["applied"]:
        app.status = "auto_applied"
        app.applied_at = now
        app.is_auto_applied = True
        app.apply_method = apply_result.get("apply_method", "playwright")
        app.cover_letter_id = cover_letter_id
        _add_timeline_event(
            app,
            "auto_apply_success",
            f"Auto-applied via {app.apply_method}. "
            f"Fields filled: {', '.join(apply_result.get('fields_filled', []))}",
        )
        # Mark job as applied
        job.is_applied = True
        logger.info(
            "Auto-applied to %s at %s (method=%s)",
            job.title, job.company_name, app.apply_method,
        )
    else:
        blocked_reason = apply_result.get("blocked_reason", "unknown")
        app.status = "blocked"
        app.blocked_reason = blocked_reason
        app.direct_apply_url = apply_url
        _add_timeline_event(
            app,
            "auto_apply_blocked",
            f"Auto-apply blocked: {blocked_reason}. Manual action required.",
        )
        logger.info(
            "Auto-apply blocked for %s: %s", job.title, blocked_reason
        )

        # Create ManualTask
        task = ManualTask(
            id=uuid.uuid4(),
            user_id=user_id,
            task_type="manual_apply",
            title=f"Apply manually: {job.title} at {job.company_name}",
            description=(
                f"Auto-apply was blocked ({blocked_reason}). "
                f"Please apply manually at: {apply_url}\n\n"
                f"Match score: {match_score:.0f}%"
            ),
            url=apply_url,
            related_job_id=job_uuid,
            priority="high",
            status="pending",
        )
        db.add(task)

        # Create high-priority Notification
        notif = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            type="auto_apply_blocked",
            title=f"Action Required: Apply to {job.title} at {job.company_name}",
            body=(
                f"Match score {match_score:.0f}% — auto-apply was blocked. "
                f"Click to apply manually."
            ),
            channel="in_app",
            priority="high",
            is_read=False,
            related_job_id=job_uuid,
            action_url=apply_url,
        )
        db.add(notif)

    app.last_activity_at = datetime.now(timezone.utc)
    await db.commit()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _add_timeline_event(app, event_type: str, detail: str):
    """Append an event to the application timeline JSONB array."""
    from datetime import datetime, timezone
    timeline = list(app.timeline or [])
    timeline.append({
        "event": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "detail": detail,
    })
    app.timeline = timeline


async def _generate_cover_letter(job, profile) -> str:
    """Generate a tailored cover letter. Fallback to template on error."""
    try:
        from engines.content.generator import ContentGenerator

        class _Job:
            title = job.title
            company_name = job.company_name

        class _Profile:
            full_name = profile.full_name
            experience_years = getattr(profile, "experience_years", 0) or 0
            skills = profile.skills or []

        gen = ContentGenerator()
        result = await gen.generate(
            content_type="cover_letter",
            job=_Job(),
            profile=_Profile(),
            tone="professional",
        )
        return result.get("body", "").strip()
    except Exception as exc:
        logger.warning("Cover letter generation failed: %s", exc)
        return (
            f"Dear Hiring Team,\n\n"
            f"I am excited to apply for the {job.title} position at {job.company_name}. "
            f"I believe my skills and experience make me an excellent fit for this role.\n\n"
            f"Best regards,\n{profile.full_name or 'Candidate'}"
        )


async def _save_cover_letter(db, body: str, job_id: uuid.UUID, user_id: uuid.UUID) -> uuid.UUID:
    """Store cover letter in the content table and return its ID."""
    from backend.models.content import Content
    cl = Content(
        id=uuid.uuid4(),
        user_id=user_id,
        job_id=job_id,
        content_type="cover_letter",
        content_body=body,
        status="generated",
        tone="professional",
        model_used="auto",
    )
    db.add(cl)
    await db.flush()
    return cl.id
