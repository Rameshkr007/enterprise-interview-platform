from __future__ import annotations

import json
from typing import Any

import structlog
from app.services.llm_service import LLMService

log = structlog.get_logger(__name__)

# ── Company Interview DNA ─────────────────────────────────────────────────────
COMPANY_PROFILES: dict[str, dict[str, Any]] = {
    "google": {
        "name": "Google",
        "logo_emoji": "🔍",
        "focus_areas": ["algorithms", "system_design", "behavioral", "culture_fit"],
        "behavioral_framework": "STAR",
        "known_values": ["User focus", "Think big", "Data-driven", "Inclusive"],
        "interview_rounds": ["Phone screen", "Technical x3", "System design", "Googleyness"],
        "question_style": "Open-ended with follow-ups on edge cases and optimization",
        "avg_difficulty": "hard",
        "famous_questions": [
            "Design Google Search",
            "Find the kth largest element in a stream",
            "Tell me about a time you had to influence without authority",
        ],
        "red_flags": ["Not asking clarifying questions", "No time/space complexity analysis", "Never heard of Big-O"],
        "culture_signals": ["intellectual humility", "collaboration", "impact at scale"],
    },
    "amazon": {
        "name": "Amazon",
        "logo_emoji": "📦",
        "focus_areas": ["behavioral", "technical", "system_design"],
        "behavioral_framework": "STAR",
        "known_values": [
            "Customer Obsession", "Ownership", "Invent and Simplify",
            "Are Right A Lot", "Learn and Be Curious", "Hire and Develop the Best",
            "Insist on the Highest Standards", "Think Big", "Bias for Action",
            "Frugality", "Earn Trust", "Dive Deep", "Have Backbone; Disagree and Commit",
            "Deliver Results",
        ],
        "interview_rounds": ["Online assessment", "Phone screen", "Loop x4-6"],
        "question_style": "Leadership Principle-anchored behavioral questions (mandatory)",
        "avg_difficulty": "hard",
        "famous_questions": [
            "Tell me about a time you disagreed with your manager",
            "Design Amazon's warehouse inventory system",
            "Tell me about a time you failed",
        ],
        "red_flags": ["No specific examples", "Team wins without personal contribution", "Never failed"],
        "culture_signals": ["ownership", "frugality", "high standards"],
    },
    "microsoft": {
        "name": "Microsoft",
        "logo_emoji": "🪟",
        "focus_areas": ["technical", "behavioral", "system_design", "culture_fit"],
        "behavioral_framework": "STAR",
        "known_values": ["Growth mindset", "Empowerment", "Inclusivity", "One Microsoft"],
        "interview_rounds": ["Recruiter screen", "Technical x3", "As-appropriate (hiring manager)"],
        "question_style": "Collaborative problem-solving with emphasis on growth mindset",
        "avg_difficulty": "medium",
        "famous_questions": [
            "Design a URL shortener",
            "Tell me about a time you had to learn something quickly",
            "How would you improve Microsoft Teams?",
        ],
        "red_flags": ["Fixed mindset language", "Blaming others", "No curiosity"],
        "culture_signals": ["growth mindset", "collaboration", "customer empathy"],
    },
    "meta": {
        "name": "Meta",
        "logo_emoji": "🌐",
        "focus_areas": ["algorithms", "system_design", "behavioral"],
        "behavioral_framework": "SOAR",
        "known_values": ["Move fast", "Be bold", "Focus on impact", "Build social value"],
        "interview_rounds": ["Recruiter", "Technical x2", "System design", "Behavioral"],
        "question_style": "Speed and correctness in coding; scale in design",
        "avg_difficulty": "hard",
        "famous_questions": [
            "Design Facebook's news feed",
            "Find if a tree is symmetric",
            "Tell me about your most impactful project",
        ],
        "red_flags": ["Slow implementation", "No scalability thinking", "Unclear impact metrics"],
        "culture_signals": ["impact", "speed", "boldness"],
    },
    "startup": {
        "name": "Early-Stage Startup",
        "logo_emoji": "🚀",
        "focus_areas": ["culture_fit", "technical", "situational"],
        "behavioral_framework": "SOAR",
        "known_values": ["Ownership", "Hustle", "Adaptability", "Mission alignment"],
        "interview_rounds": ["Founder call", "Technical take-home", "Team fit"],
        "question_style": "Practical, hands-on problem solving and culture fit",
        "avg_difficulty": "medium",
        "famous_questions": [
            "What do you want to build in the next 5 years?",
            "How would you handle wearing multiple hats?",
            "Tell me about a time you shipped something with limited resources",
        ],
        "red_flags": ["Needs extensive process", "Risk averse", "No side projects"],
        "culture_signals": ["ownership", "resourcefulness", "mission driven"],
    },
}

