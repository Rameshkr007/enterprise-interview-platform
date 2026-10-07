from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.core.exceptions import NotFoundException
from app.database import get_db
from app.models.ats_analysis import AtsAnalysis
from app.models.job_description import JobDescription
from app.schemas.ats import (
    AtsAnalysisResult,
    AtsAnalyzeRequest,
    JobDescriptionCreateRequest,
    JobMatchSummaryResponse,
    MultiJobMatchRequest,
)
from app.services.ats_service import AtsService
from app.services.embedding_service import EmbeddingService
from app.services.job_requirement_parser import JobRequirementParser
from app.services.resume_intelligence_service import ResumeIntelligenceService

router = APIRouter(prefix="/ats", tags=["Semantic ATS & Job Matching"])


@router.post("/resume", response_model=dict, status_code=201)
async def upload_resume(
    current_user: CurrentUser,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
) -> dict:
    content = await file.read()
    file_name = file.filename or "resume.pdf"
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    intel_svc = ResumeIntelligenceService(db=db)
    resume = await intel_svc.process_and_index_resume(
        user_id=current_user.id,
        file_bytes=content,
        file_name=file_name,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return {"resume_id": str(resume.id), "word_count": resume.metadata_.get("word_count", 0)}


@router.post("/job-description", response_model=dict, status_code=201)
async def create_job_description(
    body: JobDescriptionCreateRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    embedding_svc = EmbeddingService()
    embedding = await embedding_svc.embed_text(body.raw_text[:4000])

    parser = JobRequirementParser()
    parsed_jd = parser.parse_job_description(body.raw_text, title=body.title, company=body.company)

    requirements_data = [
        {
            "text": r.requirement_text,
            "category": r.category,
            "is_required": r.is_required,
            "importance": r.importance,
            "skills": r.skills,
        }
        for r in parsed_jd.requirements
    ]

    jd = JobDescription(
        created_by=current_user.id,
        title=body.title,
        company=body.company,
        raw_text=body.raw_text,
        embedding=embedding,
        requirements=requirements_data,
        structured_skills=parsed_jd.all_skills,
        seniority_level=parsed_jd.seniority_level,
        min_years_experience=parsed_jd.min_years_experience,
        education_required=parsed_jd.education_required,
        location_type=parsed_jd.location_type,
    )
    db.add(jd)
    await db.flush()
    await db.refresh(jd)
    return {"jd_id": str(jd.id), "skills_count": len(parsed_jd.all_skills), "requirements_count": len(requirements_data)}


@router.get("/jobs", response_model=list[dict])
async def list_jobs(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> list[dict]:
    result = await db.execute(select(JobDescription).order_by(JobDescription.created_at.desc()).limit(50))
    jobs = result.scalars().all()
    return [
        {
            "id": str(j.id),
            "title": j.title,
            "company": j.company,
            "seniority_level": j.seniority_level,
            "min_years_experience": j.min_years_experience,
            "location_type": j.location_type,
            "skills": j.structured_skills[:8],
            "created_at": j.created_at.isoformat(),
        }
        for j in jobs
    ]


@router.post("/analyze", response_model=AtsAnalysisResult)
async def analyze_ats(
    body: AtsAnalyzeRequest,
    request: Request,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AtsAnalysis:
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    ats_svc = AtsService(db=db)
    return await ats_svc.analyze(
        resume_id=body.resume_id,
        jd_id=body.jd_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )


@router.post("/multi-match", response_model=list[JobMatchSummaryResponse])
async def multi_job_match(
    body: MultiJobMatchRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[JobMatchSummaryResponse]:
    ats_svc = AtsService(db=db)
    analyses = await ats_svc.compare_multiple_jobs(resume_id=body.resume_id, jd_ids=body.jd_ids)

    summaries: list[JobMatchSummaryResponse] = []
    for a in analyses:
        jd = await db.get(JobDescription, a.jd_id)
        if not jd:
            continue

        strengths = [m["skill_name"] for m in a.matched_skills if m.get("match_type") == "explicit_match"][:5]
        gaps = [g["skill_name"] for g in a.skill_gaps if g.get("is_required")][:5]

        summaries.append(
            JobMatchSummaryResponse(
                jd_id=a.jd_id,
                title=jd.title,
                company=jd.company,
                overall_score=a.overall_score,
                recommendation=a.recommendation,
                match_tier=a.match_tier,
                technical_score=a.technical_score,
                seniority_fit=a.seniority_fit,
                critical_gaps=gaps,
                key_strengths=strengths,
            )
        )

    return summaries


@router.get("/analysis/{analysis_id}", response_model=AtsAnalysisResult)
async def get_analysis(
    analysis_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AtsAnalysis:
    result = await db.get(AtsAnalysis, analysis_id)
    if result is None:
        raise NotFoundException("ATS analysis not found")
    return result
