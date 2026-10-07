from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from app.config import get_settings
from app.database import Base
from app.models.vector_type import CompatibleVector
from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

settings = get_settings()


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    created_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(
        CompatibleVector(settings.OPENAI_EMBEDDING_DIMENSIONS), nullable=False
    )
    structured_skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    requirements: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    seniority_level: Mapped[str] = mapped_column(String(50), nullable=False, default="mid")
    min_years_experience: Mapped[float | None] = mapped_column(Float, nullable=True, default=0.0)
    education_required: Mapped[str | None] = mapped_column(String(100), nullable=True, default="Bachelor")
    location_type: Mapped[str] = mapped_column(String(50), nullable=False, default="remote")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    ats_analyses: Mapped[list["AtsAnalysis"]] = relationship(back_populates="job_description", lazy="noload")  # noqa: F821
