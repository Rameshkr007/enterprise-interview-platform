from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import structlog
from pydantic import BaseModel, Field
from sqlalchemy import String, Text, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSON, UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
from fastapi import APIRouter, Depends, Response
from typing import Annotated

from app.core.dependencies import CurrentUser
from app.database import Base, get_db
from app.core.exceptions import NotFoundException

log = structlog.get_logger(__name__)


from app.models.job_tracker import JobApplication, JobStatus


# ── Pydantic schemas ──────────────────────────────────────────────────────────
class JobApplicationCreate(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255)
    role_title: str = Field(..., min_length=1, max_length=512)
    job_url: str | None = None
    status: str = "wishlist"
    salary_min: int | None = None
    salary_max: int | None = None
    location: str | None = None
    is_remote: bool = False
    contact_name: str | None = None
    contact_email: str | None = None
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)
    priority: int = Field(default=2, ge=1, le=3)
    follow_up_at: datetime | None = None


class JobApplicationUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    follow_up_at: datetime | None = None
    tags: list[str] | None = None
    priority: int | None = Field(default=None, ge=1, le=3)


STATUS_ORDER = ["wishlist", "applied", "phone_screen", "technical", "final_round", "offer", "rejected", "withdrawn"]

router = APIRouter(prefix="/job-tracker", tags=["Job Tracker"])


@router.get("", response_model=dict)
async def list_applications(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Return job applications grouped by status (Kanban columns)."""
    from sqlalchemy import select
    result = await db.execute(
        select(JobApplication)
        .where(JobApplication.user_id == current_user.id)
        .order_by(JobApplication.priority, JobApplication.updated_at.desc())
    )
    apps = list(result.scalars().all())

    kanban: dict[str, list] = {status: [] for status in STATUS_ORDER}
    stats = {"total": len(apps), "active": 0, "offers": 0, "rejections": 0}

    for app in apps:
        col = kanban.get(app.status, kanban["wishlist"])
        col.append({
            "id": str(app.id),
            "company_name": app.company_name,
            "role_title": app.role_title,
            "status": app.status,
            "location": app.location,
            "is_remote": app.is_remote,
            "salary_range": f"${app.salary_min:,}–${app.salary_max:,}" if app.salary_min and app.salary_max else None,
            "tags": app.tags,
            "priority": app.priority,
            "contact_name": app.contact_name,
            "notes": app.notes,
            "follow_up_at": app.follow_up_at.isoformat() if app.follow_up_at else None,
            "applied_at": app.applied_at.isoformat() if app.applied_at else None,
            "timeline": app.timeline,
            "job_url": app.job_url,
        })
        if app.status not in ("wishlist", "rejected", "withdrawn"):
            stats["active"] += 1
        if app.status == "offer":
            stats["offers"] += 1
        if app.status == "rejected":
            stats["rejections"] += 1

    return {"kanban": kanban, "stats": stats}


@router.post("", status_code=201, response_model=dict)
async def create_application(
    body: JobApplicationCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    now = datetime.now(UTC)
    app_obj = JobApplication(
        user_id=current_user.id,
        company_name=body.company_name,
        role_title=body.role_title,
        job_url=body.job_url,
        status=body.status,
        salary_min=body.salary_min,
        salary_max=body.salary_max,
        location=body.location,
        is_remote=body.is_remote,
        contact_name=body.contact_name,
        contact_email=body.contact_email,
        notes=body.notes,
        tags=body.tags,
        priority=body.priority,
        follow_up_at=body.follow_up_at,
        applied_at=now if body.status == "applied" else None,
        timeline=[{"status": body.status, "timestamp": now.isoformat(), "note": "Created"}],
    )
    db.add(app_obj)
    await db.flush()
    await db.refresh(app_obj)
    log.info("job_application_created", id=str(app_obj.id), company=body.company_name)
    return {"id": str(app_obj.id), "company_name": app_obj.company_name, "status": app_obj.status}


@router.patch("/{app_id}", response_model=dict)
async def update_application(
    app_id: UUID,
    body: JobApplicationUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    app_obj = await db.get(JobApplication, app_id)
    if app_obj is None or app_obj.user_id != current_user.id:
        raise NotFoundException("Application not found")

    now = datetime.now(UTC)
    if body.status and body.status != app_obj.status:
        timeline = list(app_obj.timeline or [])
        timeline.append({"status": body.status, "timestamp": now.isoformat(), "previous": app_obj.status})
        app_obj.timeline = timeline
        if body.status == "applied":
            app_obj.applied_at = now
        app_obj.status = body.status

    if body.notes is not None:
        app_obj.notes = body.notes
    if body.contact_name is not None:
        app_obj.contact_name = body.contact_name
    if body.contact_email is not None:
        app_obj.contact_email = body.contact_email
    if body.salary_min is not None:
        app_obj.salary_min = body.salary_min
    if body.salary_max is not None:
        app_obj.salary_max = body.salary_max
    if body.follow_up_at is not None:
        app_obj.follow_up_at = body.follow_up_at
    if body.tags is not None:
        app_obj.tags = body.tags
    if body.priority is not None:
        app_obj.priority = body.priority

    app_obj.updated_at = now
    db.add(app_obj)
    await db.flush()
    return {"id": str(app_obj.id), "status": app_obj.status, "updated": True}


@router.delete("/{app_id}", status_code=204, response_class=Response)
async def delete_application(
    app_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    app_obj = await db.get(JobApplication, app_id)
    if app_obj is None or app_obj.user_id != current_user.id:
        raise NotFoundException("Application not found")
    await db.delete(app_obj)
    return Response(status_code=204)
