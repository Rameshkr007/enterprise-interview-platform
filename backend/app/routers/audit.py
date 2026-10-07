from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, RequireRole
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import UserRole
from app.services.audit_service import AuditService

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/audit", tags=["Security & Audit Logs"])


@router.get(
    "/verify-integrity",
    response_model=dict[str, Any],
    dependencies=[Depends(RequireRole([UserRole.org_admin, UserRole.platform_admin, UserRole.admin]))],
)
async def verify_audit_log_integrity(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Cryptographically verifies the SHA-256 hash chaining of the audit log sequence to detect tampering."""
    svc = AuditService(db)
    return await svc.verify_integrity(org_id=current_user.org_id)


@router.get(
    "/logs",
    response_model=list[dict[str, Any]],
    dependencies=[Depends(RequireRole([UserRole.org_admin, UserRole.platform_admin, UserRole.admin]))],
)
async def list_audit_logs(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=200),
    action: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    """Returns tamper-evident enterprise audit events for the organization."""
    query = select(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit)
    if current_user.org_id:
        query = query.where(AuditLog.org_id == current_user.org_id)
    if action:
        query = query.where(AuditLog.action == action)

    result = await db.execute(query)
    logs = list(result.scalars().all())

    return [
        {
            "id": str(l.id),
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "user_id": str(l.user_id) if l.user_id else None,
            "org_id": str(l.org_id) if l.org_id else None,
            "ip_address": l.ip_address,
            "created_at": l.created_at.isoformat(),
            "integrity": l.payload.get("_integrity") if isinstance(l.payload, dict) else None,
        }
        for l in logs
    ]
