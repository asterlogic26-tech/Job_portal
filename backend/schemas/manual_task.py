import uuid
import datetime
from typing import Any
from pydantic import BaseModel


class ManualTaskRead(BaseModel):
    id: uuid.UUID
    task_type: str
    status: str
    title: str
    description: str
    site_url: str
    instructions: str
    context_data: dict[str, Any]
    job_id: uuid.UUID | None
    completed_at: datetime.datetime | None
    completion_notes: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class ManualTaskResolve(BaseModel):
    completion_notes: str = ""


class ManualTaskListResponse(BaseModel):
    items: list[ManualTaskRead]
    total: int
    pending_count: int
