import uuid
import datetime
from typing import Any
from pydantic import BaseModel


APPLICATION_STATUSES = [
    "saved", "applying", "applied", "phone_screen",
    "technical_interview", "onsite_interview", "offer",
    "accepted", "rejected", "withdrawn", "ghosted",
]


class ApplicationCreate(BaseModel):
    job_id: uuid.UUID
    status: str = "saved"
    notes: str = ""


class ApplicationUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None
    applied_at: datetime.datetime | None = None
    follow_up_at: datetime.datetime | None = None
    interview_date: datetime.datetime | None = None
    offer_amount: int | None = None
    resume_version_url: str | None = None
    custom_fields: dict[str, Any] | None = None


class ApplicationRead(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID | None
    status: str
    applied_at: datetime.datetime | None
    last_activity_at: datetime.datetime
    follow_up_at: datetime.datetime | None
    interview_date: datetime.datetime | None
    offer_amount: int | None
    notes: str
    resume_version_url: str
    custom_fields: dict[str, Any]
    created_at: datetime.datetime
    updated_at: datetime.datetime

    # Embedded job summary
    job_title: str | None = None
    company_name: str | None = None
    job_url: str | None = None

    model_config = {"from_attributes": True}


class ApplicationStatusUpdate(BaseModel):
    status: str
