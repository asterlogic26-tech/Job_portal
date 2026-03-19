import uuid
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.models.manual_task import ManualTask
from backend.schemas.manual_task import ManualTaskRead, ManualTaskListResponse


class ManualTaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(
        self, user_id: uuid.UUID, status_filter: str | None = None
    ) -> ManualTaskListResponse:
        stmt = select(ManualTask).where(ManualTask.user_id == user_id)
        if status_filter:
            stmt = stmt.where(ManualTask.status == status_filter)

        total = (await self.db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
        pending_count = (
            await self.db.execute(
                select(func.count()).where(
                    ManualTask.user_id == user_id, ManualTask.status == "pending"
                )
            )
        ).scalar_one()

        stmt = stmt.order_by(ManualTask.created_at.desc())
        result = await self.db.execute(stmt)
        items = result.scalars().all()

        return ManualTaskListResponse(
            items=[ManualTaskRead.model_validate(t) for t in items],
            total=total,
            pending_count=pending_count,
        )

    async def get(self, task_id: uuid.UUID) -> ManualTask | None:
        return await self.db.get(ManualTask, task_id)

    async def update_status(self, task_id: uuid.UUID, status: str) -> ManualTask | None:
        task = await self.db.get(ManualTask, task_id)
        if not task:
            return None
        task.status = status
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def resolve(self, task_id: uuid.UUID, notes: str = "") -> ManualTask | None:
        task = await self.db.get(ManualTask, task_id)
        if not task:
            return None
        task.status = "completed"
        task.completed_at = datetime.datetime.utcnow()
        task.completion_notes = notes
        await self.db.commit()
        await self.db.refresh(task)
        return task
