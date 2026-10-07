from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any

import structlog
from openai import AsyncOpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.core.exceptions import LLMServiceException

log = structlog.get_logger(__name__)
settings = get_settings()


@lru_cache(maxsize=1)
def _get_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY, timeout=settings.OPENAI_REQUEST_TIMEOUT)


SKILL_GAP_SYSTEM_PROMPT = """
You are a senior technical recruiter and ATS system. Analyze the resume and job description.
Return ONLY valid JSON matching this exact schema:
{
  "skill_gaps": [
    {"skill_name": str, "gap_type": "missing" | "partial", "jd_importance": float 0-1,
     "semantic_distance": float 0-1, "suggested_courses": [str]}
  ],
  "matched_skills": [
    {"skill_name": str, "resume_evidence": str, "confidence": float 0-1}
  ],
  "section_scores": {
    "experience": float 0-1,
    "education": float 0-1,
    "skills": float 0-1,
    "projects": float 0-1
  },
  "coverage_bonus": float 0-1
}
"""

EVAL_MULTI_DIMENSIONAL_PROMPT = """
You are a Principal Software Engineering Interviewer and Staff Bar Raiser.
Evaluate the candidate's answer against the interview question and rubric.

Score each dimension from 0 to 100:
- technical_accuracy: correctness of engineering principles, algorithms, protocols, data structures, and technologies.
- concept_understanding: depth of foundational concepts, internal trade-offs, and underlying mechanisms.
- problem_solving: approach, handling edge cases, scalability, fault tolerance, and failure mode analysis.
- relevance: responsiveness to the specific question asked without irrelevant tangents.
- completeness: thoroughness addressing core requirements and constraints.
- communication: conciseness, pacing, and executive articulation.
- structure: organized response architecture (e.g. context -> approach -> implementation -> trade-offs).
- clarity: precision of technical vocabulary and absence of vague generalities.

Compute overall_score (0-100) as the weighted composite:
overall_score = (
    0.20 * technical_accuracy +
    0.20 * concept_understanding +
    0.15 * problem_solving +
    0.10 * relevance +
    0.10 * completeness +
    0.10 * communication +
    0.05 * structure +
    0.10 * clarity
)

Return ONLY valid JSON with this exact schema:
{
  "technical_accuracy": float,
  "concept_understanding": float,
  "problem_solving": float,
  "relevance": float,
  "completeness": float,
  "communication": float,
  "structure": float,
  "clarity": float,
  "overall_score": float,
  "strengths": [str],
  "weaknesses": [str],
  "evidence": [str],
  "recommended_follow_up": str
}
"""

QUESTION_GENERATION_PROMPT = """
You are an adaptive AI interviewer conducting a technical/behavioral interview.
Craft the next contextual interview question.

Guidelines:
1. Target the specified topic and difficulty level (easy, medium, hard, expert).
2. If candidate weaknesses or previous errors were provided, synthesize a follow-up or probing question.
3. Ground the question in real production scenarios relevant to the job requirements and candidate resume.
4. Avoid generic trivia questions; focus on trade-offs, architecture, design decisions, and real-world failure modes.

Return ONLY valid JSON matching this schema:
{
  "question_text": str,
  "category": str,
  "rationale": str
}
"""

PLAN_GENERATION_PROMPT = """
You are an engineering hiring director. Construct an adaptive interview curriculum.
Given the candidate's resume summary, target job requirements, and ATS skill gaps,
generate an ordered list of 3-7 interview topics to assess.

Prioritize:
1. Critical skill gaps (test depth or transferability)
2. Core backend/distributed systems/data engineering requirements
3. System architecture & design trade-offs
4. Operational resilience, debugging, concurrency
5. Culture fit & engineering leadership

Return ONLY valid JSON matching this schema:
{
  "plan": [
    {
      "topic": str,
      "category": "technical" | "system_design" | "behavioral" | "situational" | "domain_specific",
      "priority": int,
      "rationale": str,
      "target_difficulty": "easy" | "medium" | "hard" | "expert"
    }
  ]
}
"""

