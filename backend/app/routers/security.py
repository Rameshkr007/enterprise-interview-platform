from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, RequireRole
from app.core.exceptions import PermissionDeniedException
from app.database import get_db
from app.middleware.rate_limiter import (
    get_client_rate_status,
    get_rate_limiter_overview,
    reset_rate_limit,
)
from app.models.user import UserRole
from app.schemas.security import (
    AuditLedgerEntry,
    AuditLedgerListResponse,
    AuditLedgerVerificationResponse,
    PiiRevealRequest,
    PiiRevealResponse,
    PiiSanitizeRequest,
    PiiSanitizeResponse,
    PromptGuardScanRequest,
    PromptGuardScanResponse,
    RateLimitResetRequest,
    RateLimitResetResponse,
    RateLimitStatusResponse,
    SecurityPostureResponse,
)
from app.services.audit_service import AuditService
from app.services.pii_vault_service import get_pii_vault
from app.services.prompt_guard_service import get_prompt_guard

router = APIRouter(prefix="/security", tags=["Security & Rate Limiting"])

ELEVATED_ROLES = [
    UserRole.recruiter.value,
    "org_admin",
    "platform_admin",
    UserRole.admin.value,
]


@router.get("/posture", response_model=SecurityPostureResponse)
async def get_security_posture(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SecurityPostureResponse:
    """Provides a high-level operational security posture audit."""
    audit_svc = AuditService(db)
    audit_status = await audit_svc.verify_integrity()
    pii_vault = get_pii_vault()
    vault_count = await pii_vault.get_vault_count(db)
    prompt_guard = get_prompt_guard()
    pg_stats = prompt_guard.get_stats()
    rate_limiter_stats = get_rate_limiter_overview()

    return SecurityPostureResponse(
        status="HARDENED",
        timestamp=datetime.now(UTC).isoformat(),
        audit_ledger={
            "is_valid": audit_status.get("is_valid", True),
            "total_entries": audit_status.get("total_entries", 0),
            "head_hash": audit_status.get("head_hash", "0" * 64),
        },
        rate_limiting=rate_limiter_stats,
        pii_vault={
            "vault_entries_count": vault_count,
            "supported_entities": ["email", "phone", "ssn", "card", "ipv4", "address"],
            "encryption_algorithm": "Fernet / AES-CBC + HMAC-SHA256",
        },
        prompt_guard=pg_stats,
        security_headers={
            "hsts_enabled": True,
            "csp_enabled": True,
            "x_frame_options": "DENY",
            "x_content_type_options": "nosniff",
            "permissions_policy": "microphone=(self), camera=(), geolocation=()",
        },
    )


@router.post("/audit/verify", response_model=AuditLedgerVerificationResponse)
async def verify_audit_ledger(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuditLedgerVerificationResponse:
    """Executes cryptographic SHA-256 verification of the tamper-evident audit ledger chain."""
    start = time.perf_counter()
    audit_svc = AuditService(db)
    result = await audit_svc.verify_integrity()
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

    return AuditLedgerVerificationResponse(
        is_valid=result.get("is_valid", False),
        total_entries=result.get("total_entries", 0),
        head_hash=result.get("head_hash", "0" * 64),
        broken_at_entry_id=result.get("broken_at_entry_id"),
        sequence=result.get("sequence"),
        reason=result.get("reason"),
        verification_time_ms=elapsed_ms,
        message=result.get("message", "Audit ledger verified successfully."),
    )


@router.get("/audit/ledger", response_model=AuditLedgerListResponse)
async def get_audit_ledger(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> AuditLedgerListResponse:
    """Retrieves recent cryptographic ledger blocks."""
    audit_svc = AuditService(db)
    blocks = await audit_svc.get_ledger(limit=limit)
    entries = [AuditLedgerEntry(**b) for b in blocks]
    return AuditLedgerListResponse(total_entries=len(entries), entries=entries)


@router.post("/pii/sanitize", response_model=PiiSanitizeResponse)
async def sanitize_pii(
    body: PiiSanitizeRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PiiSanitizeResponse:
    """Scans and masks sensitive PII entities, generating reversible cryptographic surrogates."""
    vault = get_pii_vault()
    result = await vault.sanitize_text(
        db=db,
        text=body.text,
        user_id=current_user.id,
        entity_types=body.entity_types,
        reversible=body.reversible,
    )
    return PiiSanitizeResponse(**result)


@router.post("/pii/reveal", response_model=PiiRevealResponse)
async def reveal_pii(
    body: PiiRevealRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PiiRevealResponse:
    """Privileged de-anonymization of surrogate tokens (Strict RBAC: Recruiter / Org Admin / Admin)."""
    user_role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if user_role not in ELEVATED_ROLES:
        raise PermissionDeniedException("Privileged role required to de-anonymize vault PII entities.")

    vault = get_pii_vault()
    result = await vault.reveal_entities(
        db=db,
        surrogate_tokens=body.surrogate_tokens,
        user=current_user,
        justification=body.justification,
    )
    return PiiRevealResponse(**result)


@router.post("/prompt-guard/inspect", response_model=PromptGuardScanResponse)
async def inspect_prompt(
    body: PromptGuardScanRequest,
    current_user: CurrentUser,
) -> PromptGuardScanResponse:
    """Inspects text for prompt injection, jailbreaks, and delimiter smuggling."""
    guard = get_prompt_guard()
    result = guard.scan_prompt(body.prompt_text, body.context_type)
    return PromptGuardScanResponse(**result)


@router.get("/rate-limits/status", response_model=RateLimitStatusResponse)
async def get_rate_limit_status(
    current_user: CurrentUser,
    client_key: Annotated[str | None, Query()] = None,
) -> RateLimitStatusResponse:
    """Checks sliding window rate limiter quota and remaining tokens."""
    target_key = client_key or f"user:{current_user.id}"
    user_role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    limit = 600 if user_role in ("admin", "platform_admin") else 300 if user_role in ("recruiter", "org_admin") else 120

    status = await get_client_rate_status(target_key, limit=limit)
    return RateLimitStatusResponse(**status)


@router.post(
    "/rate-limits/reset",
    response_model=RateLimitResetResponse,
    dependencies=[Depends(RequireRole(["admin", "platform_admin"]))],
)
async def reset_client_rate_limit(
    body: RateLimitResetRequest,
    current_user: CurrentUser,
) -> RateLimitResetResponse:
    """Admin endpoint to reset rate limiter bucket for a given client key."""
    cleared = await reset_rate_limit(body.client_key)
    return RateLimitResetResponse(
        message=f"Rate limit bucket for '{body.client_key}' reset successfully.",
        client_key=body.client_key,
        cleared=cleared,
    )
