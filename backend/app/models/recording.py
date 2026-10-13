from __future__ import annotations

import enum
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RecordingStatus(str, enum.Enum):
    recording = "recording"
    completed = "completed"
    failed = "failed"
    deleted = "deleted"


class InterviewRecording(Base):
    __tablename__ = "interview_recordings"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=RecordingStatus.recording.value)
    media_type: Mapped[str] = mapped_column(String(50), nullable=False, default="video_audio")
    consent_given: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    total_duration_s: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    s3_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    segments: Mapped[list["RecordingSegment"]] = relationship(
        back_populates="recording",
        lazy="noload",
        cascade="all, delete-orphan",
        order_by="RecordingSegment.segment_index",
    )


class RecordingSegment(Base):
    __tablename__ = "recording_segments"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    recording_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("interview_recordings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    segment_index: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_s: Mapped[float] = mapped_column(Float, nullable=False, default=10.0)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    s3_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="uploaded")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    recording: Mapped["InterviewRecording"] = relationship(
        back_populates="segments", lazy="noload"
    )
