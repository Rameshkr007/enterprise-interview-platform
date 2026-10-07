from __future__ import annotations

from collections import defaultdict
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.core.exceptions import NotFoundException
from app.database import get_db
from app.models.resume import CandidateSkill, Resume
from app.schemas.resume_intelligence import (
    CandidateSkillProfileResponse,
    CandidateSkillSchema,
    ParsedResumeDetailResponse,
    ResumeChunkSchema,
    ResumeSectionSchema,
    ResumeUploadResponse,
)
from app.services.resume_intelligence_service import ResumeIntelligenceService

router = APIRouter(prefix="/resumes", tags=["Resume Intelligence & Parsing"])


@router.post("/upload", response_model=ResumeUploadResponse, status_code=201)
async def upload_and_process_resume(
    current_user: CurrentUser,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
) -> ResumeUploadResponse:
    content = await file.read()
    file_name = file.filename or "resume.pdf"

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    service = ResumeIntelligenceService(db=db)
    resume = await service.process_and_index_resume(
        user_id=current_user.id,
        file_bytes=content,
        file_name=file_name,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return ResumeUploadResponse(
        resume_id=resume.id,
        file_name=resume.file_name,
        word_count=resume.metadata_.get("word_count", 0),
        section_count=len(resume.sections),
        chunk_count=len(resume.chunks),
        skill_count=len(resume.skills),
        status="completed",
    )


@router.get("/me", response_model=list[ResumeUploadResponse])
async def list_my_resumes(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ResumeUploadResponse]:
    result = await db.execute(
        select(Resume)
        .where(Resume.user_id == current_user.id)
        .order_by(Resume.created_at.desc())
    )
    resumes = result.scalars().all()
    return [
        ResumeUploadResponse(
            resume_id=r.id,
            file_name=r.file_name,
            word_count=r.metadata_.get("word_count", 0),
            section_count=len(r.sections),
            chunk_count=len(r.chunks),
            skill_count=len(r.skills),
            status=r.parsing_status,
        )
        for r in resumes
    ]


@router.get("/{resume_id}", response_model=ParsedResumeDetailResponse)
async def get_resume_detail(
    resume_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Resume:
    service = ResumeIntelligenceService(db=db)
    return await service.get_resume_detail(resume_id, current_user.id)


@router.get("/{resume_id}/skills", response_model=CandidateSkillProfileResponse)
async def get_resume_skills(
    resume_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CandidateSkillProfileResponse:
    service = ResumeIntelligenceService(db=db)
    skills = await service.get_candidate_skills(resume_id, current_user.id)

    by_category: dict[str, list[CandidateSkillSchema]] = defaultdict(list)
    for sk in skills:
        schema_item = CandidateSkillSchema.model_validate(sk)
        by_category[sk.category].append(schema_item)

    top_skills = [CandidateSkillSchema.model_validate(sk) for sk in skills[:10]]

    return CandidateSkillProfileResponse(
        resume_id=resume_id,
        user_id=current_user.id,
        total_skills=len(skills),
        skills_by_category=dict(by_category),
        top_skills=top_skills,
    )


@router.get("/{resume_id}/chunks", response_model=list[ResumeChunkSchema])
async def get_resume_chunks(
    resume_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ResumeChunkSchema]:
    service = ResumeIntelligenceService(db=db)
    chunks = await service.get_resume_chunks(resume_id, current_user.id)
    return [ResumeChunkSchema.model_validate(c) for c in chunks]
