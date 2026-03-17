import uuid
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from backend.models.application import Application
from backend.models.job import Job
from backend.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationRead


class ApplicationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self, user_id: uuid.UUID, status_filter: str | None = None) -> list[ApplicationRead]:
        stmt = (
            select(Application)
            .options(selectinload(Application.job))
            .where(Application.user_id == user_id)
            .order_by(Application.last_activity_at.desc())
        )
        if status_filter:
            stmt = stmt.where(Application.status == status_filter)

        result = await self.db.execute(stmt)
        apps = result.scalars().all()
        return [self._to_read(a) for a in apps]

    async def create(self, user_id: uuid.UUID, payload: ApplicationCreate) -> ApplicationRead:
        app = Application(
            user_id=user_id,
            job_id=payload.job_id,
            status=payload.status,
            notes=payload.notes,
        )
        self.db.add(app)

        # Mark job as applied if status >= applied
        if payload.status not in ("saved", "applying"):
            job = await self.db.get(Job, payload.job_id)
            if job:
                job.is_applied = True

        await self.db.commit()
        await self.db.refresh(app)
        return self._to_read(app)

    async def get(self, app_id: uuid.UUID) -> ApplicationRead | None:
        stmt = (
            select(Application)
            .options(selectinload(Application.job))
            .where(Application.id == app_id)
        )
        result = await self.db.execute(stmt)
        app = result.scalar_one_or_none()
        return self._to_read(app) if app else None

    async def update(self, app_id: uuid.UUID, payload: ApplicationUpdate) -> ApplicationRead | None:
        app = await self.db.get(Application, app_id)
        if not app:
            return None
        for field, val in payload.model_dump(exclude_none=True).items():
            setattr(app, field, val)
        app.last_activity_at = datetime.datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(app)
        return self._to_read(app)

    async def update_status(self, app_id: uuid.UUID, status: str) -> ApplicationRead | None:
        app = await self.db.get(Application, app_id)
        if not app:
            return None
        app.status = status
        app.last_activity_at = datetime.datetime.utcnow()
        if status == "applied" and not app.applied_at:
            app.applied_at = datetime.datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(app)
        return self._to_read(app)

    async def delete(self, app_id: uuid.UUID) -> None:
        app = await self.db.get(Application, app_id)
        if app:
            await self.db.delete(app)
            await self.db.commit()

    def _to_read(self, app: Application) -> ApplicationRead:
        data = ApplicationRead.model_validate(app)
        if app.job:
            data.job_title = app.job.title
            data.company_name = app.job.company_name
            data.job_url = app.job.url
        return data
