from __future__ import annotations

import re
from typing import Any

# Pre-compiled high-efficiency zero-trust regex patterns
_EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
)
_PHONE_PATTERN = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
)
_SSN_PATTERN = re.compile(
    r"\b(?!000|666|9\d{2})\d{3}[- ](?!00)\d{2}[- ](?!0000)\d{4}\b"
)
_CREDIT_CARD_PATTERN = re.compile(
    r"\b(?:\d{4}[- ]?){3}\d{4}\b"
)
_IPV4_PATTERN = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
)


def scrub_pii(text: str) -> tuple[str, dict[str, str]]:
    """Replaces sensitive PII entities with reversible cryptographic-style surrogates.

    Returns:
        scrubbed_text: sanitized text safe for external LLM transmission.
        surrogate_map: dictionary mapping surrogate tokens back to original values.
    """
    if not text:
        return text, {}

    surrogate_map: dict[str, str] = {}
    email_c = 0
    phone_c = 0
    ssn_c = 0
    card_c = 0
    ip_c = 0

    def _replace_email(match: re.Match) -> str:
        nonlocal email_c
        email_c += 1
        token = f"[EMAIL_{email_c}]"
        surrogate_map[token] = match.group(0)
        return token

    def _replace_phone(match: re.Match) -> str:
        nonlocal phone_c
        phone_c += 1
        token = f"[PHONE_{phone_c}]"
        surrogate_map[token] = match.group(0)
        return token

    def _replace_ssn(match: re.Match) -> str:
        nonlocal ssn_c
        ssn_c += 1
        token = f"[SSN_{ssn_c}]"
        surrogate_map[token] = match.group(0)
        return token

    def _replace_card(match: re.Match) -> str:
        nonlocal card_c
        card_c += 1
        token = f"[CARD_{card_c}]"
        surrogate_map[token] = match.group(0)
        return token

    def _replace_ip(match: re.Match) -> str:
        nonlocal ip_c
        ip_c += 1
        token = f"[IP_{ip_c}]"
        surrogate_map[token] = match.group(0)
        return token

    scrubbed = _SSN_PATTERN.sub(_replace_ssn, text)
    scrubbed = _CREDIT_CARD_PATTERN.sub(_replace_card, scrubbed)
    scrubbed = _EMAIL_PATTERN.sub(_replace_email, scrubbed)
    scrubbed = _PHONE_PATTERN.sub(_replace_phone, scrubbed)
    scrubbed = _IPV4_PATTERN.sub(_replace_ip, scrubbed)

    return scrubbed, surrogate_map


def restore_pii(text: str, surrogate_map: dict[str, str]) -> str:
    """Restores scrubbed tokens with their original values."""
    if not text or not surrogate_map:
        return text

    restored = text
    for token, original in surrogate_map.items():
        restored = restored.replace(token, original)
    return restored


def mask_pii_for_logs(text: str) -> str:
    """Irreversible redaction for audit logs and application metrics."""
    if not text:
        return text
    scrubbed = _SSN_PATTERN.sub("[SSN_REDACTED]", text)
    scrubbed = _CREDIT_CARD_PATTERN.sub("[CARD_REDACTED]", scrubbed)
    scrubbed = _EMAIL_PATTERN.sub("[EMAIL_REDACTED]", scrubbed)
    scrubbed = _PHONE_PATTERN.sub("[PHONE_REDACTED]", scrubbed)
    scrubbed = _IPV4_PATTERN.sub("[IP_REDACTED]", scrubbed)
    return scrubbed
