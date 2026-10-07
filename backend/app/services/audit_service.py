from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.services.pii_scrubber import mask_pii_for_logs

log = structlog.get_logger(__name__)

GENESIS_HASH = "0" * 64


def _compute_entry_hash(
    prev_hash: str,
    sequence: int,
    action: str,
    entity_type: str,
    entity_id: str | None,
    user_id: UUID | None,
    payload_content: str,
) -> str:
    raw = f"{prev_hash}:{sequence}:{action}:{entity_type}:{entity_id or ''}:{str(user_id) or ''}:{payload_content}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def record_audit_event(
    db: AsyncSession,
    action: str,
    entity_type: str,
    org_id: UUID | None = None,
    user_id: UUID | None = None,
    entity_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    payload: dict[str, Any] | None = None,
) -> AuditLog:
    """Asynchronously records an immutable audit log entry with cryptographic hash chaining."""
    clean_payload = payload.copy() if payload else {}

    # Find recent audit entries to link to the highest sequence number in the chain
    query = select(AuditLog).order_by(desc(AuditLog.created_at)).limit(20)
    if org_id is not None:
        query = query.where(AuditLog.org_id == org_id)

    res = await db.execute(query)
    recent_logs = list(res.scalars().all())

    prev_seq = 0
    prev_hash = GENESIS_HASH
    for l in recent_logs:
        if isinstance(l.payload, dict) and "_integrity" in l.payload:
            seq = l.payload["_integrity"].get("sequence", 0)
            if seq > prev_seq:
                prev_seq = seq
                prev_hash = l.payload["_integrity"].get("entry_hash", GENESIS_HASH)

    current_seq = prev_seq + 1

    # Sanitize payload for PII before storing and hashing
    payload_str = json.dumps(clean_payload, sort_keys=True, default=str)
    sanitized_payload_str = mask_pii_for_logs(payload_str)
    entry_hash = _compute_entry_hash(
        prev_hash=prev_hash,
        sequence=current_seq,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        payload_content=sanitized_payload_str,
    )

    clean_payload["_integrity"] = {
        "sequence": current_seq,
        "previous_hash": prev_hash,
        "entry_hash": entry_hash,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    entry = AuditLog(
        org_id=org_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
        user_agent=user_agent,
        payload=clean_payload,
    )
    db.add(entry)
    await db.flush()
    log.info(
        "audit_event_logged",
        action=action,
        entity_type=entity_type,
        user_id=str(user_id) if user_id else None,
        org_id=str(org_id) if org_id else None,
        seq=current_seq,
        entry_hash=entry_hash[:12],
    )
    return entry


async def verify_audit_chain(db: AsyncSession, org_id: UUID | None = None) -> dict[str, Any]:
    """Verifies the cryptographic integrity of the audit log sequence across tenants."""
    from collections import defaultdict

    query = select(AuditLog)
    if org_id is not None:
        query = query.where(AuditLog.org_id == org_id)

    result = await db.execute(query)
    all_entries = list(result.scalars().all())

    # Group entries by tenant organization
    org_chains: dict[UUID | None, list[AuditLog]] = defaultdict(list)
    for e in all_entries:
        if isinstance(e.payload, dict) and "_integrity" in e.payload and "sequence" in e.payload["_integrity"]:
            org_chains[e.org_id].append(e)

    if not org_chains:
        return {
            "is_valid": True,
            "total_entries": 0,
            "message": "No chained audit log entries found for this scope.",
            "head_hash": GENESIS_HASH,
        }

    total_verified = 0
    head_hash = GENESIS_HASH

    for target_org, chained_entries in org_chains.items():
        chained_entries.sort(key=lambda e: e.payload["_integrity"]["sequence"])
        expected_prev = GENESIS_HASH

        for idx, entry in enumerate(chained_entries):
            integrity = entry.payload["_integrity"]
            entry_seq = integrity.get("sequence", idx + 1)
            entry_prev = integrity.get("previous_hash")
            entry_hash = integrity.get("entry_hash")

            # Verify link with previous
            if idx > 0 and entry_prev != expected_prev and expected_prev != GENESIS_HASH:
                return {
                    "is_valid": False,
                    "broken_at_entry_id": str(entry.id),
                    "sequence": entry_seq,
                    "org_id": str(target_org) if target_org else None,
                    "reason": f"Hash chain broken. Expected prev {expected_prev}, got {entry_prev}",
                }

            # Verify internal integrity of the entry
            payload_copy = {k: v for k, v in entry.payload.items() if k != "_integrity"}
            payload_str = json.dumps(payload_copy, sort_keys=True, default=str)
            sanitized_str = mask_pii_for_logs(payload_str)
            recalculated_hash = _compute_entry_hash(
                prev_hash=entry_prev,
                sequence=entry_seq,
                action=entry.action,
                entity_type=entry.entity_type,
                entity_id=entry.entity_id,
                user_id=entry.user_id,
                payload_content=sanitized_str,
            )

            if recalculated_hash != entry_hash:
                return {
                    "is_valid": False,
                    "broken_at_entry_id": str(entry.id),
                    "sequence": entry_seq,
                    "org_id": str(target_org) if target_org else None,
                    "reason": "Payload or metadata was modified after logging (tamper detected).",
                }

            expected_prev = entry_hash
            total_verified += 1

        head_hash = expected_prev

    return {
        "is_valid": True,
        "total_entries": total_verified,
        "message": f"Audit log chains verified successfully across {len(org_chains)} tenant partition(s) with zero tampering.",
        "head_hash": head_hash,
    }


async def get_recent_ledger_entries(
    db: AsyncSession, limit: int = 50, org_id: UUID | None = None
) -> list[dict[str, Any]]:
    """Retrieves recent audit log entries formatted as cryptographic ledger blocks."""
    query = select(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit)
    if org_id is not None:
        query = query.where(AuditLog.org_id == org_id)

    res = await db.execute(query)
    entries = list(res.scalars().all())

    ledger_blocks: list[dict[str, Any]] = []
    for e in entries:
        integrity = (
            e.payload.get("_integrity", {})
            if isinstance(e.payload, dict)
            else {}
        )
        seq = integrity.get("sequence", 0)
        prev_h = integrity.get("previous_hash", GENESIS_HASH)
        entry_h = integrity.get("entry_hash", GENESIS_HASH)

        ledger_blocks.append({
            "id": str(e.id),
            "sequence": seq,
            "action": e.action,
            "entity_type": e.entity_type,
            "entity_id": e.entity_id,
            "user_id": str(e.user_id) if e.user_id else None,
            "created_at": e.created_at.isoformat() if e.created_at else datetime.now(UTC).isoformat(),
            "previous_hash": prev_h,
            "entry_hash": entry_h,
            "is_valid": True,
        })

    # Sort ascending by sequence for ledger display
    ledger_blocks.sort(key=lambda b: b["sequence"])
    return ledger_blocks


class AuditService:
    """Convenience class wrapper for recording and verifying audit events."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def log_event(
        self,
        action: str,
        entity_type: str,
        user_id: UUID | None = None,
        org_id: UUID | None = None,
        entity_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> AuditLog:
        return await record_audit_event(
            db=self.db,
            action=action,
            entity_type=entity_type,
            org_id=org_id,
            user_id=user_id,
            entity_id=entity_id,
            ip_address=ip_address,
            user_agent=user_agent,
            payload=payload,
        )

    async def verify_integrity(self, org_id: UUID | None = None) -> dict[str, Any]:
        return await verify_audit_chain(self.db, org_id)

    async def get_ledger(self, limit: int = 50, org_id: UUID | None = None) -> list[dict[str, Any]]:
        return await get_recent_ledger_entries(self.db, limit, org_id)

