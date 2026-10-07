from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.core.exceptions import LLMServiceException, NotFoundException, SessionNotFoundException
from app.database import get_db
from app.models.advanced import CodingChallenge
from app.models.interview_session import InterviewSession
from app.services.audit_service import record_audit_event
from app.services.code_sandbox import IsolatedCodeSandbox, SandboxExecutionResult
from app.services.llm_service import LLMService

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/coding", tags=["Coding Interview Sandbox"])

_CHALLENGE_GEN_PROMPT = """
You are an expert technical interviewer at a top tech company.
Generate a realistic coding challenge appropriate for the given difficulty and language.
The problem must include both visible public test cases and hidden edge-case test cases (boundary values, empty collections, negative inputs, large numbers).

Return ONLY valid JSON:
{
  "title": str,
  "description": str,
  "examples": [{"input": str, "output": str, "explanation": str}],
  "constraints": [str],
  "hints": [str],
  "starter_code": str,
  "solution_code": str,
  "entry_point": str,
  "test_cases": [
    {"input": any, "expected_output": any, "is_public": bool}
  ],
  "time_complexity": str,
  "space_complexity": str,
  "tags": [str]
}
"""

_CODE_REVIEW_PROMPT = """
You are a senior software engineer performing a thorough code review.
Analyze the submitted code for correctness, efficiency, readability, and best practices.

Return ONLY valid JSON:
{
  "readability_score": float 0-1,
  "best_practices_score": float 0-1,
  "bugs_found": [{"line": int, "issue": str, "severity": "critical"|"warning"|"info", "fix": str}],
  "improvements": [str],
  "strengths": [str],
  "overall_feedback": str,
  "would_pass_interview": bool
}
"""


class ChallengeGenerateRequest(BaseModel):
    session_id: UUID
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    language: str = Field(default="python", pattern="^(python|javascript|typescript|java|cpp|go|sql)$")
    topic_hint: str | None = None


class CodeRunRequest(BaseModel):
    challenge_id: UUID
    code: str = Field(..., min_length=1, max_length=50_000)
    language: str = Field(default="python")
    custom_test_case: dict[str, Any] | None = None


class CodeSubmitRequest(BaseModel):
    challenge_id: UUID
    code: str = Field(..., min_length=1, max_length=50_000)
    language: str = Field(default="python")


