from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ── PII Sanitization & Vault Schemas ───────────────────────────────────────────
class PiiSanitizeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Input text to scan and redact PII from")
    entity_types: list[str] | None = Field(
        default=None,
        description="Optional subset of entity types to redact (email, phone, ssn, card, ipv4, address)",
    )
    reversible: bool = Field(
        default=True,
        description="Whether to store encrypted surrogates in the PII Vault for reversible recovery",
    )


class PiiSanitizeResponse(BaseModel):
    sanitized_text: str
    entities_found_count: int
    entities_by_type: dict[str, int]
    surrogate_tokens: list[str]
    reversible: bool


class PiiRevealRequest(BaseModel):
    surrogate_tokens: list[str] = Field(..., min_length=1, description="Surrogate tokens to decrypt")
    justification: str = Field(
        ...,
        min_length=10,
        description="Mandatory business reason for revealing sensitive PII (logged in audit chain)",
    )


class PiiRevealResponse(BaseModel):
    revealed_entities: dict[str, str]
    tokens_resolved_count: int
    justification: str
    revealed_at: str


# ── AI Prompt Guard & Injection Defense Schemas ──────────────────────────────
class PromptGuardScanRequest(BaseModel):
    prompt_text: str = Field(..., min_length=1, description="Candidate prompt or submission to inspect")
    context_type: str = Field(
        default="candidate_response",
        description="Context of the prompt (candidate_response, resume_text, code_submission, clarification)",
    )


class DetectedPattern(BaseModel):
    rule_id: str
    severity: str  # low, medium, high, critical
    category: str  # instruction_override, jailbreak_roleplay, delimiter_smuggling, system_leakage, delimiter_escaping
    matched_substring: str
    description: str


class PromptGuardScanResponse(BaseModel):
    threat_level: str  # safe, suspicious, blocked
    risk_score: float = Field(ge=0.0, le=1.0)
    is_safe: bool
    detected_patterns: list[DetectedPattern]
    sanitized_text: str
    details: str


# ── Cryptographic Audit Ledger Schemas ─────────────────────────────────────────
class AuditLedgerEntry(BaseModel):
    id: str
    sequence: int
    action: str
    entity_type: str
    entity_id: str | None = None
    user_id: str | None = None
    created_at: str
    previous_hash: str
    entry_hash: str
    is_valid: bool


class AuditLedgerListResponse(BaseModel):
    total_entries: int
    entries: list[AuditLedgerEntry]


class AuditLedgerVerificationResponse(BaseModel):
    is_valid: bool
    total_entries: int
    head_hash: str
    broken_at_entry_id: str | None = None
    sequence: int | None = None
    reason: str | None = None
    verification_time_ms: float
    message: str


# ── Rate Limiting & Posture Schemas ────────────────────────────────────────────
class RateLimitStatusResponse(BaseModel):
    client_key: str
    limit: int
    remaining: int
    reset_seconds: int
    is_blocked: bool
    route_rules: dict[str, int]


class RateLimitResetRequest(BaseModel):
    client_key: str = Field(..., min_length=1)


class RateLimitResetResponse(BaseModel):
    message: str
    client_key: str
    cleared: bool


class SecurityPostureResponse(BaseModel):
    status: str  # HARDENED | DEGRADED
    timestamp: str
    audit_ledger: dict[str, Any]
    rate_limiting: dict[str, Any]
    pii_vault: dict[str, Any]
    prompt_guard: dict[str, Any]
    security_headers: dict[str, Any]
