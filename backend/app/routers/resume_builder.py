from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.core.exceptions import NotFoundException
from app.database import get_db
from app.models.resume import Resume
from app.models.ats_analysis import AtsAnalysis
from app.services.resume_builder import ResumeBuilderService
from app.services.llm_service import LLMService
from app.services.tts_service import TTSService
import base64
import structlog

router = APIRouter(prefix="/resume-builder", tags=["Resume Builder"])


class ResumeImprovementRequest(BaseModel):
    resume_id: UUID
    ats_analysis_id: UUID | None = None


class CareerRoadmapRequest(BaseModel):
    resume_id: UUID
    target_role: str = Field(..., min_length=3, max_length=200)
    ats_analysis_id: UUID | None = None
    interview_score: float | None = Field(default=None, ge=0.0, le=100.0)


class TTSSynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4096)
    voice: str = Field(default="nova", pattern="^(alloy|echo|fable|onyx|nova|shimmer)$")


@router.post("/improve", response_model=dict)
async def improve_resume(
    body: ResumeImprovementRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """AI-powered resume rewriter: ATS-optimized bullet points and keyword injection."""
    resume = await db.get(Resume, body.resume_id)
    if resume is None or resume.user_id != current_user.id:
        raise NotFoundException("Resume not found")

    ats_data: dict = {}
    if body.ats_analysis_id:
        ats = await db.get(AtsAnalysis, body.ats_analysis_id)
        if ats:
            ats_data = {
                "overall_score": ats.overall_score,
                "skill_gaps": ats.skill_gaps,
                "matched_skills": ats.matched_skills,
                "section_scores": ats.section_scores,
            }

    svc = ResumeBuilderService(db=db, llm_svc=LLMService())
    return await svc.generate_resume_improvements(resume.parsed_text, ats_data)


@router.post("/career-roadmap", response_model=dict)
async def career_roadmap(
    body: CareerRoadmapRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Personalized career roadmap with learning resources, certs, salary benchmarks."""
    resume = await db.get(Resume, body.resume_id)
    if resume is None or resume.user_id != current_user.id:
        raise NotFoundException("Resume not found")

    skill_gaps: list = []
    if body.ats_analysis_id:
        ats = await db.get(AtsAnalysis, body.ats_analysis_id)
        if ats:
            skill_gaps = ats.skill_gaps or []

    svc = ResumeBuilderService(db=db, llm_svc=LLMService())
    return await svc.generate_career_roadmap(
        resume_text=resume.parsed_text,
        target_role=body.target_role,
        skill_gaps=skill_gaps,
        interview_score=body.interview_score,
    )


log = structlog.get_logger(__name__)


@router.post("/tts/synthesize", response_model=dict)
async def synthesize_speech(
    body: TTSSynthesizeRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Convert question text to speech audio (base64-encoded Opus or graceful browser fallback)."""
    tts = TTSService()
    try:
        audio_bytes = await tts.synthesize(body.text, voice=body.voice)  # type: ignore[arg-type]
        return {
            "audio_b64": base64.b64encode(audio_bytes).decode("utf-8"),
            "format": "opus",
            "voice": body.voice,
            "char_count": len(body.text),
            "use_browser_speech": False,
        }
    except Exception as exc:
        log.warning("openai_tts_unavailable_fallback_to_browser", error=str(exc))
        return {
            "audio_b64": "",
            "format": "none",
            "voice": body.voice,
            "char_count": len(body.text),
            "use_browser_speech": True,
            "message": "OpenAI TTS unavailable; falling back to client-side speech synthesis",
        }
