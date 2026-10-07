from __future__ import annotations

import json
from typing import Annotated, Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.core.exceptions import NotFoundException
from app.database import get_db
from app.models.advanced import LeaderboardEntry, ProgressTracker
from app.models.interview_session import InterviewSession
from app.models.interview_turn import InterviewTurn
from app.models.session_report import SessionReport
from app.services.resume_builder import ResumeBuilderService
from app.services.llm_service import LLMService

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/progress")
async def get_user_progress(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Full progress dashboard: score trends, heatmap, streaks, badges."""
    # Session history
    sessions_result = await db.execute(
        select(InterviewSession)
        .where(
            InterviewSession.user_id == current_user.id,
            InterviewSession.status == "completed",
        )
        .order_by(InterviewSession.created_at.asc())
    )
    sessions = list(sessions_result.scalars().all())

    score_history = [
        {
            "date": s.completed_at.isoformat() if s.completed_at else s.created_at.isoformat(),
            "score": round(s.aggregate_score or 0, 2),
            "session_id": str(s.id),
        }
        for s in sessions
    ]

    # Category heatmap across all turns
    turns_result = await db.execute(
        select(
            InterviewTurn.question_category,
            func.avg(
                func.cast(
                    func.json_extract_path_text(
                        InterviewTurn.eval_scores, "composite_score"
                    ),
                    type_=type("", (), {"__visit_name__": "float", "__module__": ""})(),
                )
            ).label("avg_score"),
            func.count(InterviewTurn.id).label("total"),
        )
        .join(InterviewSession, InterviewTurn.session_id == InterviewSession.id)
        .where(InterviewSession.user_id == current_user.id)
        .group_by(InterviewTurn.question_category)
    )
    # Fallback: raw query for heatmap
    heatmap_query = text("""
        SELECT
            it.question_category,
            AVG((it.eval_scores->>'composite_score')::float) as avg_score,
            COUNT(*) as total_turns
        FROM interview_turns it
        JOIN interview_sessions s ON it.session_id = s.id
        WHERE s.user_id = :user_id
          AND it.eval_scores IS NOT NULL
        GROUP BY it.question_category
    """)
    heatmap_result = await db.execute(heatmap_query, {"user_id": str(current_user.id)})
    skill_heatmap = {
        row.question_category: {
            "avg_score": round(float(row.avg_score or 0), 3),
            "total_turns": int(row.total_turns),
        }
        for row in heatmap_result
    }

    # Badges
    badges = _compute_badges(sessions, skill_heatmap)

    # Best + avg score
    scores = [s.aggregate_score or 0 for s in sessions if s.aggregate_score]
    avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
    best_score = round(max(scores, default=0.0), 2)

    return {
        "total_sessions": len(sessions),
        "avg_score": avg_score,
        "best_score": best_score,
        "score_history": score_history,
        "skill_heatmap": skill_heatmap,
        "badges": badges,
        "streak_days": _compute_streak(sessions),
        "weak_categories": sorted(
            skill_heatmap, key=lambda k: skill_heatmap[k]["avg_score"]
        )[:3],
        "strong_categories": sorted(
            skill_heatmap, key=lambda k: -skill_heatmap[k]["avg_score"]
        )[:3],
    }


@router.get("/leaderboard")
async def get_leaderboard(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 20,
    category: str = "general",
) -> dict[str, Any]:
    """Global leaderboard with user's own rank."""
    query = text("""
        WITH ranked AS (
            SELECT
                sr.user_id,
                u.full_name,
                AVG(sr.final_score) as avg_score,
                MAX(sr.final_score) as best_score,
                COUNT(sr.id) as session_count,
                RANK() OVER (ORDER BY AVG(sr.final_score) DESC) as rank,
                PERCENT_RANK() OVER (ORDER BY AVG(sr.final_score) DESC) as percentile_rank
            FROM session_reports sr
            JOIN users u ON sr.user_id = u.id
            GROUP BY sr.user_id, u.full_name
        )
        SELECT * FROM ranked ORDER BY rank LIMIT :limit
    """)
    result = await db.execute(query, {"limit": limit})
    entries = [
        {
            "rank": row.rank,
            "user_name": row.full_name,
            "avg_score": round(float(row.avg_score), 2),
            "best_score": round(float(row.best_score), 2),
            "session_count": int(row.session_count),
            "percentile": round((1 - float(row.percentile_rank)) * 100, 1),
            "is_current_user": str(row.user_id) == str(current_user.id),
        }
        for row in result
    ]

    # Current user's position if not in top N
    my_rank_query = text("""
        WITH ranked AS (
            SELECT
                sr.user_id,
                AVG(sr.final_score) as avg_score,
                RANK() OVER (ORDER BY AVG(sr.final_score) DESC) as rank,
                PERCENT_RANK() OVER (ORDER BY AVG(sr.final_score) DESC) as percentile_rank
            FROM session_reports sr
            GROUP BY sr.user_id
        )
        SELECT rank, avg_score, percentile_rank FROM ranked WHERE user_id = :user_id
    """)
    my_rank_result = await db.execute(my_rank_query, {"user_id": str(current_user.id)})
    my_rank_row = my_rank_result.fetchone()

    return {
        "leaderboard": entries,
        "my_rank": {
            "rank": int(my_rank_row.rank) if my_rank_row else None,
            "avg_score": round(float(my_rank_row.avg_score), 2) if my_rank_row else 0.0,
            "percentile": round((1 - float(my_rank_row.percentile_rank)) * 100, 1) if my_rank_row else 0.0,
        },
        "total_participants": len(entries),
    }


@router.get("/compare/{session_id}")
async def compare_with_peers(
    session_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Compare a specific session against platform averages by category."""
    report = await db.execute(
        select(SessionReport).where(
            SessionReport.session_id == session_id,
            SessionReport.user_id == current_user.id,
        )
    )
    report_row = report.scalar_one_or_none()
    if not report_row:
        raise NotFoundException("Session report not found")

    platform_avg_query = text("""
        SELECT
            AVG(final_score) as platform_avg_score,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY final_score) as median_score,
            COUNT(*) as total_sessions
        FROM session_reports
        WHERE final_score IS NOT NULL
    """)
    avg_result = await db.execute(platform_avg_query)
    avg_row = avg_result.fetchone()

    return {
        "session_score": report_row.final_score,
        "platform_avg_score": round(float(avg_row.platform_avg_score or 0), 2) if avg_row else 0.0,
        "platform_median_score": round(float(avg_row.median_score or 0), 2) if avg_row else 0.0,
        "total_platform_sessions": int(avg_row.total_sessions or 0) if avg_row else 0,
        "score_delta_from_avg": round(
            report_row.final_score - float(avg_row.platform_avg_score or 0), 2
        ) if avg_row else 0.0,
        "category_scores": report_row.category_scores,
        "audio_metrics": report_row.overall_audio_metrics,
        "difficulty_progression": report_row.difficulty_progression,
    }


@router.get("/coaching")
async def get_coaching_plan(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Multi-session AI coaching analysis."""
    svc = ResumeBuilderService(db=db, llm_svc=LLMService())
    return await svc.generate_interview_coaching(current_user.id)


def _compute_badges(sessions: list, heatmap: dict) -> list[dict]:
    badges: list[dict] = []
    if len(sessions) >= 1:
        badges.append({"id": "first_session", "name": "First Step", "icon": "🚀", "earned": True})
    if len(sessions) >= 5:
        badges.append({"id": "consistent", "name": "Consistent Practitioner", "icon": "🔥", "earned": True})
    if len(sessions) >= 20:
        badges.append({"id": "veteran", "name": "Interview Veteran", "icon": "🏆", "earned": True})
    scores = [s.aggregate_score or 0 for s in sessions if s.aggregate_score]
    if scores and max(scores) >= 90:
        badges.append({"id": "top_scorer", "name": "Top Scorer", "icon": "⭐", "earned": True})
    if len(heatmap) >= 4:
        badges.append({"id": "all_rounder", "name": "All-Rounder", "icon": "🎯", "earned": True})
    return badges


def _compute_streak(sessions: list) -> int:
    if not sessions:
        return 0
    from datetime import date, timedelta
    today = date.today()
    streak = 0
    check_date = today
    session_dates = set(
        (s.completed_at or s.created_at).date()
        for s in sessions
        if s.completed_at or s.created_at
    )
    while check_date in session_dates:
        streak += 1
        check_date -= timedelta(days=1)
    return streak
