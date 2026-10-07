from __future__ import annotations

import json
from typing import Any
import structlog
from app.services.llm_service import LLMService

log = structlog.get_logger(__name__)

_NEGOTIATION_SYSTEM = """
You are an expert salary negotiation coach AND a tough HR interviewer simultaneously.
You will simulate a realistic salary negotiation conversation.

Current context:
- Candidate's target role: {role}
- Market range: ${min_salary}k–${max_salary}k
- Candidate's current salary: ${current_salary}k
- Candidate's experience years: {years_exp}
- Company: {company}
- Round: {round_num} of the negotiation

Based on the candidate's last message, respond as the HR/recruiter would (be realistic, push back, give counter-offers, use anchoring tactics).
Then score their negotiation tactic.

Return ONLY JSON:
{{
  "hr_response": str,
  "tactic_used_by_candidate": str,
  "tactic_score": float 0-1,
  "negotiation_tip": str,
  "current_offer": int,
  "negotiation_status": "ongoing" | "accepted" | "rejected" | "countered",
  "power_dynamics": "candidate_winning" | "hr_winning" | "balanced",
  "what_to_say_next": str
}}
"""

_NEGOTIATION_ANALYSIS_PROMPT = """
Analyze the complete salary negotiation conversation and give a final coaching report.

Return ONLY JSON:
{{
  "final_offer_achieved": int,
  "vs_target": float,
  "overall_score": float 0-1,
  "tactics_used": [str],
  "best_moment": str,
  "worst_moment": str,
  "what_you_did_well": [str],
  "mistakes_made": [str],
  "pro_tips": [str],
  "would_have_gotten_offer": bool,
  "estimated_money_left_on_table": int
}}
"""

NEGOTIATION_TIPS = [
    "Never give the first number — always ask for their budget range first.",
    "Use silence as a weapon — after naming your number, stay quiet.",
    "Anchor high: ask for 20-30% above your target so there's room to negotiate.",
    "Never negotiate against yourself — if they say 'is that your final answer?' say yes.",
    "Bundle total compensation: ask about equity, bonus, PTO, remote days, not just salary.",
    "Use competing offers as leverage — but only if you actually have them.",
    "Express enthusiasm for the role before negotiating — 'I'm very excited about this opportunity...'",
    "Research market data and cite it: 'According to Levels.fyi, the P4 range at similar companies is...'",
]


class NegotiationService:
    """Salary negotiation simulator with realistic HR pushback and tactic scoring."""

    def __init__(self, llm_svc: LLMService) -> None:
        self._llm = llm_svc

    async def simulate_round(
        self,
        role: str,
        min_salary: int,
        max_salary: int,
        current_salary: int,
        years_exp: int,
        company: str,
        candidate_message: str,
        conversation_history: list[dict],
        round_num: int,
    ) -> dict[str, Any]:
        system = _NEGOTIATION_SYSTEM.format(
            role=role, min_salary=min_salary, max_salary=max_salary,
            current_salary=current_salary, years_exp=years_exp,
            company=company, round_num=round_num,
        )
        history_str = "\n".join(
            f"{m['role'].upper()}: {m['content']}"
            for m in conversation_history[-6:]
        )
        user_msg = f"CONVERSATION SO FAR:\n{history_str}\n\nCANDIDATE JUST SAID: {candidate_message}"
        result = await self._llm._chat_json(system, user_msg)
        log.info("negotiation_round", round=round_num, status=result.get("negotiation_status"))
        return result

    async def analyze_full_negotiation(
        self,
        target_salary: int,
        conversation_history: list[dict],
    ) -> dict[str, Any]:
        history_str = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in conversation_history)
        user_msg = f"TARGET SALARY: ${target_salary}k\n\nFULL CONVERSATION:\n{history_str}"
        return await self._llm._chat_json(_NEGOTIATION_ANALYSIS_PROMPT, user_msg)

    def get_starter_tips(self) -> list[str]:
        return NEGOTIATION_TIPS
