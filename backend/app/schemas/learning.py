from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.learning_plan import LearningPlanStatus


class PlanCreateRequest(BaseModel):
    gap_name: str | None = Field(default=None, max_length=255)
    skill_name: str | None = Field(default=None, max_length=255)
    gap_id: UUID | None = None
    target_role: str | None = None
    source_session_id: UUID | None = None
    category: str = Field(default="technical", max_length=50)
    target_days: int = Field(default=7, ge=3, le=30)

    @model_validator(mode="after")
    def populate_gap_name(self) -> PlanCreateRequest:
        if not self.gap_name:
            self.gap_name = self.skill_name or "Core Competency"
        return self


class DayCompleteRequest(BaseModel):
    day_number: int = Field(default=1, ge=1, le=30)


class ReassessmentAnswerItem(BaseModel):
    question_id: int
    answer_text: str = Field(..., min_length=2)


class ReassessmentSubmitRequest(BaseModel):
    answers: list[ReassessmentAnswerItem] | dict[str, str]

    @model_validator(mode="after")
    def normalize_answers(self) -> ReassessmentSubmitRequest:
        if isinstance(self.answers, dict):
            items: list[ReassessmentAnswerItem] = []
            for k, v in self.answers.items():
                try:
                    qid = int(k)
                except ValueError:
                    qid = 0
                items.append(ReassessmentAnswerItem(question_id=qid, answer_text=str(v)))
            self.answers = items
        return self


class LearningPlanResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID
    title: str
    detected_gap: str
    source_session_id: UUID | None
    category: str
    status: LearningPlanStatus
    target_completion_days: int
    current_day: int
    daily_schedule: list[dict]
    reassessment_quiz: list[dict]
    reassessment_score: float | None
    reassessment_passed: bool | None
    created_at: datetime
    updated_at: datetime


class ReassessmentResultResponse(BaseModel):
    plan_id: str
    reassessment_score: float
    passed: bool
    gap_resolved: bool = False
    status: str
    feedback: list[dict]
    message: str
