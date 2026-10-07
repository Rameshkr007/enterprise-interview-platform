from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.core.exceptions import NotFoundException
from app.database import get_db
from app.models.session_report import SessionReport
from app.schemas.report import ReportResponse
from app.services.llm_service import LLMService
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/generate/{session_id}", response_model=ReportResponse, status_code=201)
async def generate_report(
    session_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionReport:
    svc = ReportService(db=db, llm_svc=LLMService())
    return await svc.generate_report(session_id)


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionReport:
    result = await db.execute(
        select(SessionReport).where(
            SessionReport.id == report_id,
            SessionReport.user_id == current_user.id,
        )
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise NotFoundException("Report not found")
    return report


@router.get("/session/{session_id}", response_model=ReportResponse)
async def get_report_by_session(
    session_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionReport:
    result = await db.execute(
        select(SessionReport).where(
            SessionReport.session_id == session_id,
            SessionReport.user_id == current_user.id,
        )
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise NotFoundException("Report not found for this session")
    return report
