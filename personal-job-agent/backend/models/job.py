import uuid
from sqlalchemy import String, Integer, Float, Text, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.base import Base, TimestampMixin


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    external_id: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)

    # Core fields
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    normalized_title: Mapped[str] = mapped_column(String(512), default="")
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Description
    description: Mapped[str] = mapped_column(Text, default="")
    description_html: Mapped[str] = mapped_column(Text, default="")

    # Location
    location: Mapped[str] = mapped_column(String(255), default="")
    remote_policy: Mapped[str] = mapped_column(String(50), default="unknown")

    # Seniority
    seniority_level: Mapped[str] = mapped_column(String(50), default="unknown")

    # Salary
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_currency: Mapped[str] = mapped_column(String(10), default="USD")

    # Skills
    required_skills: Mapped[list] = mapped_column(JSONB, default=list)
    preferred_skills: Mapped[list] = mapped_column(JSONB, default=list)

    # URL
    url: Mapped[str] = mapped_column(Text, nullable=False)
    apply_url: Mapped[str] = mapped_column(Text, default="")

    # Metadata
    posted_at: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    embedding_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # User interaction
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    is_saved: Mapped[bool] = mapped_column(Boolean, default=False)
    is_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    content_hash: Mapped[str] = mapped_column(String(64), default="")

    # Relations
    match: Mapped["JobMatch"] = relationship("JobMatch", back_populates="job", uselist=False)
    applications: Mapped[list["Application"]] = relationship("Application", back_populates="job")
