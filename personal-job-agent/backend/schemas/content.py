import uuid
import datetime
from typing import Any
from pydantic import BaseModel


class ContentGenerate(BaseModel):
    content_type: str  # cover_letter, linkedin_post, outreach_email, etc.
    job_id: uuid.UUID | None = None
    company_id: uuid.UUID | None = None
    application_id: uuid.UUID | None = None
    extra_context: dict[str, Any] = {}


class ContentUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    subject: str | None = None
    status: str | None = None


class ContentRead(BaseModel):
    id: uuid.UUID
    content_type: str
    status: str
    title: str
    body: str
    subject: str
    job_id: uuid.UUID | None
    company_id: uuid.UUID | None
    application_id: uuid.UUID | None
    is_approved: bool
    approved_at: str | None
    model_used: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class ContentListResponse(BaseModel):
    items: list[ContentRead]
    total: int
