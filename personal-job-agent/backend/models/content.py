import uuid
from sqlalchemy import String, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from backend.db.base import Base, TimestampMixin


class Content(Base, TimestampMixin):
    __tablename__ = "content"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    title: Mapped[str] = mapped_column(String(512), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    subject: Mapped[str] = mapped_column(String(512), default="")

    # Context
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    application_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # LLM metadata
    prompt_used: Mapped[str] = mapped_column(Text, default="")
    model_used: Mapped[str] = mapped_column(String(100), default="")
    generation_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Approval
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_at: Mapped[str | None] = mapped_column(String(100), nullable=True)
