from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview_session import InterviewSession
from app.models.interview_turn import InterviewTurn

log = structlog.get_logger(__name__)

# ── XP Configuration ──────────────────────────────────────────────────────────
XP_TABLE: dict[str, int] = {
    "answer_question": 50,
    "complete_session": 200,
    "score_above_80": 100,
    "score_above_90": 200,
    "daily_streak_3": 150,
    "daily_streak_7": 400,
    "daily_streak_30": 2000,
    "first_session": 500,
    "first_coding_submit": 300,
    "resume_analyzed": 100,
    "invite_friend": 250,
}

LEVEL_THRESHOLDS = [
    (0,      "Intern",            "🎒"),
    (500,    "Junior Dev",        "💻"),
    (1500,   "Mid Engineer",      "⚙️"),
    (3500,   "Senior Engineer",   "🔧"),
    (7000,   "Staff Engineer",    "🏗️"),
    (12000,  "Principal Engineer","🎯"),
    (20000,  "Distinguished Eng", "🌟"),
    (35000,  "Fellow",            "🏆"),
    (55000,  "VP Engineering",    "👑"),
    (80000,  "CTO",               "🚀"),
]

ACHIEVEMENTS: list[dict[str, Any]] = [
    {"id": "first_blood",      "name": "First Blood",         "icon": "🩸", "desc": "Complete your first interview",    "xp": 500,  "condition": "first_session"},
    {"id": "perfect_score",    "name": "Perfectionist",        "icon": "💯", "desc": "Score 100 in any session",        "xp": 1000, "condition": "score_100"},
    {"id": "speedrunner",      "name": "Speedrunner",          "icon": "⚡", "desc": "Answer 5 questions in under 2min each", "xp": 300, "condition": "fast_answers"},
    {"id": "polyglot",         "name": "Polyglot Coder",       "icon": "🌍", "desc": "Submit in 3 different languages", "xp": 500,  "condition": "multi_language"},
    {"id": "streak_7",         "name": "Weekly Warrior",       "icon": "🔥", "desc": "7-day practice streak",           "xp": 400,  "condition": "streak_7"},
    {"id": "streak_30",        "name": "Monthly Champion",     "icon": "🏅", "desc": "30-day practice streak",          "xp": 2000, "condition": "streak_30"},
    {"id": "company_buster",   "name": "Company Buster",       "icon": "🏢", "desc": "Pass company-mode for 3 companies","xp": 750, "condition": "company_3"},
    {"id": "ats_master",       "name": "ATS Master",           "icon": "📊", "desc": "Score 90%+ on ATS analysis",      "xp": 400,  "condition": "ats_90"},
    {"id": "clean_coder",      "name": "Clean Coder",          "icon": "✨", "desc": "0 bugs in a code submission",     "xp": 600,  "condition": "no_bugs"},
    {"id": "top_1pct",         "name": "Top 1%",               "icon": "👑", "desc": "Reach top 1% on leaderboard",    "xp": 2000, "condition": "top_1_pct"},
]

