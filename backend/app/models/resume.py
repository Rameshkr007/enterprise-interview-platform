from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from app.config import get_settings
from app.database import Base
from app.models.vector_type import CompatibleVector
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

settings = get_settings()


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_name: Mapped[str] = mapped_column(String(512), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    parsed_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(
        CompatibleVector(settings.OPENAI_EMBEDDING_DIMENSIONS), nullable=False
    )
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    structured_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    parsing_status: Mapped[str] = mapped_column(String(50), nullable=False, default="completed")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="resumes", lazy="noload")  # noqa: F821
    ats_analyses: Mapped[list["AtsAnalysis"]] = relationship(back_populates="resume", lazy="noload")  # noqa: F821
    sections: Mapped[list["ResumeSection"]] = relationship(
        back_populates="resume", cascade="all, delete-orphan", lazy="selectin", order_by="ResumeSection.sequence_order"
    )
    chunks: Mapped[list["ResumeChunk"]] = relationship(
        back_populates="resume", cascade="all, delete-orphan", lazy="selectin", order_by="ResumeChunk.chunk_index"
    )
    skills: Mapped[list["CandidateSkill"]] = relationship(
        back_populates="resume", cascade="all, delete-orphan", lazy="selectin"
    )


class ResumeSection(Base):
    __tablename__ = "resume_sections"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    resume_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    heading: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    resume: Mapped["Resume"] = relationship(back_populates="sections")
    chunks: Mapped[list["ResumeChunk"]] = relationship(
        back_populates="section", cascade="all, delete-orphan", lazy="selectin"
    )


class ResumeChunk(Base):
    __tablename__ = "resume_chunks"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    resume_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("resume_sections.id", ondelete="CASCADE"), nullable=True, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    embedding: Mapped[list[float]] = mapped_column(
        CompatibleVector(settings.OPENAI_EMBEDDING_DIMENSIONS), nullable=False
    )
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    resume: Mapped["Resume"] = relationship(back_populates="chunks")
    section: Mapped["ResumeSection | None"] = relationship(back_populates="chunks")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    resume_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="technical")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    years_experience: Mapped[float | None] = mapped_column(Float, nullable=True)
    proficiency_level: Mapped[str] = mapped_column(String(50), nullable=False, default="intermediate")
    evidence_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    resume: Mapped["Resume"] = relationship(back_populates="skills")