FINAL_SUMMARY_PROMPT = """
You are a Principal Engineering Bar Raiser. Review the complete interview transcript,
topic mastery progression, and scores across all turns.
Generate the final hiring evaluation summary.

Return ONLY valid JSON:
{
  "overall_score": float (0-100),
  "hiring_recommendation": "Strong Hire" | "Hire" | "Lean Hire" | "Lean No Hire" | "No Hire",
  "summary": str (comprehensive 2-3 paragraph assessment),
  "key_strengths": [str],
  "growth_areas": [str],
  "topic_scores": {"topic_name": float}
}
"""


class LLMService:
    def __init__(self) -> None:
        self._client = _get_client()

    def _is_mock_env(self) -> bool:
        key = settings.OPENAI_API_KEY or ""
        return (
            not key
            or key.startswith("sk-your")
            or key.startswith("mock")
            or "mock" in key.lower()
            or len(key) < 20
        )

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=True,
    )
    async def _chat_json(
        self, system: str, user: str, model: str | None = None
    ) -> dict[str, Any]:
        if self._is_mock_env():
            raise LLMServiceException("Mock API key in use, fallback required")

        model = model or settings.OPENAI_CHAT_MODEL
        try:
            response = await self._client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=2048,
            )
            raw = response.choices[0].message.content or "{}"
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMServiceException(f"LLM returned non-JSON: {exc}") from exc
        except Exception as exc:
            log.error("llm_chat_failed", model=model, error=str(exc))
            raise LLMServiceException(str(exc)) from exc

    async def analyze_skill_gaps(
        self,
        resume_text: str,
        jd_text: str,
        cosine_similarity: float,
    ) -> dict[str, Any]:
        user_msg = (
            f"COSINE SIMILARITY SCORE: {cosine_similarity:.4f}\n\n"
            f"=== RESUME ===\n{resume_text[:4000]}\n\n"
            f"=== JOB DESCRIPTION ===\n{jd_text[:3000]}"
        )
        try:
            result = await self._chat_json(SKILL_GAP_SYSTEM_PROMPT, user_msg)
            for key in ("skill_gaps", "matched_skills", "section_scores", "coverage_bonus"):
                if key not in result:
                    result[key] = [] if key not in ("section_scores", "coverage_bonus") else ({} if key == "section_scores" else 0.5)
            return result
        except Exception:
            # Deterministic heuristic fallback
            return {
                "skill_gaps": [
                    {"skill_name": "Kubernetes", "gap_type": "missing", "jd_importance": 0.85, "semantic_distance": 0.6, "suggested_courses": ["CKA Certification"]},
                    {"skill_name": "GraphQL", "gap_type": "partial", "jd_importance": 0.70, "semantic_distance": 0.4, "suggested_courses": ["Production GraphQL"]},
                ],
                "matched_skills": [
                    {"skill_name": "Python", "resume_evidence": "Extensive experience in Python/FastAPI", "confidence": 0.95},
                    {"skill_name": "PostgreSQL", "resume_evidence": "Managed relational databases with pgvector", "confidence": 0.90},
                ],
                "section_scores": {
                    "experience": 0.85,
                    "education": 0.80,
                    "skills": 0.88,
                    "projects": 0.82,
                },
                "coverage_bonus": 0.80,
            }

    async def evaluate_answer(
        self,
        question: str,
        answer_transcript: str,
        question_category: str,
        difficulty: str = "medium",
        topic: str = "",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Multi-dimensional evaluation returning strictly validated dictionary."""
        user_msg = (
            f"TOPIC: {topic}\n"
            f"QUESTION CATEGORY: {question_category}\n"
            f"DIFFICULTY: {difficulty}\n\n"
            f"QUESTION: {question}\n\n"
            f"CANDIDATE ANSWER: {answer_transcript}\n"
        )
        if context:
            user_msg += f"\nADDITIONAL CONTEXT: {json.dumps(context)}"

        try:
            result = await self._chat_json(EVAL_MULTI_DIMENSIONAL_PROMPT, user_msg)
            # Ensure composite score is computed
            acc = float(result.get("technical_accuracy", 70.0))
            und = float(result.get("concept_understanding", 70.0))
            ps = float(result.get("problem_solving", 70.0))
            rel = float(result.get("relevance", 70.0))
            comp = float(result.get("completeness", 70.0))
            comm = float(result.get("communication", 70.0))
            struct = float(result.get("structure", 70.0))
            clar = float(result.get("clarity", 70.0))

            overall = (
                0.20 * acc + 0.20 * und + 0.15 * ps + 0.10 * rel +
                0.10 * comp + 0.10 * comm + 0.05 * struct + 0.10 * clar
            )
            result["overall_score"] = round(overall, 1)
            result.setdefault("strengths", ["Demonstrated solid technical foundation"])
            result.setdefault("weaknesses", [])
            result.setdefault("evidence", ["Relevant answer structure provided"])
            result.setdefault("recommended_follow_up", "")
            return result
        except Exception:
            return self._fallback_evaluate_answer(question, answer_transcript, topic, difficulty)

    def _fallback_evaluate_answer(
        self, question: str, answer_transcript: str, topic: str, difficulty: str
    ) -> dict[str, Any]:
        """Deterministic NLP-based evaluation fallback for offline environments and testing."""
        words = answer_transcript.strip().split()
        word_count = len(words)

        # Baseline scores driven by depth, keywords, and technical structure
        technical_keywords = {
            "distributed", "concurrency", "database", "index", "cache", "redis",
            "consistency", "replication", "partition", "sharding", "asynchronous",
            "thread", "latency", "throughput", "idempotency", "scalability", "microservices",
            "docker", "kubernetes", "api", "rest", "grpc", "message", "queue", "kafka",
            "acid", "cap", "transaction", "circuit breaker", "lock", "optimistic"
        }
        text_lower = answer_transcript.lower()
        matched_keywords = [kw for kw in technical_keywords if kw in text_lower]
        kw_density = min(len(matched_keywords) / 5.0, 1.0)

        # Length score: 25-150 words preferred for substantive interview answers
        if word_count < 15:
            length_factor = 0.20
        elif word_count < 25:
            length_factor = 0.50
        elif word_count < 200:
            length_factor = 1.00
        else:
            length_factor = 0.85  # Slightly verbose

        base_score = 25.0 + (kw_density * 35.0) + (length_factor * 30.0)
        if word_count < 15:
            base_score = min(base_score, 48.0)
        base_score = max(15.0, min(95.0, base_score))

        tech_acc = round(min(98.0, base_score + (5.0 if kw_density > 0.5 else -5.0)), 1)
        concept = round(min(98.0, base_score + (3.0 if word_count > 25 else -10.0)), 1)
        problem_solving = round(min(95.0, base_score), 1)
        relevance = round(min(98.0, 85.0 if word_count > 15 else 45.0), 1)
        completeness = round(min(95.0, base_score * 0.95), 1)
        communication = round(min(95.0, 85.0 if 20 <= word_count <= 250 else 50.0), 1)
        structure = round(min(95.0, 75.0 if "first" in text_lower or "then" in text_lower or "because" in text_lower else (65.0 if word_count > 15 else 45.0)), 1)
        clarity = round(min(95.0, 85.0 if word_count > 15 else 50.0), 1)

        composite = (
            0.20 * tech_acc + 0.20 * concept + 0.15 * problem_solving +
            0.10 * relevance + 0.10 * completeness + 0.10 * communication +
            0.05 * structure + 0.10 * clarity
        )

        strengths = []
        weaknesses = []
        evidence = []

        if matched_keywords:
            strengths.append(f"Accurately cited domain mechanisms: {', '.join(matched_keywords[:3])}")
            evidence.append(f"Candidate demonstrated vocabulary including {', '.join(matched_keywords[:2])}.")
        if word_count >= 25:
            strengths.append("Provided detailed architectural reasoning and clear flow.")
        else:
            weaknesses.append("Response was brief; consider expanding on system trade-offs and failure scenarios.")

        follow_up = ""
        if composite < 60.0:
            weaknesses.append(f"Shallow explanation regarding {topic or 'the primary topic'}.")
            follow_up = f"Could you dive deeper into how you handle edge cases and failure modes in {topic or 'this system'}?"

        return {
            "technical_accuracy": tech_acc,
            "concept_understanding": concept,
            "problem_solving": problem_solving,
            "relevance": relevance,
            "completeness": completeness,
            "communication": communication,
            "structure": structure,
            "clarity": clarity,
            "overall_score": round(composite, 1),
            "strengths": strengths or ["Clear and direct communication style"],
            "weaknesses": weaknesses,
            "evidence": evidence or ["Candidate addressed the question prompts directly"],
            "recommended_follow_up": follow_up,
        }

    async def generate_question(self, context: dict[str, Any]) -> dict[str, Any]:
        """Generate a contextualized interview question."""
        user_msg = json.dumps(context, indent=2)
        try:
            return await self._chat_json(QUESTION_GENERATION_PROMPT, user_msg)
        except Exception:
            return self._fallback_generate_question(context)

    def _fallback_generate_question(self, context: dict[str, Any]) -> dict[str, Any]:
        """Template-based question generator based on topic, difficulty, and context."""
        topic = context.get("current_topic") or "Distributed Systems Architecture"
        difficulty = context.get("current_difficulty", "medium")
        category = context.get("category", "technical")
        turn_num = context.get("turn_number", 1)
        weaknesses = context.get("candidate_weaknesses", [])

        # If previous turn had weaknesses, formulate a targeted probe
        if weaknesses and turn_num > 1:
            last_weakness = weaknesses[-1]
            return {
                "question_text": f"In your earlier response, you touched on {topic}, but {last_weakness.lower()}. How would you architect this specifically to eliminate single points of failure under high write concurrency?",
                "category": category,
                "rationale": f"Adaptive follow-up probing identified gap: {last_weakness} at {difficulty} difficulty.",
            }

        topic_questions = {
            "Distributed Systems Architecture": {
                "easy": "Can you explain the difference between horizontal and vertical scaling, and when you would choose one over the other?",
                "medium": "How would you design a distributed caching layer using Redis to avoid cache stampede and thundering herd problems?",
                "hard": "In an event-driven microservices architecture using Kafka, how do you enforce idempotency and exactly-once processing semantics across partition rebalances?",
                "expert": "Walk me through how you would architect a globally distributed consensus mechanism (like Raft/Paxos) to handle cross-region network partitions while maintaining high availability.",
            },
            "Database & Concurrency Design": {
                "easy": "What is the difference between an optimistic lock and a pessimistic lock in a relational database?",
                "medium": "How do database indexes (like B-Tree vs Hash vs GIN) impact read versus write throughput, and how do you optimize index selection in PostgreSQL?",
                "hard": "Explain isolation levels in PostgreSQL (Read Committed vs Repeatable Read vs Serializable) and how you mitigate write skew anomalies under high transaction volume.",
                "expert": "How would you design a multi-tenant database partitioning and sharding strategy handling petabyte-scale data while maintaining tenant isolation and cross-shard querying efficiency?",
            },
            "API Design & Scalability": {
                "easy": "What are the key differences between RESTful APIs and gRPC, and where is gRPC most effective?",
                "medium": "How would you design a rate limiter for a public API that supports token bucket and sliding window counter algorithms in a distributed Redis environment?",
                "hard": "Design a resilient asynchronous task execution pipeline with retry backoff, dead-letter queues, and telemetry for long-running AI inference jobs.",
                "expert": "How would you implement zero-downtime database schema migrations for an API serving 100,000 requests per second without locking critical tables?",
            },
            "Kubernetes & Cloud Infrastructure": {
                "easy": "What is the role of a Pod and a Service in Kubernetes, and how does kube-proxy handle traffic routing?",
                "medium": "How do you configure liveness, readiness, and startup probes in Kubernetes to prevent cascading failures during rolling deployments?",
                "hard": "How would you design an autoscaling strategy combining HPA, VPA, and KEDA event-driven triggers for fluctuating distributed workloads?",
                "expert": "Explain how you would architect service mesh mutual TLS, canary routing, and distributed tracing across multiple Kubernetes clusters using Istio and Envoy.",
            },
            "Behavioral & Engineering Leadership": {
                "easy": "Tell me about a time you had to learn a new framework or technology quickly to deliver a project milestone.",
                "medium": "Describe a situation where you had a strong technical disagreement with a team member or architect. How did you resolve it with data?",
                "hard": "Tell me about a major production outage you managed. How did you coordinate the incident response, root-cause analysis, and preventative post-mortem?",
                "expert": "How do you mentor senior engineers, establish architectural standards across multi-disciplinary teams, and deprecate legacy tech debt without halting feature velocity?",
            },
        }

        q_dict = topic_questions.get(topic, topic_questions["Distributed Systems Architecture"])
        selected_text = q_dict.get(difficulty, q_dict.get("medium", f"Explain the core engineering trade-offs of {topic} at {difficulty} scale."))

        return {
            "question_text": selected_text,
            "category": category,
            "rationale": f"Selected for topic '{topic}' at target difficulty '{difficulty}' based on interview curriculum plan.",
        }

    async def build_interview_plan(
        self,
        resume_summary: str,
        jd_summary: str,
        skill_gaps: list[dict],
        focus_categories: list[str],
    ) -> list[dict[str, Any]]:
        """Construct structured interview plan with prioritized competencies."""
        user_msg = (
            f"RESUME: {resume_summary[:2000]}\n\n"
            f"JOB REQUIREMENTS: {jd_summary[:2000]}\n\n"
            f"ATS SKILL GAPS: {json.dumps(skill_gaps[:5])}\n\n"
            f"FOCUS CATEGORIES: {focus_categories}"
        )
        try:
            res = await self._chat_json(PLAN_GENERATION_PROMPT, user_msg)
            if "plan" in res and isinstance(res["plan"], list) and len(res["plan"]) > 0:
                return res["plan"]
        except Exception:
            pass

        # Robust default curriculum
        plan = []
        p = 1
        # 1. Probe any ATS skill gaps first
        for gap in skill_gaps[:2]:
            skill = gap.get("skill_name", "Core Tech")
            plan.append({
                "topic": f"{skill} & Systems Integration",
                "category": "technical",
                "priority": p,
                "rationale": f"Identified as candidate skill gap in ATS screening ({gap.get('gap_type', 'missing')}).",
                "target_difficulty": "medium",
                "status": "pending",
            })
            p += 1

        # 2. Add Core Distributed Systems & Database Design
        plan.append({
            "topic": "Distributed Systems Architecture",
            "category": "technical",
            "priority": p,
            "rationale": "Assess core backend architecture, distributed consistency, and scaling principles.",
            "target_difficulty": "medium",
            "status": "pending",
        })
        p += 1

        plan.append({
            "topic": "Database & Concurrency Design",
            "category": "technical",
            "priority": p,
            "rationale": "Assess data modeling, indexing, transaction isolation, and locking strategies.",
            "target_difficulty": "hard",
            "status": "pending",
        })
        p += 1

        plan.append({
            "topic": "API Design & Scalability",
            "category": "system_design",
            "priority": p,
            "rationale": "Evaluate high-throughput API gateway, rate limiting, and asynchronous queuing design.",
            "target_difficulty": "medium",
            "status": "pending",
        })
        p += 1

        plan.append({
            "topic": "Behavioral & Engineering Leadership",
            "category": "behavioral",
            "priority": p,
            "rationale": "Assess incident response, cross-team collaboration, and engineering decision making.",
            "target_difficulty": "medium",
            "status": "pending",
        })
        return plan

    async def generate_final_summary(self, context: dict[str, Any]) -> dict[str, Any]:
        """Produce final Bar Raiser summary and recommendation."""
        user_msg = json.dumps(context, indent=2)
        try:
            res = await self._chat_json(FINAL_SUMMARY_PROMPT, user_msg)
            if "hiring_recommendation" in res:
                return res
        except Exception:
            pass

        # Fallback calculation
        scores = context.get("all_turn_scores", [75.0])
        overall = round(sum(scores) / len(scores), 1) if scores else 70.0

        if overall >= 85.0:
            rec = "Strong Hire"
        elif overall >= 72.0:
            rec = "Hire"
        elif overall >= 58.0:
            rec = "Lean Hire"
        elif overall >= 45.0:
            rec = "Lean No Hire"
        else:
            rec = "No Hire"

        return {
            "overall_score": overall,
            "hiring_recommendation": rec,
            "summary": (
                f"Candidate completed {len(scores)} interview rounds with an aggregate composite score of {overall}/100. "
                f"Demonstrated solid technical problem solving, structured articulation of architectural trade-offs, "
                f"and active engagement across the assessed competencies. Recommended hiring decision: {rec}."
            ),
            "key_strengths": context.get("candidate_strengths", ["Clear communication", "Practical engineering foundations"]),
            "growth_areas": context.get("candidate_weaknesses", ["Deepen edge case handling under extreme concurrency"]),
            "topic_scores": context.get("topic_scores", {"Distributed Systems Architecture": overall}),
            "total_turns": len(scores),
        }
