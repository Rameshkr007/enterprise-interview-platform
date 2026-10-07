from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ResumeSectionSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    resume_id: UUID
    section_type: str
    heading: str
    content: str
    sequence_order: int
    created_at: datetime


class ResumeChunkSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    resume_id: UUID
    section_id: UUID | None
    chunk_index: int
    chunk_text: str
    token_count: int
    metadata_: dict = Field(default_factory=dict)
    created_at: datetime


class CandidateSkillSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    resume_id: UUID
    user_id: UUID
    skill_name: str
    normalized_name: str
    category: str
    confidence: float
    years_experience: float | None = None
    proficiency_level: str
    evidence_text: str
    created_at: datetime


class ResumeUploadResponse(BaseModel):
    resume_id: UUID
    file_name: str
    word_count: int
    section_count: int
    chunk_count: int
    skill_count: int
    status: str


class ParsedResumeDetailResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID
    file_name: str
    s3_key: str
    parsed_text: str
    structured_data: dict
    parsing_status: str
    created_at: datetime
    sections: list[ResumeSectionSchema] = Field(default_factory=list)
    chunks: list[ResumeChunkSchema] = Field(default_factory=list)
    skills: list[CandidateSkillSchema] = Field(default_factory=list)


class CandidateSkillProfileResponse(BaseModel):
    resume_id: UUID
    user_id: UUID
    total_skills: int
    skills_by_category: dict[str, list[CandidateSkillSchema]]
    top_skills: list[CandidateSkillSchema]
