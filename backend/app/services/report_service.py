from __future__ import annotations

from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import SessionNotFoundException
from app.models.interview_session import InterviewSession, SessionStatus
from app.models.interview_turn import InterviewTurn
from app.models.session_report import SessionReport
from app.services.llm_service import LLMService

log = structlog.get_logger(__name__)


class ReportService:
    def __init__(self, db: AsyncSession, llm_svc: LLMService) -> None:
        self._db = db
        self._llm = llm_svc

    async def generate_report(self, session_id: UUID) -> SessionReport:
        session = await self._db.get(InterviewSession, session_id)
        if session is None:
            raise SessionNotFoundException()

        turns_result = await self._db.execute(
            select(InterviewTurn)
            .where(InterviewTurn.session_id == session_id)
            .order_by(InterviewTurn.turn_index)
        )
        turns = list(turns_result.scalars().all())

        audio_metrics = self._aggregate_audio_metrics(turns)
        category_scores = self._aggregate_category_scores(turns)
        difficulty_progression = self._build_difficulty_progression(turns)
        all_scores = [
            t.eval_scores.get("composite_score", 0.0) for t in turns if t.eval_scores
        ]
        final_score = (sum(all_scores) / len(all_scores) * 100) if all_scores else 0.0

        llm_insights = await self._llm.generate_question(
            context={
                "task": "generate_report_insights",
                "category_scores": category_scores,
                "final_score": final_score,
                "turn_count": len(turns),
            }
        )

        report = SessionReport(
            session_id=session_id,
            user_id=session.user_id,
            overall_audio_metrics=audio_metrics,
            category_scores=category_scores,
            difficulty_progression=difficulty_progression,
            skill_coverage_delta=[],
            strengths=llm_insights.get("strengths", []),
            improvement_areas=llm_insights.get("improvement_areas", []),
            recommended_resources=llm_insights.get("recommended_resources", []),
            final_score=min(final_score, 100.0),
        )
        self._db.add(report)

        session.status = SessionStatus.completed
        session.aggregate_score = final_score
        self._db.add(session)

        await self._db.flush()
        await self._db.refresh(report)
        log.info("report_generated", session_id=str(session_id), final_score=final_score)
        return report

    def _aggregate_audio_metrics(self, turns: list[InterviewTurn]) -> dict:
        metrics = [t.audio_metrics for t in turns if t.audio_metrics]
        if not metrics:
            return {}
        avg = lambda key: sum(m.get(key, 0) for m in metrics) / len(metrics)  # noqa: E731
        return {
            "avg_silence_ratio": round(avg("silence_ratio"), 4),
            "avg_pitch_variance_score": round(avg("pitch_variance_score"), 4),
            "avg_filler_rate": round(avg("filler_word_rate"), 4),
            "avg_speech_rate_wpm": round(avg("speech_rate_wpm"), 2),
            "confidence_score": round(1.0 - avg("pitch_variance_score") * 0.5 - avg("silence_ratio") * 0.3 - min(avg("filler_word_rate") / 10, 0.2), 4),
        }

    def _aggregate_category_scores(self, turns: list[InterviewTurn]) -> dict:
        from collections import defaultdict
        cat_scores: dict[str, list[float]] = defaultdict(list)
        for turn in turns:
            if turn.eval_scores:
                cat = turn.question_category.value if hasattr(turn.question_category, "value") else str(turn.question_category)
                cat_scores[cat].append(turn.eval_scores.get("composite_score", 0.0))
        return {cat: round(sum(v) / len(v), 4) for cat, v in cat_scores.items()}

    def _build_difficulty_progression(self, turns: list[InterviewTurn]) -> list:
        return [
            {
                "turn_index": t.turn_index,
                "difficulty": t.question_difficulty,
                "composite_score": t.eval_scores.get("composite_score", 0.0) if t.eval_scores else None,
            }
            for t in turns
        ]