@router.post("/generate", response_model=dict, status_code=201)
async def generate_challenge(
    body: ChallengeGenerateRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """AI-generated coding challenge tailored to session context, skill gaps, and difficulty."""
    session = await db.get(InterviewSession, body.session_id)
    if session is None or session.user_id != current_user.id:
        raise SessionNotFoundException()

    llm = LLMService()
    user_msg = (
        f"DIFFICULTY: {body.difficulty}\n"
        f"LANGUAGE: {body.language}\n"
        f"TOPIC HINT: {body.topic_hint or 'Data structures, algorithms, and systems engineering'}\n"
        f"INTERVIEW CONTEXT: Technical coding round at a tier-1 technology company"
    )

    try:
        challenge_data = await llm._chat_json(_CHALLENGE_GEN_PROMPT, user_msg)
    except Exception as exc:
        log.warn("llm_challenge_gen_failed_fallback", error=str(exc))
        challenge_data = _get_default_challenge(body.difficulty, body.language)

    entry_point = challenge_data.get("entry_point") or "solution"
    test_cases = challenge_data.get("test_cases", [])

    challenge = CodingChallenge(
        session_id=body.session_id,
        title=challenge_data.get("title", "Coding Challenge"),
        description=challenge_data.get("description", ""),
        difficulty=body.difficulty,
        language=body.language,
        starter_code=challenge_data.get("starter_code", f"def {entry_point}():\n    pass\n"),
        solution_code=challenge_data.get("solution_code"),
        test_cases=test_cases,
        constraints=challenge_data.get("constraints", []),
        hints=challenge_data.get("hints", []),
        time_limit_minutes=30,
    )
    db.add(challenge)
    await db.commit()
    await db.refresh(challenge)

    public_test_cases = [
        tc for tc in test_cases if tc.get("is_public", True)
    ]

    log.info("challenge_generated", id=str(challenge.id), difficulty=body.difficulty)
    return {
        "challenge_id": str(challenge.id),
        "title": challenge.title,
        "description": challenge.description,
        "difficulty": challenge.difficulty,
        "language": challenge.language,
        "starter_code": challenge.starter_code,
        "constraints": challenge.constraints,
        "hints": [],  # Hidden initially, revealed progressively
        "test_cases": public_test_cases,
        "time_limit_minutes": challenge.time_limit_minutes,
        "examples": challenge_data.get("examples", []),
        "tags": challenge_data.get("tags", []),
    }


@router.post("/run-tests", response_model=dict)
async def run_tests(
    body: CodeRunRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Execute code in isolated sandbox against visible test cases only (without submitting)."""
    challenge = await db.get(CodingChallenge, body.challenge_id)
    if challenge is None:
        raise NotFoundException("Challenge not found")

    public_tests = [tc for tc in challenge.test_cases if tc.get("is_public", True)]
    if body.custom_test_case:
        custom_tc = dict(body.custom_test_case)
        custom_tc["is_public"] = True
        public_tests.append(custom_tc)

    sandbox = IsolatedCodeSandbox(default_timeout_s=3.0)
    result: SandboxExecutionResult = await sandbox.execute(
        code=body.code,
        test_cases=public_tests,
        language=body.language,
    )

    return result.to_dict(mask_hidden=False)


@router.post("/submit", response_model=dict)
async def submit_code(
    body: CodeSubmitRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Execute code against ALL test cases (visible + hidden edge cases) and generate comprehensive review."""
    challenge = await db.get(CodingChallenge, body.challenge_id)
    if challenge is None:
        raise NotFoundException("Challenge not found")

    # 1. Run in Isolated Subprocess Sandbox against ALL test cases
    sandbox = IsolatedCodeSandbox(default_timeout_s=3.5)
    sandbox_res: SandboxExecutionResult = await sandbox.execute(
        code=body.code,
        test_cases=challenge.test_cases,
        language=body.language,
    )

    # 2. LLM Code Quality & Readability Review
    llm = LLMService()
    review_context = (
        f"PROBLEM TITLE: {challenge.title}\n"
        f"PROBLEM DESCRIPTION: {challenge.description}\n"
        f"DIFFICULTY: {challenge.difficulty}\n\n"
        f"SUBMITTED CODE:\n```{body.language}\n{body.code}\n```\n\n"
        f"SANDBOX RESULTS:\n"
        f"Passed: {sandbox_res.passed_tests}/{sandbox_res.total_tests} (Pass rate: {sandbox_res.pass_rate * 100:.1f}%)\n"
        f"Static Time Complexity: {sandbox_res.static_analysis.estimated_time_complexity}\n"
        f"Static Space Complexity: {sandbox_res.static_analysis.estimated_space_complexity}\n"
        f"Execution Time: {sandbox_res.total_execution_time_ms:.1f}ms\n"
        f"Security Passed: {sandbox_res.security_passed}"
    )

    try:
        review = await llm._chat_json(_CODE_REVIEW_PROMPT, review_context)
    except Exception as exc:
        log.warn("code_review_llm_failed_fallback", error=str(exc))
        review = _fallback_code_review(sandbox_res)

    # 3. Composite Scoring Formula:
    # 60% test case pass rate + 20% code quality / AST + 20% LLM readability & best practices
    test_score = sandbox_res.pass_rate * 100.0
    ast_score = sandbox_res.static_analysis.quality_score
    llm_readability = float(review.get("readability_score", 0.75)) * 100.0
    llm_best_practice = float(review.get("best_practices_score", 0.75)) * 100.0
    llm_score = (llm_readability + llm_best_practice) / 2.0

    if not sandbox_res.security_passed:
        composite_score = 0.0
    else:
        composite_score = (test_score * 0.60) + (ast_score * 0.20) + (llm_score * 0.20)

    composite_score = round(max(0.0, min(100.0, composite_score)), 1)
    would_pass = bool(sandbox_res.success and composite_score >= 70.0)

    # Persist in DB
    challenge.submission_code = body.code
    challenge.score = composite_score
    challenge.submitted_at = datetime.now(UTC)
    challenge.submission_result = sandbox_res.to_dict(mask_hidden=True)
    challenge.ai_feedback = {
        "readability_score": round(llm_readability, 1),
        "best_practices_score": round(llm_best_practice, 1),
        "bugs_found": review.get("bugs_found", []),
        "improvements": review.get("improvements", []) + sandbox_res.static_analysis.suggestions,
        "strengths": review.get("strengths", []),
        "overall_feedback": review.get("overall_feedback", "Code evaluation completed."),
        "would_pass_interview": would_pass,
        "time_complexity": sandbox_res.static_analysis.estimated_time_complexity,
        "space_complexity": sandbox_res.static_analysis.estimated_space_complexity,
    }
    db.add(challenge)

    # Record Audit Log
    session = await db.get(InterviewSession, challenge.session_id)
    if session:
        await record_audit_event(
            db=db,
            action="coding.challenge_submitted",
            entity_type="coding_challenge",
            user_id=session.user_id,
            org_id=session.org_id,
            entity_id=str(challenge.id),
            payload={
                "score": composite_score,
                "passed_tests": sandbox_res.passed_tests,
                "total_tests": sandbox_res.total_tests,
                "pass_rate": sandbox_res.pass_rate,
                "time_complexity": sandbox_res.static_analysis.estimated_time_complexity,
            },
        )

    await db.commit()
    await db.refresh(challenge)

    return {
        "challenge_id": str(challenge.id),
        "score": composite_score,
        "passed_tests": sandbox_res.passed_tests,
        "total_tests": sandbox_res.total_tests,
        "pass_rate": round(sandbox_res.pass_rate * 100, 1),
        "test_results": [r.to_dict(mask_hidden=True) for r in sandbox_res.test_results],
        "static_analysis": {
            "estimated_time_complexity": sandbox_res.static_analysis.estimated_time_complexity,
            "estimated_space_complexity": sandbox_res.static_analysis.estimated_space_complexity,
            "cyclomatic_complexity": sandbox_res.static_analysis.cyclomatic_complexity,
            "lines_of_code": sandbox_res.static_analysis.lines_of_code,
            "quality_score": round(sandbox_res.static_analysis.quality_score, 1),
            "suggestions": sandbox_res.static_analysis.suggestions,
        },
        "readability_score": round(llm_readability, 1),
        "best_practices_score": round(llm_best_practice, 1),
        "bugs_found": review.get("bugs_found", []),
        "improvements": challenge.ai_feedback["improvements"],
        "strengths": review.get("strengths", []),
        "overall_feedback": review.get("overall_feedback", "Code reviewed."),
        "would_pass_interview": would_pass,
        "model_solution": challenge.solution_code if would_pass else None,
    }


@router.get("/hint/{challenge_id}")
async def get_hint(
    challenge_id: UUID,
    hint_index: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Reveal a progressive hint for the challenge."""
    challenge = await db.get(CodingChallenge, challenge_id)
    if challenge is None:
        raise NotFoundException("Challenge not found")
    hints = challenge.hints or []
    if hint_index >= len(hints):
        return {"hint": None, "message": "No more hints available", "total_hints": len(hints)}
    return {"hint": hints[hint_index], "hint_index": hint_index, "total_hints": len(hints)}


def _get_default_challenge(difficulty: str, language: str) -> dict[str, Any]:
    """Default fallback coding challenge with visible and hidden test cases."""
    return {
        "title": "Two Sum with Target Index Search",
        "description": "Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to target. Each input will have exactly one solution.",
        "starter_code": "def two_sum(nums, target):\n    # Write your solution here\n    pass\n",
        "solution_code": "def two_sum(nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        complement = target - num\n        if complement in seen:\n            return [seen[complement], i]\n        seen[num] = i\n    return []\n",
        "entry_point": "two_sum",
        "constraints": ["2 <= len(nums) <= 10^4", "-10^9 <= nums[i] <= 10^9", "Exactly one valid answer exists."],
        "hints": [
            "A brute force O(n^2) approach checks all pairs.",
            "Can you use a hash map to look up complements in O(1) time?",
        ],
        "test_cases": [
            {"input": {"nums": [2, 7, 11, 15], "target": 9}, "expected_output": [0, 1], "is_public": True},
            {"input": {"nums": [3, 2, 4], "target": 6}, "expected_output": [1, 2], "is_public": True},
            {"input": {"nums": [3, 3], "target": 6}, "expected_output": [0, 1], "is_public": False},
            {"input": {"nums": [-1, -2, -3, -4, -5], "target": -8}, "expected_output": [2, 4], "is_public": False},
        ],
        "examples": [
            {"input": "nums = [2,7,11,15], target = 9", "output": "[0, 1]", "explanation": "nums[0] + nums[1] == 9"},
        ],
        "tags": ["Array", "Hash Table", "Algorithms"],
    }


def _fallback_code_review(sandbox_res: SandboxExecutionResult) -> dict[str, Any]:
    """Offline heuristic code review when LLM is unavailable."""
    return {
        "readability_score": 0.85 if sandbox_res.static_analysis.lines_of_code < 60 else 0.70,
        "best_practices_score": 0.90 if sandbox_res.static_analysis.cyclomatic_complexity < 6 else 0.65,
        "bugs_found": [] if sandbox_res.success else [{"line": 1, "issue": "One or more edge cases failed assertion.", "severity": "warning", "fix": "Check zero, negative, or duplicate input cases."}],
        "improvements": sandbox_res.static_analysis.suggestions,
        "strengths": ["Clean function declaration", "Correct output types"] if sandbox_res.passed_tests > 0 else [],
        "overall_feedback": f"Solution passed {sandbox_res.passed_tests}/{sandbox_res.total_tests} test cases with {sandbox_res.static_analysis.estimated_time_complexity} time complexity.",
        "would_pass_interview": sandbox_res.success,
    }
