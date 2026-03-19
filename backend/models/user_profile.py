import uuid
from typing import Any
from sqlalchemy import String, Integer, Float, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from backend.db.base import Base, TimestampMixin


class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profile"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    current_title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    target_titles: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    skills: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    location: Mapped[str] = mapped_column(String(255), default="Remote")
    remote_preference: Mapped[str] = mapped_column(String(50), default="remote")
    target_salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    linkedin_url: Mapped[str] = mapped_column(Text, default="")
    github_url: Mapped[str] = mapped_column(Text, default="")
    resume_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    bio: Mapped[str] = mapped_column(Text, default="")
    preferences: Mapped[dict] = mapped_column(JSONB, default=dict)
    profile_embedding_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    health_score: Mapped[int] = mapped_column(Integer, default=0)