_COMPANY_QUESTION_PROMPT = """
You are an expert interviewer preparing a candidate specifically for a {company} interview.
Generate ONE hyper-realistic {company} interview question based on their Leadership Principles / culture.

Context:
- Behavioral Framework: {framework}
- Company Values: {values}
- Question Style: {style}
- Current Difficulty: {difficulty}
- Focus Area: {focus}
- Candidate's Skill Gaps: {gaps}

Return ONLY JSON:
{{
  "question_text": str,
  "category": str,
  "company_principle": str,
  "what_they_look_for": str,
  "rationale": str,
  "red_flags_to_avoid": [str],
  "model_answer_structure": str
}}
"""

_CULTURE_FIT_PROMPT = """
You are evaluating a candidate's answer for cultural fit at {company}.
Score against their known values: {values}
Behavioral framework expected: {framework}

Question: {question}
Answer: {answer}

Return ONLY JSON:
{{
  "culture_fit_score": float 0-1,
  "principle_alignment": [{{"principle": str, "score": float, "evidence": str}}],
  "framework_used": bool,
  "specific_examples_given": bool,
  "impact_quantified": bool,
  "feedback": str,
  "what_would_impress_them_more": str
}}
"""


class CompanyInterviewService:
    """Generates company-specific questions with culture principle alignment scoring."""

    def __init__(self, llm_svc: LLMService) -> None:
        self._llm = llm_svc

    def get_company_profile(self, company_key: str) -> dict[str, Any]:
        profile = COMPANY_PROFILES.get(company_key.lower())
        if not profile:
            raise ValueError(f"Company '{company_key}' not supported. Available: {list(COMPANY_PROFILES.keys())}")
        return profile

    def list_companies(self) -> list[dict[str, Any]]:
        return [
            {
                "key": k,
                "name": v["name"],
                "emoji": v["logo_emoji"],
                "difficulty": v["avg_difficulty"],
                "focus_areas": v["focus_areas"],
            }
            for k, v in COMPANY_PROFILES.items()
        ]

    async def generate_company_question(
        self,
        company_key: str,
        difficulty: str,
        focus_area: str,
        skill_gaps: list[dict],
    ) -> dict[str, Any]:
        profile = self.get_company_profile(company_key)
        prompt = _COMPANY_QUESTION_PROMPT.format(
            company=profile["name"],
            framework=profile["behavioral_framework"],
            values=", ".join(profile["known_values"][:5]),
            style=profile["question_style"],
            difficulty=difficulty,
            focus=focus_area,
            gaps=json.dumps([g.get("skill_name") for g in skill_gaps[:5]]),
        )
        result = await self._llm._chat_json(prompt, "Generate the question now.")
        result["company"] = company_key
        result["company_name"] = profile["name"]
        result["red_flags"] = profile["red_flags"]
        log.info("company_question_generated", company=company_key, category=result.get("category"))
        return result

    async def score_culture_fit(
        self,
        company_key: str,
        question: str,
        answer: str,
    ) -> dict[str, Any]:
        profile = self.get_company_profile(company_key)
        prompt = _CULTURE_FIT_PROMPT.format(
            company=profile["name"],
            values=json.dumps(profile["known_values"]),
            framework=profile["behavioral_framework"],
            question=question,
            answer=answer,
        )
        result = await self._llm._chat_json(prompt, "Evaluate culture fit now.")
        result["company"] = company_key
        result["behavioral_framework"] = profile["behavioral_framework"]
        log.info("culture_fit_scored", company=company_key, score=result.get("culture_fit_score"))
        return result
