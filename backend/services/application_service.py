import uuid
import datetime
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from backend.models.application import Application
from backend.models.job import Job
from backend.models.job_match import JobMatch
from backend.schemas.application import (
    ApplicationCreate, ApplicationUpdate, ApplicationRead,
)


class ApplicationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Queries ────────────────────────────────────────────────────────────────

    async def list(
        self,
        user_id: uuid.UUID,
        status_filter: Optional[str] = None,
        auto_applied_only: bool = False,
        blocked_only: bool = False,
    ) -> List[ApplicationRead]:
        stmt = (
            select(Application)
            .options(selectinload(Application.job))
            .where(Application.user_id == user_id)
            .order_by(Application.last_activity_at.desc())
        )
        if status_filter:
            stmt = stmt.where(Application.status == status_filter)
        if auto_applied_only:
            stmt = stmt.where(Application.is_auto_applied == True)  # noqa: E712
        if blocked_only:
            stmt = stmt.where(Application.status == "blocked")

        result = await self.db.execute(stmt)
        apps = result.scalars().all()
        return [await self._to_read(a) for a in apps]

    async def get(self, app_id: uuid.UUID) -> Optional[ApplicationRead]:
        stmt = (
            select(Application)
            .options(selectinload(Application.job))
            .where(Application.id == app_id)
        )
        result = await self.db.execute(stmt)
        app = result.scalar_one_or_none()
        return await self._to_read(app) if app else None

    # ── Mutations ──────────────────────────────────────────────────────────────

    async def create(self, user_id: uuid.UUID, payload: ApplicationCreate) -> ApplicationRead:
        app = Application(
            user_id=user_id,
            job_id=payload.job_id,
            status=payload.status,
            notes=payload.notes,
            timeline=[_timeline_event("created", f"Application saved with status '{payload.status}'")],
        )
        self.db.add(app)

        if payload.status not in ("saved", "applying", "auto_applying"):
            job = await self.db.get(Job, payload.job_id)
            if job:
                job.is_applied = True

        await self.db.commit()
        await self.db.refresh(app)
        return await self._to_read(app)

    async def update(self, app_id: uuid.UUID, payload: ApplicationUpdate) -> Optional[ApplicationRead]:
        app = await self.db.get(Application, app_id)
        if not app:
            return None
        for field, val in payload.model_dump(exclude_none=True).items():
            setattr(app, field, val)
        app.last_activity_at = datetime.datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(app)
        return await self._to_read(app)

    async def update_status(
        self, app_id: uuid.UUID, status: str, note: str = ""
    ) -> Optional[ApplicationRead]:
        app = await self.db.get(Application, app_id)
        if not app:
            return None

        old_status = app.status
        app.status = status
        app.last_activity_at = datetime.datetime.utcnow()

        if status == "applied" and not app.applied_at:
            app.applied_at = datetime.datetime.utcnow()
            if not app.is_auto_applied:
                app.apply_method = "manual"

        detail = note or f"Status changed: {old_status} → {status}"
        timeline = list(app.timeline or [])
        timeline.append(_timeline_event("status_changed", detail))
        app.timeline = timeline

        await self.db.commit()
        await self.db.refresh(app)
        return await self._to_read(app)

    async def mark_manually_applied(self, app_id: uuid.UUID) -> Optional[ApplicationRead]:
        """Mark a blocked application as applied manually — user clicked the direct link."""
        return await self.update_status(
            app_id, "applied", "User applied manually via direct apply link"
        )

    async def delete(self, app_id: uuid.UUID) -> None:
        app = await self.db.get(Application, app_id)
        if app:
            await self.db.delete(app)
            await self.db.commit()

    # ── Auto-apply trigger ────────────────────────────────────────────────────

    async def trigger_auto_apply(self, job_id: uuid.UUID, match_score: float = 0.0) -> str:
        """Queue an auto-apply Celery task and return the task ID."""
        from workers.celery_app import celery_app
        task = celery_app.send_task(
            "workers.tasks.apply_tasks.auto_apply_job",
            args=[str(job_id), match_score],
            queue="default",
        )
        return task.id

    # ── Stats ──────────────────────────────────────────────────────────────────

    async def get_stats(self, user_id: uuid.UUID) -> dict:
        stmt = (
            select(Application.status, func.count())
            .where(Application.user_id == user_id)
            .group_by(Application.status)
        )
        result = await self.db.execute(stmt)
        counts = dict(result.all())
        return {
            "total": sum(counts.values()),
            "auto_applied": counts.get("auto_applied", 0),
            "blocked": counts.get("blocked", 0),
            "applied": counts.get("applied", 0) + counts.get("auto_applied", 0),
            "interview": (
                counts.get("phone_screen", 0)
                + counts.get("technical_interview", 0)
                + counts.get("onsite_interview", 0)
            ),
            "offer": counts.get("offer", 0),
            "by_status": counts,
        }

    # ── Serialization ──────────────────────────────────────────────────────────

    async def _to_read(self, app: Application) -> ApplicationRead:
        data = ApplicationRead.model_validate(app)
        if app.job:
            data.job_title = app.job.title
            data.company_name = app.job.company_name
            data.job_url = app.job.url

        if app.job_id:
            match_stmt = select(JobMatch).where(JobMatch.job_id == app.job_id)
            match_result = await self.db.execute(match_stmt)
            match = match_result.scalar_one_or_none()
            if match:
                data.match_score = match.match_score
        return data


def _timeline_event(event_type: str, detail: str) -> dict:
    from datetime import datetime, timezone
    return {
        "event": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "detail": detail,
    }
