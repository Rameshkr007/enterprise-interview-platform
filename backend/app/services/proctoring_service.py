from __future__ import annotations

import asyncio
import base64
from typing import Any
from uuid import UUID

import numpy as np
import structlog

from app.config import get_settings
from app.core.exceptions import InvalidAudioException
from app.services.llm_service import LLMService

log = structlog.get_logger(__name__)
settings = get_settings()

_PROCTORING_SYSTEM_PROMPT = """
You are an AI interview proctoring system analyzing candidate behavior from audio signals.
Based on audio energy patterns and the candidate metrics provided, detect:
1. Distraction indicators (sudden silence after active speech, background noise spikes)
2. Anxiety markers (pitch spikes, rapid speech rate changes)
3. Confidence score (0-1) based on speech consistency
4. Suspicious patterns (overly scripted speech, reading indicators)

Return ONLY valid JSON:
{
  "attention_score": float 0-1,
  "confidence_score": float 0-1,
  "anxiety_level": "low" | "medium" | "high",
  "suspicious_patterns": [str],
  "behavioral_flags": [str],
  "proctoring_pass": bool,
  "notes": str
}
"""


class ProctoringService:
    """
    AI Proctoring: Analyzes audio energy + pitch patterns per turn to detect:
    - Distraction / off-task behavior
    - Reading from notes (unnaturally flat pitch variance)
    - Suspiciously fast/slow speech
    - Background voice detection (energy spikes inconsistent with speaker voice)

    No camera required — fully audio-based proctoring using Librosa metrics.
    """

    # Thresholds
    MIN_ATTENTION_SCORE = 0.5
    READING_PITCH_CV_THRESHOLD = 0.05   # Too-flat pitch = reading from script
    SUSPICIOUS_SILENCE_RATIO = 0.60     # >60% silence = off-task
    MAX_FILLER_RATE = 15.0              # >15 fillers/min = extreme anxiety

    def __init__(self, llm_svc: LLMService) -> None:
        self._llm = llm_svc

    async def analyze_turn(
        self,
        audio_metrics: dict[str, Any],
        session_history: list[dict[str, Any]],
        turn_index: int,
    ) -> dict[str, Any]:
        """
        Analyze a single interview turn for proctoring signals.
        Combines rule-based heuristics with LLM behavioral analysis.
        """
        flags: list[str] = []
        suspicious: list[str] = []

        silence_ratio: float = audio_metrics.get("silence_ratio", 0.0)
        pitch_variance: float = audio_metrics.get("pitch_variance_score", 0.5)
        filler_rate: float = audio_metrics.get("filler_word_rate", 0.0)
        speech_rate: float = audio_metrics.get("speech_rate_wpm", 120.0)
        duration: float = audio_metrics.get("duration_s", 10.0)

        # Rule-based flags
        if silence_ratio > self.SUSPICIOUS_SILENCE_RATIO:
            flags.append("excessive_silence")
            suspicious.append("Candidate may be reading from notes or distracted")

        if pitch_variance < self.READING_PITCH_CV_THRESHOLD:
            flags.append("flat_pitch_pattern")
            suspicious.append("Suspiciously monotone speech — possible script reading")

        if filler_rate > self.MAX_FILLER_RATE:
            flags.append("extreme_filler_usage")
            suspicious.append(f"Very high filler word rate ({filler_rate:.1f}/min) — extreme anxiety")

        if speech_rate > 250:
            flags.append("unusually_fast_speech")
            suspicious.append(f"Speech rate {speech_rate:.0f} WPM exceeds normal range")

        if duration < 5.0 and turn_index > 0:
            flags.append("very_short_response")
            suspicious.append("Response too brief for question complexity")

        # LLM behavioral pass
        context = {
            "turn_index": turn_index,
            "audio_metrics": audio_metrics,
            "flags_detected": flags,
            "session_turns_so_far": len(session_history),
            "avg_silence_ratio_session": (
                sum(t.get("silence_ratio", 0) for t in session_history) / len(session_history)
                if session_history else silence_ratio
            ),
        }

        try:
            llm_result = await self._llm._chat_json(
                _PROCTORING_SYSTEM_PROMPT, str(context)
            )
        except Exception as exc:
            log.warning("proctoring_llm_failed", error=str(exc))
            llm_result = {
                "attention_score": max(0.0, 1.0 - silence_ratio - len(flags) * 0.1),
                "confidence_score": min(1.0, pitch_variance * 1.5),
                "anxiety_level": "high" if filler_rate > 10 else "medium" if filler_rate > 5 else "low",
                "suspicious_patterns": suspicious,
                "behavioral_flags": flags,
                "proctoring_pass": len(flags) < 2,
                "notes": "Rule-based fallback (LLM unavailable)",
            }

        llm_result["behavioral_flags"] = list(set(flags + llm_result.get("behavioral_flags", [])))
        llm_result["suspicious_patterns"] = list(set(suspicious + llm_result.get("suspicious_patterns", [])))
        llm_result["turn_index"] = turn_index

        log.info(
            "proctoring_turn_analyzed",
            turn=turn_index,
            flags=len(llm_result["behavioral_flags"]),
            pass_=llm_result.get("proctoring_pass"),
        )
        return llm_result

    def compute_session_proctoring_report(
        self, turn_results: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Aggregate all turn proctoring results into a session-level report."""
        if not turn_results:
            return {"overall_pass": True, "avg_attention_score": 1.0, "flags_summary": []}

        avg_attention = sum(r.get("attention_score", 1.0) for r in turn_results) / len(turn_results)
        avg_confidence = sum(r.get("confidence_score", 1.0) for r in turn_results) / len(turn_results)
        all_flags = [f for r in turn_results for f in r.get("behavioral_flags", [])]
        flag_counts: dict[str, int] = {}
        for f in all_flags:
            flag_counts[f] = flag_counts.get(f, 0) + 1

        overall_pass = (
            avg_attention >= self.MIN_ATTENTION_SCORE
            and sum(1 for r in turn_results if not r.get("proctoring_pass", True)) < len(turn_results) * 0.4
        )

        return {
            "overall_pass": overall_pass,
            "avg_attention_score": round(avg_attention, 4),
            "avg_confidence_score": round(avg_confidence, 4),
            "flags_summary": sorted(flag_counts.items(), key=lambda x: -x[1]),
            "flagged_turns": [r["turn_index"] for r in turn_results if not r.get("proctoring_pass", True)],
            "integrity_score": round(avg_attention * 0.6 + (1.0 - min(len(all_flags) / max(len(turn_results), 1) / 3, 1.0)) * 0.4, 4),
        }
