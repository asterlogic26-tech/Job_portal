import uuid
import datetime
from typing import Any
from pydantic import BaseModel


class NotificationRead(BaseModel):
    id: uuid.UUID
    notification_type: str
    title: str
    body: str
    is_read: bool
    priority: str
    action_url: str
    metadata_: dict[str, Any] = {}
    created_at: datetime.datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class NotificationListResponse(BaseModel):
    items: list[NotificationRead]
    unread_count: int
    total: int