# ── SM-2 Spaced Repetition ─────────────────────────────────────────────────────
def sm2_next_interval(
    ease_factor: float,
    interval: int,
    quality: int,   # 0-5 (0=blackout, 5=perfect)
) -> tuple[int, float]:
    """Returns (next_interval_days, new_ease_factor)."""
    if quality < 3:
        return 1, max(1.3, ease_factor - 0.2)
    if interval == 0:
        next_interval = 1
    elif interval == 1:
        next_interval = 6
    else:
        next_interval = round(interval * ease_factor)
    new_ef = max(1.3, ease_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    return next_interval, round(new_ef, 2)


class GamificationService:
    """XP, levels, achievements, daily challenges, spaced repetition."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── XP & Level ────────────────────────────────────────────────────────────
    def compute_level(self, total_xp: int) -> dict[str, Any]:
        level_idx = 0
        for i, (threshold, _, _) in enumerate(LEVEL_THRESHOLDS):
            if total_xp >= threshold:
                level_idx = i

        current = LEVEL_THRESHOLDS[level_idx]
        next_lvl = LEVEL_THRESHOLDS[min(level_idx + 1, len(LEVEL_THRESHOLDS) - 1)]
        current_threshold = current[0]
        next_threshold = next_lvl[0]

        if current_threshold == next_threshold:
            progress = 100.0
        else:
            progress = ((total_xp - current_threshold) / (next_threshold - current_threshold)) * 100

        return {
            "level": level_idx + 1,
            "title": current[1],
            "emoji": current[2],
            "total_xp": total_xp,
            "progress_to_next": round(min(progress, 100), 1),
            "xp_to_next": max(0, next_threshold - total_xp),
            "next_title": next_lvl[1],
        }

    def calculate_session_xp(self, session_score: float, turn_count: int, streak_days: int) -> dict[str, Any]:
        """Calculate XP earned from a completed session."""
        xp_breakdown: list[dict] = []
        total_xp = 0

        # Base XP per question
        q_xp = turn_count * XP_TABLE["answer_question"]
        xp_breakdown.append({"reason": f"Answered {turn_count} questions", "xp": q_xp})
        total_xp += q_xp

        # Completion bonus
        xp_breakdown.append({"reason": "Session completed", "xp": XP_TABLE["complete_session"]})
        total_xp += XP_TABLE["complete_session"]

        # Score bonuses
        if session_score >= 90:
            xp_breakdown.append({"reason": "Scored 90%+", "xp": XP_TABLE["score_above_90"]})
            total_xp += XP_TABLE["score_above_90"]
        elif session_score >= 80:
            xp_breakdown.append({"reason": "Scored 80%+", "xp": XP_TABLE["score_above_80"]})
            total_xp += XP_TABLE["score_above_80"]

        # Streak bonus
        if streak_days >= 30:
            xp_breakdown.append({"reason": "30-day streak! 🔥", "xp": XP_TABLE["daily_streak_30"]})
            total_xp += XP_TABLE["daily_streak_30"]
        elif streak_days >= 7:
            xp_breakdown.append({"reason": "7-day streak!", "xp": XP_TABLE["daily_streak_7"]})
            total_xp += XP_TABLE["daily_streak_7"]
        elif streak_days >= 3:
            xp_breakdown.append({"reason": "3-day streak", "xp": XP_TABLE["daily_streak_3"]})
            total_xp += XP_TABLE["daily_streak_3"]

        return {"total_xp_earned": total_xp, "breakdown": xp_breakdown}

    # ── Achievements ──────────────────────────────────────────────────────────
    async def check_achievements(
        self,
        user_id: UUID,
        event: str,
        context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Check and return newly unlocked achievements for a given event."""
        newly_unlocked: list[dict] = []
        sessions_result = await self._db.execute(
            select(InterviewSession)
            .where(InterviewSession.user_id == user_id, InterviewSession.status == "completed")
        )
        sessions = list(sessions_result.scalars().all())
        scores = [s.aggregate_score or 0 for s in sessions if s.aggregate_score]

        checks = {
            "first_session": len(sessions) == 1,
            "score_100": any(s >= 99.9 for s in scores),
            "streak_7": context.get("streak_days", 0) >= 7,
            "streak_30": context.get("streak_days", 0) >= 30,
            "ats_90": context.get("ats_score", 0) >= 90,
        }

        for ach in ACHIEVEMENTS:
            cond = ach.get("condition", "")
            if checks.get(cond, False):
                newly_unlocked.append({
                    "id": ach["id"],
                    "name": ach["name"],
                    "icon": ach["icon"],
                    "description": ach["desc"],
                    "xp_awarded": ach["xp"],
                })

        return newly_unlocked

    # ── Daily Challenge ───────────────────────────────────────────────────────
    async def get_daily_challenge(self, user_id: UUID) -> dict[str, Any]:
        """Returns today's daily challenge question. Same for all users (seeded by date)."""
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        categories = ["behavioral", "technical", "system_design", "situational"]
        cat_idx = hash(today) % len(categories)
        difficulties = ["easy", "medium", "hard"]
        diff_idx = (hash(today + str(user_id)) // 7) % len(difficulties)

        return {
            "challenge_date": today,
            "category": categories[cat_idx],
            "difficulty": difficulties[diff_idx],
            "xp_reward": 300 if difficulties[diff_idx] == "hard" else 200 if difficulties[diff_idx] == "medium" else 100,
            "streak_bonus_xp": 150,
            "expires_at": (datetime.now(UTC).replace(hour=23, minute=59, second=59)).isoformat(),
        }

    # ── Spaced Repetition ─────────────────────────────────────────────────────
    async def get_review_queue(self, user_id: UUID) -> list[dict[str, Any]]:
        """SM-2 spaced repetition: returns questions due for review today."""
        due_turns_query = text("""
            SELECT
                it.id,
                it.question_text,
                it.question_category,
                it.question_difficulty,
                it.eval_scores,
                it.created_at,
                s.id as session_id
            FROM interview_turns it
            JOIN interview_sessions s ON it.session_id = s.id
            WHERE s.user_id = :user_id
              AND it.eval_scores IS NOT NULL
              AND (it.eval_scores->>'composite_score')::float < 0.7
            ORDER BY it.created_at ASC
            LIMIT 10
        """)
        result = await self._db.execute(due_turns_query, {"user_id": str(user_id)})
        rows = result.fetchall()

        review_queue = []
        for row in rows:
            score = float((row.eval_scores or {}).get("composite_score", 0))
            quality = int(score * 5)
            interval, new_ef = sm2_next_interval(2.5, 0, quality)
            due_date = row.created_at + timedelta(days=interval)
            if due_date.date() <= datetime.now(UTC).date():
                review_queue.append({
                    "turn_id": str(row.id),
                    "question_text": row.question_text,
                    "category": str(row.question_category),
                    "difficulty": row.question_difficulty,
                    "last_score": round(score * 100, 1),
                    "due_date": due_date.date().isoformat(),
                    "session_id": str(row.session_id),
                    "review_reason": "Low score — needs practice",
                })

        log.info("review_queue_built", user_id=str(user_id), count=len(review_queue))
        return review_queue
