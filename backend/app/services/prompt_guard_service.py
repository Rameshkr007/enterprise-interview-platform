from __future__ import annotations

import re
import threading
from typing import Any

import structlog

log = structlog.get_logger(__name__)


# ── Canonical Prompt Guard Heuristics & Signatures ───────────────────────────
PROMPT_RULES: list[dict[str, Any]] = [
    {
        "rule_id": "PR-001",
        "category": "instruction_override",
        "severity": "critical",
        "weight": 0.55,
        "pattern": re.compile(
            r"\b(ignore|disregard|forget|bypass|override|drop)\s+(all\s+)?(previous|prior|above|system)\s+(instructions|prompts?|rules?|directives?)\b",
            re.IGNORECASE,
        ),
        "description": "Attempt to override or negate system directives",
    },
    {
        "rule_id": "PR-002",
        "category": "instruction_override",
        "severity": "high",
        "weight": 0.40,
        "pattern": re.compile(
            r"\b(from\s+now\s+on\s+you\s+(are|will)|you\s+must\s+now\s+act\s+as|new\s+operating\s+instructions?)\b",
            re.IGNORECASE,
        ),
        "description": "Persona hijacking or unauthorized operating instruction declaration",
    },
    {
        "rule_id": "PR-003",
        "category": "jailbreak_roleplay",
        "severity": "critical",
        "weight": 0.60,
        "pattern": re.compile(
            r"\b(dan\s+mode|do\s+anything\s+now|jailbreak(\s+mode)?|developer\s+mode\s+enabled|uncensored\s+mode)\b",
            re.IGNORECASE,
        ),
        "description": "Known jailbreak persona signature (DAN / Developer Mode)",
    },
    {
        "rule_id": "PR-004",
        "category": "jailbreak_roleplay",
        "severity": "high",
        "weight": 0.40,
        "pattern": re.compile(
            r"\b(pretend\s+you\s+have\s+no\s+(rules|ethics|filters|limits)|simulate\s+an\s+unfiltered\s+ai)\b",
            re.IGNORECASE,
        ),
        "description": "Filter circumvention via hypothetical unconstrained persona",
    },
    {
        "rule_id": "PR-005",
        "category": "delimiter_smuggling",
        "severity": "critical",
        "weight": 0.50,
        "pattern": re.compile(
            r"(<\|im_start\|>|<\|im_end\|>|<\|system\|>|\[SYSTEM\]|\[INST\]|\[\/INST\]|```json\s*\{\s*\"role\"\s*:\s*\"system\")",
            re.IGNORECASE,
        ),
        "description": "ChatML, Llama, or OpenAI special delimiter injection",
    },
    {
        "rule_id": "PR-006",
        "category": "delimiter_smuggling",
        "severity": "medium",
        "weight": 0.30,
        "pattern": re.compile(
            r"\b(Assistant:\s*|System:\s*|Human:\s*|User:\s*)\s*(\n|\r)",
            re.IGNORECASE,
        ),
        "description": "Turn-boundary delimiter injection mimicking conversational roles",
    },
    {
        "rule_id": "PR-007",
        "category": "system_leakage",
        "severity": "high",
        "weight": 0.45,
        "pattern": re.compile(
            r"\b(print|reveal|output|display|show|dump|repeat|export)\s+(your\s+)?(system\s+prompt|initial\s+instructions?|core\s+prompt|hidden\s+rules?|developer\s+prompt)\b",
            re.IGNORECASE,
        ),
        "description": "Attempted exfiltration of private system instructions",
    },
    {
        "rule_id": "PR-008",
        "category": "system_leakage",
        "severity": "critical",
        "weight": 0.55,
        "pattern": re.compile(
            r"\b(output\s+all\s+text\s+above|repeat\s+everything\s+prior\s+to\s+this|what\s+are\s+your\s+secret\s+instructions)\b",
            re.IGNORECASE,
        ),
        "description": "Exfiltration of system initialization context",
    },
]


class PromptGuardService:
    """Enterprise AI firewall inspecting candidate inputs for prompt injection & jailbreak attacks."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._total_scans = 0
        self._threats_blocked = 0
        self._threats_by_category: dict[str, int] = {
            "instruction_override": 0,
            "jailbreak_roleplay": 0,
            "delimiter_smuggling": 0,
            "system_leakage": 0,
        }

    def scan_prompt(self, text: str, context_type: str = "candidate_response") -> dict[str, Any]:
        """Inspects text against known injection signatures and returns risk metrics."""
        with self._lock:
            self._total_scans += 1

        detected_patterns: list[dict[str, Any]] = []
        accumulated_weight = 0.0

        for rule in PROMPT_RULES:
            match = rule["pattern"].search(text)
            if match:
                detected = {
                    "rule_id": rule["rule_id"],
                    "severity": rule["severity"],
                    "category": rule["category"],
                    "matched_substring": match.group(0),
                    "description": rule["description"],
                }
                detected_patterns.append(detected)
                accumulated_weight += rule["weight"]

        risk_score = round(min(accumulated_weight, 1.0), 3)

        if risk_score >= 0.70:
            threat_level = "blocked"
            is_safe = False
        elif risk_score >= 0.30:
            threat_level = "suspicious"
            is_safe = True  # allowed but flagged
        else:
            threat_level = "safe"
            is_safe = True

        if threat_level == "blocked":
            with self._lock:
                self._threats_blocked += 1
                for pat in detected_patterns:
                    cat = pat["category"]
                    self._threats_by_category[cat] = self._threats_by_category.get(cat, 0) + 1
            log.warning(
                "prompt_injection_blocked",
                context=context_type,
                risk_score=risk_score,
                patterns=[p["rule_id"] for p in detected_patterns],
            )

        sanitized_text = self._sanitize(text, detected_patterns)

        details = (
            f"Prompt scanned clean with risk score {risk_score}."
            if is_safe and threat_level == "safe"
            else f"Threat level: {threat_level.upper()} ({len(detected_patterns)} patterns detected, score: {risk_score})."
        )

        return {
            "threat_level": threat_level,
            "risk_score": risk_score,
            "is_safe": is_safe,
            "detected_patterns": detected_patterns,
            "sanitized_text": sanitized_text,
            "details": details,
        }

    def _sanitize(self, text: str, detected_patterns: list[dict[str, Any]]) -> str:
        """Neutralizes matched injection substrings."""
        if not detected_patterns:
            return text

        clean = text
        for pat in detected_patterns:
            match_str = pat["matched_substring"]
            clean = clean.replace(match_str, f"[DEFUSED:{pat['category'].upper()}]")
        return clean

    def get_stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "firewall_status": "ACTIVE",
                "rules_loaded_count": len(PROMPT_RULES),
                "total_scans": self._total_scans,
                "total_threats_blocked": self._threats_blocked,
                "threats_by_category": dict(self._threats_by_category),
            }


# Singleton instance
_prompt_guard: PromptGuardService | None = None


def get_prompt_guard() -> PromptGuardService:
    global _prompt_guard
    if _prompt_guard is None:
        _prompt_guard = PromptGuardService()
    return _prompt_guard
