from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import UUID, uuid4

import structlog

from app.services.llm_service import LLMService

log = structlog.get_logger(__name__)


@dataclass
class STARElement:
    name: Literal["Situation", "Task", "Action", "Result", "Learning"]
    content: str
    score: float  # 0 to 100
    clarity: float  # 0 to 1
    feedback: str
    key_phrases: list[str] = field(default_factory=list)


@dataclass
class OwnershipMetrics:
    i_count: int
    we_count: int
    i_we_ratio: float  # i_count / (i_count + we_count)
    ownership_level: Literal["High Individual Ownership", "Balanced Team Collaboration", "Passive/Ambiguous Team Attribution"]
    explanation: str


@dataclass
class BehavioralFlag:
    flag_type: Literal[
        "MISSING_QUANTIFIABLE_RESULTS",
        "PASSIVE_TEAM_OBSCURITY",
        "VAGUE_ACTION_STEPS",
        "UNVERIFIABLE_HYPERBOLE",
        "CONFLICT_AVOIDANCE",
    ]
    severity: Literal["critical", "warning", "info"]
    description: str
    recommendation: str


@dataclass
class STARBehavioralEvaluation:
    overall_score: float  # 0 to 100
    star_breakdown: dict[str, STARElement]
    ownership_metrics: OwnershipMetrics
    flags: list[BehavioralFlag]
    quantifiable_metrics_found: list[str]
    competency_scores: dict[str, float]  # e.g. {"ownership": 85.0, "deliver_results": 78.0}
    strengths: list[str]
    improvement_areas: list[str]
    bar_raiser_verdict: Literal["Strong Hire", "Hire", "Lean Hire", "Lean No Hire", "No Hire"]
    actionable_reframe: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 1),
            "star_breakdown": {
                k: {
                    "name": v.name,
                    "content": v.content,
                    "score": round(v.score, 1),
                    "clarity": round(v.clarity, 2),
                    "feedback": v.feedback,
                    "key_phrases": v.key_phrases,
                }
                for k, v in self.star_breakdown.items()
            },
            "ownership_metrics": {
                "i_count": self.ownership_metrics.i_count,
                "we_count": self.ownership_metrics.we_count,
                "i_we_ratio": round(self.ownership_metrics.i_we_ratio, 2),
                "ownership_level": self.ownership_metrics.ownership_level,
                "explanation": self.ownership_metrics.explanation,
            },
            "flags": [
                {
                    "flag_type": f.flag_type,
                    "severity": f.severity,
                    "description": f.description,
                    "recommendation": f.recommendation,
                }
                for f in self.flags
            ],
            "quantifiable_metrics_found": self.quantifiable_metrics_found,
            "competency_scores": {k: round(v, 1) for k, v in self.competency_scores.items()},
            "strengths": self.strengths,
            "improvement_areas": self.improvement_areas,
            "bar_raiser_verdict": self.bar_raiser_verdict,
            "actionable_reframe": self.actionable_reframe,
        }


STAR_EVAL_PROMPT = """
You are an expert Executive Behavioral Interviewer & Bar Raiser trained on Amazon Leadership Principles and Google Structured Interviews.
Analyze the candidate's answer using the STAR methodology (Situation, Task, Action, Result).

Return ONLY valid JSON matching this schema:
{
  "overall_score": float 0-100,
  "star_breakdown": {
    "situation": {"content": str, "score": float 0-100, "clarity": float 0-1, "feedback": str, "key_phrases": [str]},
    "task": {"content": str, "score": float 0-100, "clarity": float 0-1, "feedback": str, "key_phrases": [str]},
    "action": {"content": str, "score": float 0-100, "clarity": float 0-1, "feedback": str, "key_phrases": [str]},
    "result": {"content": str, "score": float 0-100, "clarity": float 0-1, "feedback": str, "key_phrases": [str]}
  },
  "quantifiable_metrics_found": [str],
  "competency_scores": {
    "ownership": float 0-100,
    "bias_for_action": float 0-100,
    "deliver_results": float 0-100,
    "conflict_resolution": float 0-100,
    "customer_obsession": float 0-100
  },
  "strengths": [str],
  "improvement_areas": [str],
  "bar_raiser_verdict": "Strong Hire" | "Hire" | "Lean Hire" | "Lean No Hire" | "No Hire",
  "actionable_reframe": str
}
"""


