import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from backend.models.notification import Notification
from backend.schemas.notification import NotificationRead, NotificationListResponse


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(
        self,
        user_id: uuid.UUID,
        unread_only: bool = False,
        page: int = 1,
        page_size: int = 30,
    ) -> NotificationListResponse:
        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.is_read == False)

        total = (await self.db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()

        unread_stmt = select(func.count()).where(
            Notification.user_id == user_id, Notification.is_read == False
        )
        unread_count = (await self.db.execute(unread_stmt)).scalar_one()

        stmt = stmt.order_by(Notification.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        items = result.scalars().all()

        return NotificationListResponse(
            items=[NotificationRead.model_validate(n) for n in items],
            unread_count=unread_count,
            total=total,
        )

    async def mark_read(self, notif_id: uuid.UUID) -> None:
        notif = await self.db.get(Notification, notif_id)
        if notif:
            notif.is_read = True
            await self.db.commit()

    async def mark_all_read(self, user_id: uuid.UUID) -> int:
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)
            .values(is_read=True)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount

    async def delete_read(self, user_id: uuid.UUID) -> int:
        stmt = delete(Notification).where(
            Notification.user_id == user_id, Notification.is_read == True
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount

    async def create(
        self,
        user_id: uuid.UUID,
        notification_type: str,
        title: str,
        body: str = "",
        priority: str = "normal",
        action_url: str = "",
        metadata: dict | None = None,
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            body=body,
            priority=priority,
            action_url=action_url,
            metadata_=metadata or {},
        )
        self.db.add(notif)
        await self.db.commit()
        await self.db.refresh(notif)
        return notif
