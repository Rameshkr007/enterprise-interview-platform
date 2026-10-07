from __future__ import annotations

from typing import Annotated, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.dependencies import CurrentUser
from app.services.llm_service import LLMService
from app.services.negotiation_service import NegotiationService, NEGOTIATION_TIPS

router = APIRouter(prefix="/negotiation", tags=["Salary Negotiation Simulator"])


class NegotiationRoundRequest(BaseModel):
    role: str = Field(..., min_length=2, max_length=255)
    company: str = Field(default="Tech Corp", max_length=255)
    min_salary: int = Field(default=120, ge=30, le=1000)  # in $k
    max_salary: int = Field(default=180, ge=40, le=2000)  # in $k
    current_salary: int = Field(default=100, ge=20, le=1000)
    years_exp: int = Field(default=4, ge=0, le=40)
    candidate_message: str = Field(..., min_length=2, max_length=2000)
    conversation_history: list[dict[str, Any]] = Field(default_factory=list)
    round_num: int = Field(default=1, ge=1, le=20)


class NegotiationAnalysisRequest(BaseModel):
    target_salary: int = Field(default=160, ge=30, le=2000)
    conversation_history: list[dict[str, Any]] = Field(..., min_length=1)


@router.get("/tips")
async def get_negotiation_tips() -> dict[str, list[str]]:
    """Returns strategic salary negotiation rules and counter-tactics."""
    return {"tips": NEGOTIATION_TIPS}


@router.post("/round")
async def simulate_negotiation_round(
    body: NegotiationRoundRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Simulates a tough HR counter-offer, scores the candidate's tactics, and advises the next move."""
    service = NegotiationService(LLMService())
    return await service.simulate_round(
        role=body.role,
        min_salary=body.min_salary,
        max_salary=body.max_salary,
        current_salary=body.current_salary,
        years_exp=body.years_exp,
        company=body.company,
        candidate_message=body.candidate_message,
        conversation_history=body.conversation_history,
        round_num=body.round_num,
    )


@router.post("/analyze")
async def analyze_negotiation(
    body: NegotiationAnalysisRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Evaluates the entire salary negotiation dialogue with financial outcome metrics."""
    service = NegotiationService(LLMService())
    return await service.analyze_full_negotiation(
        target_salary=body.target_salary,
        conversation_history=body.conversation_history,
    )
