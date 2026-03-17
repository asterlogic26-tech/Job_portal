import uuid
import datetime
from sqlalchemy import String, Integer, Float, Text, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.base import Base, TimestampMixin


class Application(Base, TimestampMixin):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Status
    status: Mapped[str] = mapped_column(String(50), default="saved")

    # Timeline
    applied_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_activity_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    follow_up_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Notes
    notes: Mapped[str] = mapped_column(Text, default="")
    resume_version_url: Mapped[str] = mapped_column(Text, default="")
    cover_letter_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Interview
    interview_date: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    offer_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Extra
    custom_fields: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Relations
    job: Mapped["Job"] = relationship("Job", back_populates="applications")
