from __future__ import annotations

import enum
import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import LLMServiceException, NotFoundException
from app.models.interview_session import InterviewSession
from app.models.interview_turn import InterviewTurn
from app.models.session_report import SessionReport
from app.services.llm_service import LLMService

log = structlog.get_logger(__name__)
settings = get_settings()

_RESUME_IMPROVEMENT_PROMPT = """
You are an elite technical resume writer and career coach.
Given a resume and ATS analysis results, generate specific, actionable improvements.

Return ONLY valid JSON:
{
  "improved_summary": str,
  "bullet_improvements": [
    {"original": str, "improved": str, "reason": str}
  ],
  "missing_keywords": [str],
  "skills_to_highlight": [str],
  "format_suggestions": [str],
  "ats_optimization_tips": [str],
  "estimated_score_improvement": float
}
"""

_CAREER_PATH_PROMPT = """
You are a senior career counselor with deep knowledge of tech industry trajectories.
Based on the candidate's resume, ATS skill gaps, and interview performance, provide a detailed career roadmap.

Return ONLY valid JSON:
{
  "current_level": str,
  "target_role": str,
  "timeline_months": int,
  "skill_roadmap": [
    {"skill": str, "priority": "high"|"medium"|"low", "resources": [{"title": str, "url": str, "type": str}], "estimated_weeks": int}
  ],
  "certifications": [{"name": str, "provider": str, "url": str, "value": str}],
  "salary_range": {"min": int, "max": int, "currency": "USD"},
  "job_titles_to_target": [str],
  "networking_tips": [str]
}
"""

_INTERVIEW_COACH_PROMPT = """
You are an expert interview coach analyzing patterns across a candidate's interview sessions.
Identify systematic weaknesses and provide specific coaching.

Return ONLY valid JSON:
{
  "pattern_analysis": str,
  "top_weaknesses": [{"area": str, "evidence": str, "fix": str}],
  "top_strengths": [{"area": str, "evidence": str}],
  "practice_scenarios": [{"scenario": str, "model_answer_outline": str}],
  "confidence_coaching": str,
  "communication_coaching": str,
  "overall_readiness_score": float
}
"""


class ResumeBuilderService:
    """
    AI-powered Resume Builder & Career Intelligence Engine.

    Features:
    1. Resume bullet-point rewriting with ATS keyword injection
    2. Career path roadmap generation
    3. Multi-session interview pattern analysis & coaching
    4. Salary benchmarking
    5. Missing certification identification
    """

    def __init__(self, db: AsyncSession, llm_svc: LLMService) -> None:
        self._db = db
        self._llm = llm_svc

    async def generate_resume_improvements(
        self,
        resume_text: str,
        ats_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """Rewrite resume sections with ATS-optimized language."""
        user_msg = (
            f"CURRENT RESUME:\n{resume_text[:4000]}\n\n"
            f"ATS ANALYSIS RESULTS:\n"
            f"Overall Score: {ats_analysis.get('overall_score', 0):.1f}/100\n"
            f"Skill Gaps: {json.dumps(ats_analysis.get('skill_gaps', [])[:8], indent=2)}\n"
            f"Matched Skills: {json.dumps(ats_analysis.get('matched_skills', [])[:8], indent=2)}\n"
            f"Section Scores: {json.dumps(ats_analysis.get('section_scores', {}), indent=2)}"
        )
        result = await self._llm._chat_json(_RESUME_IMPROVEMENT_PROMPT, user_msg)
        log.info("resume_improvements_generated", improvements=len(result.get("bullet_improvements", [])))
        return result

    async def generate_career_roadmap(
        self,
        resume_text: str,
        target_role: str,
        skill_gaps: list[dict],
        interview_score: float | None = None,
    ) -> dict[str, Any]:
        """Generate a personalized career roadmap with learning resources."""
        user_msg = (
            f"TARGET ROLE: {target_role}\n\n"
            f"CURRENT RESUME:\n{resume_text[:3000]}\n\n"
            f"SKILL GAPS:\n{json.dumps(skill_gaps[:10], indent=2)}\n\n"
            f"INTERVIEW PERFORMANCE SCORE: {interview_score or 'Not yet assessed'}/100"
        )
        result = await self._llm._chat_json(_CAREER_PATH_PROMPT, user_msg)
        log.info("career_roadmap_generated", role=target_role, skills=len(result.get("skill_roadmap", [])))
        return result

    async def generate_interview_coaching(
        self,
        user_id: UUID,
        latest_n_sessions: int = 5,
    ) -> dict[str, Any]:
        """Analyze patterns across multiple sessions and generate coaching plan."""
        sessions_result = await self._db.execute(
            select(InterviewSession)
            .where(
                InterviewSession.user_id == user_id,
                InterviewSession.status == "completed",
            )
            .order_by(InterviewSession.created_at.desc())
            .limit(latest_n_sessions)
        )
        sessions = list(sessions_result.scalars().all())

        if not sessions:
            raise NotFoundException("No completed interview sessions found for coaching")

        # Collect aggregate metrics across sessions
        all_turns: list[InterviewTurn] = []
        session_scores: list[float] = []
        for session in sessions:
            turns_result = await self._db.execute(
                select(InterviewTurn)
                .where(InterviewTurn.session_id == session.id)
                .order_by(InterviewTurn.turn_index)
            )
            turns = list(turns_result.scalars().all())
            all_turns.extend(turns)
            if session.aggregate_score:
                session_scores.append(session.aggregate_score)

        # Build analysis context
        category_breakdown: dict[str, list[float]] = {}
        audio_patterns: dict[str, list[float]] = {}
        for turn in all_turns:
            cat = str(turn.question_category)
            if turn.eval_scores:
                category_breakdown.setdefault(cat, []).append(
                    turn.eval_scores.get("composite_score", 0.5)
                )
            if turn.audio_metrics:
                for key in ("silence_ratio", "pitch_variance_score", "filler_word_rate", "speech_rate_wpm"):
                    val = turn.audio_metrics.get(key)
                    if val is not None:
                        audio_patterns.setdefault(key, []).append(float(val))

        avg_by_category = {
            cat: round(sum(v) / len(v), 3) for cat, v in category_breakdown.items()
        }
        avg_audio = {
            k: round(sum(v) / len(v), 3) for k, v in audio_patterns.items()
        }

        user_msg = (
            f"SESSIONS ANALYZED: {len(sessions)}\n"
            f"TOTAL TURNS: {len(all_turns)}\n"
            f"SESSION SCORES (newest first): {session_scores}\n"
            f"AVERAGE SCORES BY CATEGORY: {json.dumps(avg_by_category, indent=2)}\n"
            f"AUDIO PATTERN AVERAGES: {json.dumps(avg_audio, indent=2)}\n"
            f"SCORE TREND: {'improving' if len(session_scores) >= 2 and session_scores[0] > session_scores[-1] else 'declining' if len(session_scores) >= 2 else 'single session'}"
        )

        result = await self._llm._chat_json(_INTERVIEW_COACH_PROMPT, user_msg)
        result["sessions_analyzed"] = len(sessions)
        result["score_trend"] = session_scores
        log.info("coaching_generated", user_id=str(user_id), sessions=len(sessions))
        return result
