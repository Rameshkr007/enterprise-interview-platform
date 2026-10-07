from __future__ import annotations

import base64
import hashlib
import hmac
import re
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.pii_vault import PiiVaultEntry
from app.models.user import User

log = structlog.get_logger(__name__)
settings = get_settings()

# Key derivation for Fernet from platform secret
_KEY_BYTES = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
_FERNET_KEY = base64.urlsafe_b64encode(_KEY_BYTES)
_CIPHER = Fernet(_FERNET_KEY)

# Regex detectors for common high-risk PII
_PATTERNS: dict[str, re.Pattern] = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"),
    "phone": re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "ssn": re.compile(r"\b(?!000|666|9\d{2})\d{3}[- ](?!00)\d{2}[- ](?!0000)\d{4}\b"),
    "card": re.compile(r"\b(?:\d{4}[- ]?){3}\d{4}\b"),
    "ipv4": re.compile(
        r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
    ),
    "address": re.compile(
        r"\b\d{1,5}\s+[A-Za-z0-9\s.,]+(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Lane|Ln|Court|Ct|Way)\b",
        re.IGNORECASE,
    ),
}


class PiiVaultService:
    """Enterprise zero-trust reversible PII tokenization and encrypted vault."""

    def __init__(self) -> None:
        self._cipher = _CIPHER
        self._secret_bytes = settings.SECRET_KEY.encode()

    def _compute_digest(self, raw_val: str) -> str:
        return hmac.new(self._secret_bytes, raw_val.strip().lower().encode(), hashlib.sha256).hexdigest()

    def _encrypt(self, raw_val: str) -> str:
        return self._cipher.encrypt(raw_val.encode("utf-8")).decode("utf-8")

    def _decrypt(self, encrypted_val: str) -> str:
        return self._cipher.decrypt(encrypted_val.encode("utf-8")).decode("utf-8")

    async def sanitize_text(
        self,
        db: AsyncSession,
        text: str,
        user_id: UUID | None = None,
        entity_types: list[str] | None = None,
        reversible: bool = True,
    ) -> dict[str, Any]:
        """Detects PII, stores encrypted entries in PiiVaultEntry if reversible, and replaces with surrogate tokens."""
        if not text:
            return {
                "sanitized_text": "",
                "entities_found_count": 0,
                "entities_by_type": {},
                "surrogate_tokens": [],
                "reversible": reversible,
            }

        types_to_check = entity_types or list(_PATTERNS.keys())
        sanitized = text
        surrogate_tokens: list[str] = []
        counts_by_type: dict[str, int] = {}
        total_found = 0

        # Collect matches across all selected entity types
        for ent_type in types_to_check:
            pat = _PATTERNS.get(ent_type)
            if not pat:
                continue

            matches = list(pat.finditer(sanitized))
            if not matches:
                continue

            counts_by_type[ent_type] = len(matches)
            total_found += len(matches)

            for match in matches:
                original_val = match.group(0)
                digest = self._compute_digest(original_val)
                token = f"[SURR_{ent_type.upper()}_{digest[:8]}]"

                if reversible:
                    # Check if token exists in DB to avoid duplicate insertion
                    q = select(PiiVaultEntry).where(PiiVaultEntry.surrogate_token == token)
                    res = await db.execute(q)
                    existing = res.scalar_one_or_none()

                    if existing is None:
                        encrypted = self._encrypt(original_val)
                        vault_entry = PiiVaultEntry(
                            surrogate_token=token,
                            entity_type=ent_type,
                            encrypted_value=encrypted,
                            hmac_digest=digest,
                            user_id=user_id,
                        )
                        db.add(vault_entry)

                if token not in surrogate_tokens:
                    surrogate_tokens.append(token)

                sanitized = sanitized.replace(original_val, token)

        if reversible and total_found > 0:
            await db.flush()

        log.info(
            "pii_sanitized",
            total_found=total_found,
            reversible=reversible,
            types=counts_by_type,
        )

        return {
            "sanitized_text": sanitized,
            "entities_found_count": total_found,
            "entities_by_type": counts_by_type,
            "surrogate_tokens": surrogate_tokens,
            "reversible": reversible,
        }

    async def reveal_entities(
        self,
        db: AsyncSession,
        surrogate_tokens: list[str],
        user: User,
        justification: str,
    ) -> dict[str, Any]:
        """Privileged de-anonymization: looks up and decrypts vault entries, logging tamper-evident audit record."""
        revealed: dict[str, str] = {}
        now = datetime.now(UTC)

        for token in surrogate_tokens:
            q = select(PiiVaultEntry).where(PiiVaultEntry.surrogate_token == token)
            res = await db.execute(q)
            entry = res.scalar_one_or_none()

            if entry:
                try:
                    decrypted = self._decrypt(entry.encrypted_value)
                    revealed[token] = decrypted
                    entry.last_accessed_at = now
                    db.add(entry)
                except Exception as exc:
                    log.error("pii_decrypt_failed", token=token, error=str(exc))
                    revealed[token] = "[DECRYPTION_ERROR]"

        await db.flush()

        # Emit tamper-evident audit log
        from app.services.audit_service import record_audit_event
        await record_audit_event(
            db=db,
            action="security.pii_revealed",
            entity_type="pii_vault",
            user_id=user.id,
            payload={
                "tokens_requested": surrogate_tokens,
                "resolved_count": len(revealed),
                "justification": justification,
                "user_role": user.role.value if hasattr(user.role, "value") else str(user.role),
            },
        )

        log.info(
            "pii_revealed",
            user_id=str(user.id),
            tokens_count=len(surrogate_tokens),
            resolved_count=len(revealed),
        )

        return {
            "revealed_entities": revealed,
            "tokens_resolved_count": len(revealed),
            "justification": justification,
            "revealed_at": now.isoformat(),
        }

    async def get_vault_count(self, db: AsyncSession) -> int:
        from sqlalchemy import func
        res = await db.execute(select(func.count(PiiVaultEntry.id)))
        return res.scalar_one() or 0


# Singleton instance
_pii_vault: PiiVaultService | None = None


def get_pii_vault() -> PiiVaultService:
    global _pii_vault
    if _pii_vault is None:
        _pii_vault = PiiVaultService()
    return _pii_vault
