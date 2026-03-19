import uuid
import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict


APPLICATION_STATUSES = [
    "saved", "applying", "auto_applying", "auto_applied", "blocked",
    "applied", "phone_screen", "technical_interview", "onsite_interview",
    "offer", "accepted", "rejected", "withdrawn", "ghosted",
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


class ApplicationStatusUpdate(BaseModel):
    status: str
    note: str = ""


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID | None
    status: str
    is_auto_applied: bool = False
    apply_method: str | None = None
    blocked_reason: str | None = None
    direct_apply_url: str = ""
    applied_at: datetime.datetime | None
    last_activity_at: datetime.datetime
    follow_up_at: datetime.datetime | None
    interview_date: datetime.datetime | None
    offer_amount: int | None
    notes: str
    resume_version_url: str
    cover_letter_id: uuid.UUID | None = None
    timeline: List[dict] = []
    custom_fields: dict[str, Any]
    created_at: datetime.datetime
    updated_at: datetime.datetime

    # Flattened from related Job
    job_title: str | None = None
    company_name: str | None = None
    job_url: str | None = None
    match_score: float | None = None
