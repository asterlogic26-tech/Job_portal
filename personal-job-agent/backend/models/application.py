import uuid
import datetime
from sqlalchemy import String, Integer, Float, Boolean, Text, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.base import Base, TimestampMixin

APPLICATION_STATUSES = [
    "saved",           # bookmarked, not yet acting
    "applying",        # user is manually preparing
    "auto_applying",   # auto-apply task in progress
    "auto_applied",    # successfully submitted by system
    "blocked",         # auto-apply was blocked — manual action needed
    "applied",         # manually applied by user
    "phone_screen",
    "technical_interview",
    "onsite_interview",
    "offer",
    "accepted",
    "rejected",
    "withdrawn",
    "ghosted",
]


class Application(Base, TimestampMixin):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # ── Status ────────────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(String(50), default="saved")

    # ── Apply method ──────────────────────────────────────────────────────────
    is_auto_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    apply_method: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # playwright | ats_api | manual
    blocked_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    direct_apply_url: Mapped[str] = mapped_column(Text, default="")

    # ── Timeline ──────────────────────────────────────────────────────────────
    # JSONB list of {event, timestamp, detail} dicts
    timeline: Mapped[list] = mapped_column(JSONB, default=list)

    applied_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_activity_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    follow_up_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Content ───────────────────────────────────────────────────────────────
    notes: Mapped[str] = mapped_column(Text, default="")
    resume_version_url: Mapped[str] = mapped_column(Text, default="")
    cover_letter_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # ── Interview / offer ─────────────────────────────────────────────────────
    interview_date: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    offer_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Extra ──────────────────────────────────────────────────────────────────
    custom_fields: Mapped[dict] = mapped_column(JSONB, default=dict)

    # ── Relations ─────────────────────────────────────────────────────────────
    job: Mapped["Job"] = relationship("Job", back_populates="applications")