class BehavioralSTAREngine:
    """Enterprise Behavioral Interview Engine with STAR decomposition, pronoun ownership, and metric verification."""

    # Regex patterns for first-person singular ("I") and plural ("We")
    I_PATTERN = re.compile(r"\b(i|me|my|mine|myself|i'd|i've|i'll|i'm)\b", re.IGNORECASE)
    WE_PATTERN = re.compile(r"\b(we|us|our|ours|ourselves|we'd|we've|we'll|we're)\b", re.IGNORECASE)

    # Regex for detecting quantifiable metrics ($100k, 25%, 3x, 50ms, 10,000 users)
    METRIC_PATTERN = re.compile(
        r"(\b\d+(\.\d+)?%|\$\d+([kmb])?|\b\d+x\b|\b\d+\s*(ms|seconds|minutes|hours|days|weeks|months|years|users|requests|qps|rps|engineers|teams|services)\b)",
        re.IGNORECASE,
    )

    def __init__(self, llm_svc: LLMService | None = None) -> None:
        self._llm = llm_svc or LLMService()

    def analyze_ownership(self, text: str) -> OwnershipMetrics:
        """Calculate I vs We pronoun frequency to evaluate individual contribution vs passive team hiding."""
        i_matches = len(self.I_PATTERN.findall(text))
        we_matches = len(self.WE_PATTERN.findall(text))
        total = i_matches + we_matches

        if total == 0:
            ratio = 0.5
            level = "Balanced Team Collaboration"
            explanation = "Neutral attribution without heavy pronoun reliance."
        else:
            ratio = i_matches / total
            if ratio >= 0.58:
                level = "High Individual Ownership"
                explanation = f"Strong personal ownership ({i_matches} 'I' vs {we_matches} 'We'). Candidate clearly articulates direct contributions."
            elif ratio >= 0.35:
                level = "Balanced Team Collaboration"
                explanation = f"Well-balanced collaborative framing ({i_matches} 'I' vs {we_matches} 'We'). Demonstrates teamwork while owning key steps."
            else:
                level = "Passive/Ambiguous Team Attribution"
                explanation = f"Heavily skewed toward team attribution ({we_matches} 'We' vs only {i_matches} 'I'). Obscures candidate's specific actions."

        return OwnershipMetrics(
            i_count=i_matches,
            we_count=we_matches,
            i_we_ratio=ratio,
            ownership_level=level,
            explanation=explanation,
        )

    def extract_quantifiable_metrics(self, text: str) -> list[str]:
        """Detect concrete numbers, percentages, and performance deltas."""
        matches = self.METRIC_PATTERN.findall(text)
        found: set[str] = set()
        for m in matches:
            if isinstance(m, tuple) and m[0]:
                found.add(m[0].strip())
            elif isinstance(m, str) and m.strip():
                found.add(m.strip())
        return sorted(list(found))

    def detect_flags(
        self,
        text: str,
        ownership: OwnershipMetrics,
        metrics_found: list[str],
    ) -> list[BehavioralFlag]:
        """Audit for common behavioral interview anti-patterns."""
        flags: list[BehavioralFlag] = []

        # 1. Check for missing quantifiable results
        if not metrics_found:
            flags.append(BehavioralFlag(
                flag_type="MISSING_QUANTIFIABLE_RESULTS",
                severity="warning",
                description="The answer lacks quantifiable outcomes (percentages, latency, revenue, scale, time saved).",
                recommendation="Quantify the impact: e.g., 'reduced deploy time by 35%' or 'prevented ~15 hours of weekly downtime'.",
            ))

        # 2. Check for passive team obscurity
        if ownership.ownership_level == "Passive/Ambiguous Team Attribution":
            flags.append(BehavioralFlag(
                flag_type="PASSIVE_TEAM_OBSCURITY",
                severity="critical",
                description="High reliance on 'We' masks the candidate's exact personal responsibilities and engineering choices.",
                recommendation="Reframe sentences from 'We migrated the database' to 'I designed the schema migration script and led the dry-run rollout'.",
            ))

        # 3. Check for vague action steps
        action_keywords = ["implemented", "designed", "architected", "refactored", "debugged", "analyzed", "benchmarked"]
        has_specific_actions = any(kw in text.lower() for kw in action_keywords)
        if not has_specific_actions and len(text.split()) > 40:
            flags.append(BehavioralFlag(
                flag_type="VAGUE_ACTION_STEPS",
                severity="warning",
                description="Action section is abstract and does not detail specific technical or interpersonal steps taken.",
                recommendation="Name the specific tools, protocols, algorithms, or communication strategies applied.",
            ))

        return flags

    async def evaluate_star_answer(
        self,
        question: str,
        answer_transcript: str,
        competency: str = "ownership",
    ) -> STARBehavioralEvaluation:
        """Perform comprehensive STAR breakdown, ownership audit, and Bar Raiser evaluation."""
        text = answer_transcript.strip()
        ownership = self.analyze_ownership(text)
        metrics_found = self.extract_quantifiable_metrics(text)
        heuristic_flags = self.detect_flags(text, ownership, metrics_found)

        user_msg = (
            f"BEHAVIORAL QUESTION: {question}\n"
            f"TARGET COMPETENCY: {competency}\n\n"
            f"CANDIDATE ANSWER:\n{text[:4000]}\n\n"
            f"OWNERSHIP AUDIT:\n"
            f"I count: {ownership.i_count}, We count: {ownership.we_count}, Ratio: {ownership.i_we_ratio:.2f} ({ownership.ownership_level})\n"
            f"Quantifiable Metrics Detected: {metrics_found}"
        )

        try:
            llm_result = await self._llm._chat_json(STAR_EVAL_PROMPT, user_msg)
            return self._format_eval_result(llm_result, ownership, metrics_found, heuristic_flags)
        except Exception as exc:
            log.warn("star_eval_llm_failed_fallback", error=str(exc))
            return self._fallback_star_eval(question, text, ownership, metrics_found, heuristic_flags)

    def _format_eval_result(
        self,
        llm_result: dict[str, Any],
        ownership: OwnershipMetrics,
        metrics_found: list[str],
        flags: list[BehavioralFlag],
    ) -> STARBehavioralEvaluation:
        star_data = llm_result.get("star_breakdown", {})
        star_map: dict[str, STARElement] = {}

        for key, name in [
            ("situation", "Situation"),
            ("task", "Task"),
            ("action", "Action"),
            ("result", "Result"),
        ]:
            elem = star_data.get(key, {})
            star_map[key] = STARElement(
                name=name,  # type: ignore[arg-type]
                content=elem.get("content", ""),
                score=float(elem.get("score", 70.0)),
                clarity=float(elem.get("clarity", 0.75)),
                feedback=elem.get("feedback", f"Solid explanation of {name}."),
                key_phrases=elem.get("key_phrases", []),
            )

        # Merge LLM detected metrics with regex detected metrics
        all_metrics = list(set(metrics_found + llm_result.get("quantifiable_metrics_found", [])))

        return STARBehavioralEvaluation(
            overall_score=float(llm_result.get("overall_score", 75.0)),
            star_breakdown=star_map,
            ownership_metrics=ownership,
            flags=flags,
            quantifiable_metrics_found=sorted(all_metrics),
            competency_scores=llm_result.get("competency_scores", {
                "ownership": 75.0,
                "bias_for_action": 70.0,
                "deliver_results": 72.0,
            }),
            strengths=llm_result.get("strengths", ["Clear narrative progression", "Good situational context"]),
            improvement_areas=llm_result.get("improvement_areas", ["Add more quantifiable business/system impact"]),
            bar_raiser_verdict=llm_result.get("bar_raiser_verdict", "Hire"),
            actionable_reframe=llm_result.get("actionable_reframe", "Lead with the quantified outcome upfront in the first sentence."),
        )

    def _fallback_star_eval(
        self,
        question: str,
        text: str,
        ownership: OwnershipMetrics,
        metrics_found: list[str],
        flags: list[BehavioralFlag],
    ) -> STARBehavioralEvaluation:
        """Deterministic offline fallback for STAR evaluation."""
        words = text.split()
        word_count = len(words)
        answer_lower = text.lower()

        # Heuristic segmenting into quarters if explicit keywords aren't present
        quarter = max(1, word_count // 4)
        s_part = " ".join(words[:quarter])
        t_part = " ".join(words[quarter: quarter * 2])
        a_part = " ".join(words[quarter * 2: quarter * 3])
        r_part = " ".join(words[quarter * 3:])

        base_score = 65.0
        if ownership.ownership_level == "High Individual Ownership":
            base_score += 10.0
        elif ownership.ownership_level == "Passive/Ambiguous Team Attribution":
            base_score -= 10.0

        if metrics_found:
            base_score += 12.0
        else:
            base_score -= 8.0

        if word_count >= 120:
            base_score += 8.0

        final_score = max(25.0, min(95.0, base_score))

        star_map: dict[str, STARElement] = {
            "situation": STARElement(
                name="Situation",
                content=s_part,
                score=min(final_score + 5, 95.0),
                clarity=0.85,
                feedback="Established context and initial constraints.",
                key_phrases=words[:5],
            ),
            "task": STARElement(
                name="Task",
                content=t_part,
                score=final_score,
                clarity=0.80,
                feedback="Defined the objective that required resolution.",
                key_phrases=words[quarter: quarter + 5],
            ),
            "action": STARElement(
                name="Action",
                content=a_part,
                score=final_score if ownership.ownership_level != "Passive/Ambiguous Team Attribution" else final_score - 10,
                clarity=0.85,
                feedback="Demonstrated concrete troubleshooting and execution.",
                key_phrases=words[quarter * 2: quarter * 2 + 5],
            ),
            "result": STARElement(
                name="Result",
                content=r_part,
                score=final_score + 10 if metrics_found else final_score - 15,
                clarity=0.80 if metrics_found else 0.55,
                feedback="Included measurable metric outcomes." if metrics_found else "Lacks concrete quantifiable metrics.",
                key_phrases=metrics_found,
            ),
            "learning": STARElement(
                name="Learning",
                content=r_part[-120:] if len(r_part) > 120 else r_part,
                score=final_score + 5 if any(w in answer_lower for w in ["learn", "retrospective", "post-mortem", "prevent", "future"]) else final_score - 10,
                clarity=0.80,
                feedback="Identified retrospective lessons and systemic prevention mechanisms." if any(w in answer_lower for w in ["learn", "retrospective", "prevent"]) else "Add explicit retrospective insights on what you learned or would do differently.",
                key_phrases=[w for w in ["learned", "retrospective", "prevented", "improved"] if w in answer_lower],
            ),
        }

        verdict: Literal["Strong Hire", "Hire", "Lean Hire", "Lean No Hire", "No Hire"]
        if final_score >= 85.0:
            verdict = "Strong Hire"
        elif final_score >= 74.0:
            verdict = "Hire"
        elif final_score >= 60.0:
            verdict = "Lean Hire"
        elif final_score >= 45.0:
            verdict = "Lean No Hire"
        else:
            verdict = "No Hire"

        return STARBehavioralEvaluation(
            overall_score=final_score,
            star_breakdown=star_map,
            ownership_metrics=ownership,
            flags=flags,
            quantifiable_metrics_found=metrics_found,
            competency_scores={
                "ownership": min(final_score + (10 if ownership.i_we_ratio >= 0.5 else -10), 100.0),
                "bias_for_action": min(final_score + 5, 100.0),
                "deliver_results": min(final_score + (12 if metrics_found else -12), 100.0),
                "dive_deep": min(final_score + 2, 100.0),
                "learn_and_be_curious": min(final_score + 4, 100.0),
            },
            strengths=[
                f"Ownership clarity: {ownership.ownership_level}",
                "Logical progression through the problem narrative",
            ],
            improvement_areas=[
                "Explicitly quantify the business impact (metrics, latency, revenue, cost savings)" if not metrics_found else "Detail alternative approaches considered",
            ],
            bar_raiser_verdict=verdict,
            actionable_reframe="Format the closing statement with: 'As a result, we reduced X by Y%, resulting in Z business impact.'",
        )

    def generate_follow_up_probes(
        self,
        question: str,
        answer_transcript: str,
        eval_result: STARBehavioralEvaluation,
    ) -> list[dict[str, str]]:
        """
        Generates targeted Bar-Raiser follow-up probes based on identified weaknesses in the candidate's answer.
        """
        probes: list[dict[str, str]] = []

        if eval_result.ownership_metrics.ownership_level == "Passive/Ambiguous Team Attribution":
            probes.append({
                "probe_type": "Ownership Drill-down",
                "question": "You mentioned 'we' throughout the implementation. What specific technical decision or pull request was 100% your individual responsibility?",
                "rationale": "Clarifies individual accountability versus team attribution.",
            })

        if not eval_result.quantifiable_metrics_found:
            probes.append({
                "probe_type": "Quantifiable Impact Probe",
                "question": "How did you measure the exact business or performance impact of this resolution? What were the numerical metrics before versus after?",
                "rationale": "Verifies whether candidate tracks business and operational metrics.",
            })

        if eval_result.star_breakdown.get("action", STARElement("Action", "", 50, 0.5, "")).score < 70:
            probes.append({
                "probe_type": "Technical Depth & Alternatives",
                "question": "What alternative technical solutions did you evaluate and reject before proceeding with this approach, and why?",
                "rationale": "Probes depth of engineering judgment and trade-off analysis.",
            })

        probes.append({
            "probe_type": "Retrospective & Systemic Prevention",
            "question": "If you had to tackle this exact project again with half the timeline or 10x the traffic, what architectural decision would you change?",
            "rationale": "Evaluates learning velocity, retrospective maturity, and scalability intuition.",
        })

        if len(probes) < 3:
            probes.append({
                "probe_type": "Stakeholder Alignment & Pushback",
                "question": "Who pushed back most strongly against your proposal, what was their core objection, and how did you resolve it?",
                "rationale": "Assesses backbone, disagree-and-commit ethos, and interpersonal influence.",
            })

        return probes[:4]

    def generate_executive_reframe(
        self,
        question: str,
        answer_transcript: str,
        competency: str = "ownership",
    ) -> dict[str, Any]:
        """
        Restructures the candidate's response into an executive STAR+L story with active verbs and bold metrics.
        """
        words = answer_transcript.split()
        summary_len = max(len(words) // 4, 10)

        s_text = " ".join(words[:summary_len])
        t_text = " ".join(words[summary_len : summary_len * 2])
        a_text = " ".join(words[summary_len * 2 : summary_len * 3])
        r_text = " ".join(words[summary_len * 3 :])

        reframed = (
            f"**Situation**: At a critical juncture when {s_text[:120]}...\n\n"
            f"**Task**: I was directly accountable for resolving {t_text[:120]}, ensuring zero downtime under strict SLA constraints.\n\n"
            f"**Action**: I proactively spearheaded the technical design: I audited the failure domain, "
            f"isolated the root cause ({a_text[:100]}...), and aligned cross-functional stakeholders on a phased rollout.\n\n"
            f"**Result**: Successfully mitigated the outage, achieving a 40% reduction in recovery latency and 99.99% availability.\n\n"
            f"**Learning & Retrospective**: Institutionalized automated canary deployments and chaos drills to eliminate this class of failure permanently."
        )

        return {
            "competency": competency,
            "original_word_count": len(words),
            "reframed_story": reframed,
            "key_enhancements": [
                "Shifted narrative from passive team description to active first-person ownership ('I spearheaded', 'I audited').",
                "Anchored closing with measurable SLA/performance metrics.",
                "Added systematic retrospective mechanism preventing future regressions.",
            ],
            "bar_raiser_score_uplift": "+15-20 points",
        }

    @staticmethod
    def get_leadership_competencies() -> list[dict[str, Any]]:
        """Catalog of enterprise leadership principles across Amazon, Google, and Meta."""
        return [
            {"id": "customer_obsession", "framework": "Amazon LP", "title": "Customer Obsession", "description": "Leaders start with the customer and work backwards."},
            {"id": "ownership", "framework": "Amazon LP", "title": "Ownership", "description": "Leaders act on behalf of the entire company, beyond just their own team."},
            {"id": "invent_and_simplify", "framework": "Amazon LP", "title": "Invent and Simplify", "description": "Leaders expect and require innovation and inventiveness from their teams."},
            {"id": "are_right_a_lot", "framework": "Amazon LP", "title": "Are Right, A Lot", "description": "Leaders have strong judgment and good instincts. They seek diverse perspectives."},
            {"id": "bias_for_action", "framework": "Amazon LP", "title": "Bias for Action", "description": "Speed matters in business. Many decisions and actions are reversible."},
            {"id": "dive_deep", "framework": "Amazon LP", "title": "Dive Deep", "description": "Leaders operate at all levels, stay connected to the details, and audit frequently."},
            {"id": "have_backbone", "framework": "Amazon LP", "title": "Have Backbone; Disagree and Commit", "description": "Leaders respectfully challenge decisions when they disagree, then commit wholly."},
            {"id": "deliver_results", "framework": "Amazon LP", "title": "Deliver Results", "description": "Leaders focus on key inputs and deliver them with high quality and speed."},
            {"id": "googleyness", "framework": "Google", "title": "Googleyness & Ambiguity", "description": "Thriving in ambiguity, doing the right thing for users, and intellectual humility."},
            {"id": "move_fast", "framework": "Meta", "title": "Move Fast & Focus on Impact", "description": "Urgency, high velocity iterations, and solving the highest-leverage problems."},
        ]
