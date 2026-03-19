import uuid
import datetime
from typing import Any
from pydantic import BaseModel


class SkillRef(BaseModel):
    name: str
    level: str = ""
    required: bool = True


class JobMatchRead(BaseModel):
    total_score: float
    skill_score: float
    seniority_score: float
    salary_score: float
    recency_score: float
    culture_score: float
    company_growth_score: float
    interview_probability: float
    matching_skills: list[str]
    missing_skills: list[str]
    score_breakdown: dict[str, Any]

    model_config = {"from_attributes": True}


class JobRead(BaseModel):
    id: uuid.UUID
    external_id: str
    source: str
    title: str
    normalized_title: str
    company_name: str
    location: str
    remote_policy: str
    seniority_level: str
    salary_min: int | None
    salary_max: int | None
    salary_currency: str
    required_skills: list[Any]
    preferred_skills: list[Any]
    url: str
    apply_url: str
    posted_at: str | None
    is_hidden: bool
    is_saved: bool
    is_applied: bool
    match: JobMatchRead | None = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    items: list[JobRead]
    total: int
    page: int
    page_size: int


class JobFilter(BaseModel):
    q: str | None = None
    remote_only: bool = False
    min_score: float | None = None
    seniority: str | None = None
    source: str | None = None
    saved_only: bool = False
    page: int = 1
    page_size: int = 20
