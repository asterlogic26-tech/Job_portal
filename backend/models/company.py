import uuid
from sqlalchemy import String, Integer, Float, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.base import Base, TimestampMixin


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), default="")
    domain: Mapped[str] = mapped_column(String(255), default="")
    website: Mapped[str] = mapped_column(Text, default="")
    linkedin_url: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    industry: Mapped[str] = mapped_column(String(255), default="")
    size_range: Mapped[str] = mapped_column(String(50), default="")  # "1-10", "11-50", etc.
    stage: Mapped[str] = mapped_column(String(50), default="")  # "seed", "series_a", etc.
    founded_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    headquarters: Mapped[str] = mapped_column(String(255), default="")

    # Radar
    hiring_score: Mapped[float] = mapped_column(Float, default=0.0)
    job_velocity: Mapped[float] = mapped_column(Float, default=0.0)
    is_watched: Mapped[bool] = mapped_column(Boolean, default=False)

    # Funding
    total_funding_usd: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_funding_round: Mapped[str] = mapped_column(String(100), default="")
    last_funding_amount_usd: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Metadata
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)

    # Relations
    signals: Mapped[list["CompanySignal"]] = relationship(
        "CompanySignal", back_populates="company", cascade="all, delete-orphan"
    )
