import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import get_session, get_user_id
from backend.schemas.notification import NotificationRead, NotificationListResponse
from backend.schemas.common import MessageResponse
from backend.services.notification_service import NotificationService

router = APIRouter()


def _svc(db: AsyncSession = Depends(get_session)) -> NotificationService:
    return NotificationService(db)


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    user_id: uuid.UUID = Depends(get_user_id),
    svc: NotificationService = Depends(_svc),
):
    return await svc.list(user_id, unread_only=unread_only, page=page, page_size=page_size)


@router.post("/{notif_id}/read", response_model=MessageResponse)
async def mark_read(notif_id: uuid.UUID, svc: NotificationService = Depends(_svc)):
    await svc.mark_read(notif_id)
    return MessageResponse(message="Notification marked as read")


@router.post("/read-all", response_model=MessageResponse)
async def mark_all_read(
    user_id: uuid.UUID = Depends(get_user_id),
    svc: NotificationService = Depends(_svc),
):
    count = await svc.mark_all_read(user_id)
    return MessageResponse(message=f"Marked {count} notifications as read")


@router.delete("/clear-read", response_model=MessageResponse)
async def clear_read(
    user_id: uuid.UUID = Depends(get_user_id),
    svc: NotificationService = Depends(_svc),
):
    count = await svc.delete_read(user_id)
    return MessageResponse(message=f"Deleted {count} read notifications")
