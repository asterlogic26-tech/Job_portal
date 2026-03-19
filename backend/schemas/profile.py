import uuid
import datetime
from typing import Any
from pydantic import BaseModel, Field, HttpUrl


class SkillItem(BaseModel):
    name: str
    level: str = "intermediate"  # beginner, intermediate, expert
    years: int = 0


class ProfileRead(BaseModel):
    id: uuid.UUID
    full_name: str
    current_title: str
    target_titles: list[str]
    skills: list[SkillItem]
    experience_years: int
    location: str
    remote_preference: str
    target_salary_min: int | None
    target_salary_max: int | None
    linkedin_url: str
    github_url: str
    resume_url: str | None
    bio: str
    preferences: dict[str, Any]
    health_score: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    current_title: str | None = None
    target_titles: list[str] | None = None
    skills: list[SkillItem] | None = None
    experience_years: int | None = None
    location: str | None = None
    remote_preference: str | None = None
    target_salary_min: int | None = None
    target_salary_max: int | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    bio: str | None = None
    preferences: dict[str, Any] | None = None


class ProfileHealthRead(BaseModel):
    score: int
    grade: str
    missing_fields: list[str]
    suggestions: list[str]
