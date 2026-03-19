import uuid
import datetime
from typing import Any
from pydantic import BaseModel


class CompanySignalRead(BaseModel):
    id: uuid.UUID
    signal_type: str
    title: str
    summary: str
    source_url: str
    amount_usd: int | None
    signal_date: datetime.datetime | None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class CompanyRead(BaseModel):
    id: uuid.UUID
    name: str
    domain: str
    website: str
    description: str
    industry: str
    size_range: str
    stage: str
    headquarters: str
    hiring_score: float
    job_velocity: float
    is_watched: bool
    total_funding_usd: int | None
    last_funding_round: str
    signals: list[CompanySignalRead] = []
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class CompanyListResponse(BaseModel):
    items: list[CompanyRead]
    total: int
