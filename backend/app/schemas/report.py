from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AudioMetricsSummary(BaseModel):
    avg_silence_ratio: float
    avg_pitch_variance_score: float
    avg_filler_rate: float
    avg_speech_rate_wpm: float
    confidence_score: float


class ReportResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    session_id: UUID
    user_id: UUID
    final_score: float
    percentile_rank: float | None
    overall_audio_metrics: dict
    category_scores: dict
    difficulty_progression: list
    skill_coverage_delta: list
    strengths: list[str]
    improvement_areas: list[str]
    recommended_resources: list
    generated_at: datetime
