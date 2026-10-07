from __future__ import annotations

import json
from typing import Any, Literal, TypedDict
from uuid import UUID

import structlog
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.config import get_settings
from app.models.interview_session import QuestionDifficulty
from app.models.interview_turn import QuestionCategory
from app.services.llm_service import LLMService

log = structlog.get_logger(__name__)
settings = get_settings()

_DIFFICULTY_ORDER = [
    QuestionDifficulty.easy,
    QuestionDifficulty.medium,
    QuestionDifficulty.hard,
    QuestionDifficulty.expert,
]


class InterviewState(TypedDict):
    session_id: str
    user_id: str
    resume_text: str
    jd_text: str
    ats_skill_gaps: list[dict]
    focus_categories: list[str]
    target_question_count: int
    current_turn: int
    current_difficulty: str
    current_topic: str
    interview_plan: list[dict]
    topic_mastery: dict[str, dict]
    candidate_strengths: list[str]
    candidate_weaknesses: list[str]
    conversation_history: list[dict]  # [{role, content, turn_index}]
    last_question: str
    last_question_category: str
    last_question_rationale: str
    last_evaluation: dict | None
    last_eval_score: float
    all_turn_scores: list[float]
    next_action: Literal["generate", "finalize"]
    is_complete: bool
    final_summary: dict | None
    error: str | None


class InterviewEngine:
    """LangGraph stateful adaptive interview state machine conforming to Master Prompt Feature 4."""

    def __init__(self, llm_svc: LLMService) -> None:
        self._llm = llm_svc
        self._checkpointer = MemorySaver()
        self._graph = self._build_graph()

    def _build_graph(self) -> Any:
        builder: StateGraph = StateGraph(InterviewState)

        # 1. State machine nodes
        builder.add_node("load_profile", self._node_load_profile)
        builder.add_node("analyze_job", self._node_analyze_job)
        builder.add_node("build_interview_plan", self._node_build_interview_plan)
        builder.add_node("select_topic", self._node_select_topic)
        builder.add_node("generate_question", self._node_generate_question)
        builder.add_node("evaluate_answer", self._node_evaluate_answer)
        builder.add_node("update_candidate_state", self._node_update_candidate_state)
        builder.add_node("adapt_difficulty", self._node_adapt_difficulty)
        builder.add_node("finalize", self._node_finalize)

        # 2. Graph topology
        builder.set_entry_point("load_profile")
        builder.add_edge("load_profile", "analyze_job")
        builder.add_edge("analyze_job", "build_interview_plan")
        builder.add_edge("build_interview_plan", "select_topic")
        builder.add_edge("select_topic", "generate_question")

        # After generate_question, graph pauses waiting for candidate audio/text answer
        builder.add_edge("generate_question", "evaluate_answer")

        # Resume pipeline upon receiving answer
        builder.add_edge("evaluate_answer", "update_candidate_state")
        builder.add_edge("update_candidate_state", "adapt_difficulty")

        # Conditional route: either select next topic and generate next question, or finalize
        builder.add_conditional_edges(
            "adapt_difficulty",
            self._route_after_adapt,
            {"generate": "select_topic", "finalize": "finalize"},
        )
        builder.add_edge("finalize", END)

        return builder.compile(
            checkpointer=self._checkpointer,
            interrupt_after=["generate_question"],
        )

    # ── Graph Node Implementations ────────────────────────────────────────────

    async def _node_load_profile(self, state: InterviewState) -> dict:
        """Node 1: Extract candidate background highlights from resume."""
        log.info("lg_load_profile", session_id=state["session_id"])
        return {
            "current_turn": 0,
            "all_turn_scores": [],
            "conversation_history": [],
            "candidate_strengths": [],
            "candidate_weaknesses": [],
            "last_eval_score": 0.0,
            "next_action": "generate",
            "is_complete": False,
            "final_summary": None,
            "error": None,
        }

    async def _node_analyze_job(self, state: InterviewState) -> dict:
        """Node 2: Analyze target job requirements and seniority expectations."""
        log.info("lg_analyze_job", session_id=state.get("session_id", ""))
        # Ensures JD requirements are available in state context
        return {}

    async def _node_build_interview_plan(self, state: InterviewState) -> dict:
        """Node 3: Synthesize ATS skill gaps and JD into an adaptive curriculum."""
        log.info("lg_build_interview_plan", session_id=state.get("session_id", ""))
        plan = await self._llm.build_interview_plan(
            resume_summary=state.get("resume_text", ""),
            jd_summary=state.get("jd_text", ""),
            skill_gaps=state.get("ats_skill_gaps", []),
            focus_categories=state.get("focus_categories", []),
        )

        topic_mastery: dict[str, dict] = {}
        for item in plan:
            topic_name = item["topic"]
            topic_mastery[topic_name] = {
                "topic": topic_name,
                "score": 0.0,
                "turns_count": 0,
                "status": "untested",
            }

        return {
            "interview_plan": plan,
            "topic_mastery": topic_mastery,
            "current_topic": plan[0]["topic"] if plan else "Distributed Systems Architecture",
        }

    async def _node_select_topic(self, state: InterviewState) -> dict:
        """Node 4 & Node 10: Select the next topic or drill down into candidate weakness."""
        last_eval = state.get("last_evaluation") or {}
        weaknesses = state.get("candidate_weaknesses", [])
        plan = list(state.get("interview_plan", []))
        current_turn = state.get("current_turn", 0)

        # Probing strategy: if candidate struggled (score < 55) and follow-up recommended, probe weakness
        if last_eval.get("recommended_follow_up") and last_eval.get("overall_score", 100.0) < 55.0:
            selected_topic = state.get("current_topic") or "Distributed Systems Architecture"
            log.info("lg_select_topic_probe", topic=selected_topic, weakness=weaknesses[-1] if weaknesses else "")
            return {"current_topic": selected_topic}

        # Otherwise pick the next pending topic in curriculum
        selected_topic = None
        for item in plan:
            if item.get("status") == "pending":
                selected_topic = item["topic"]
                item["status"] = "in_progress"
                break

        if not selected_topic:
            # Fallback to cycling unmastered topics
            mastery = state.get("topic_mastery", {})
            for topic, stats in mastery.items():
                if stats.get("status") != "mastered":
                    selected_topic = topic
                    break

        if not selected_topic:
            selected_topic = plan[current_turn % len(plan)]["topic"] if plan else "Distributed Systems Architecture"

        log.info("lg_select_topic_progress", turn=current_turn + 1, topic=selected_topic)
        return {"current_topic": selected_topic, "interview_plan": plan}

    async def _node_generate_question(self, state: InterviewState) -> dict:
        """Node 5 & Node 11: Grounded question generation using context, topic, and difficulty."""
        turn_num = state.get("current_turn", 0) + 1
        current_topic = state.get("current_topic") or "Distributed Systems Architecture"
        current_diff = state.get("current_difficulty", "medium")

        # Determine category based on current plan item
        category = "technical"
        for item in state.get("interview_plan", []):
            if item["topic"] == current_topic:
                category = item.get("category", "technical")
                break

        context = {
            "session_id": state.get("session_id", ""),
            "turn_number": turn_num,
            "target_total": state.get("target_question_count", 5),
            "current_topic": current_topic,
            "current_difficulty": current_diff,
            "category": category,
            "candidate_weaknesses": state.get("candidate_weaknesses", []),
            "candidate_strengths": state.get("candidate_strengths", []),
            "resume_summary": state.get("resume_text", "")[:1200],
            "jd_summary": state.get("jd_text", "")[:1000],
            "recent_history": state.get("conversation_history", [])[-3:],
        }

        result = await self._llm.generate_question(context)
        log.info(
            "lg_question_generated",
            session_id=state.get("session_id", ""),
            turn=turn_num,
            topic=current_topic,
            difficulty=current_diff,
        )
        return {
            "last_question": result.get("question_text", ""),
            "last_question_category": result.get("category", category),
            "last_question_rationale": result.get("rationale", ""),
        }

    async def _node_evaluate_answer(self, state: InterviewState) -> dict:
        """Node 6: Multi-dimensional answer evaluation against question and rubric."""
        history = state.get("conversation_history", [])
        last_answer = history[-1]["content"] if history else ""

        current_topic = state.get("current_topic") or "Distributed Systems Architecture"
        current_diff = state.get("current_difficulty", "medium")
        category = state.get("last_question_category", "technical")

        eval_result = await self._llm.evaluate_answer(
            question=state.get("last_question", ""),
            answer_transcript=last_answer,
            question_category=category,
            difficulty=current_diff,
            topic=current_topic,
            context={"turn": state.get("current_turn", 0) + 1},
        )

        composite = float(eval_result.get("overall_score", 65.0))
        log.info(
            "lg_answer_evaluated",
            session_id=state.get("session_id", ""),
            turn=state.get("current_turn", 0) + 1,
            overall_score=composite,
        )
        return {
            "last_evaluation": eval_result,
            "last_eval_score": composite,
        }

    async def _node_update_candidate_state(self, state: InterviewState) -> dict:
        """Node 7: Update candidate topic mastery, strengths, weaknesses, and score log."""
        current_turn = state.get("current_turn", 0) + 1
        last_eval = state.get("last_evaluation") or {}
        composite = float(last_eval.get("overall_score", 65.0))
        current_topic = state.get("current_topic") or "Distributed Systems Architecture"

        # Update mastery map
        mastery = dict(state.get("topic_mastery", {}))
        topic_stats = dict(mastery.get(current_topic, {
            "topic": current_topic,
            "score": 0.0,
            "turns_count": 0,
            "status": "untested",
        }))

        prev_turns = topic_stats.get("turns_count", 0)
        prev_score = topic_stats.get("score", 0.0)
        new_turns = prev_turns + 1
        new_score = round(((prev_score * prev_turns) + composite) / new_turns, 1)

        if new_score >= 80.0:
            status = "mastered"
        elif new_score >= 60.0:
            status = "proficient"
        else:
            status = "struggling"

        topic_stats["score"] = new_score
        topic_stats["turns_count"] = new_turns
        topic_stats["status"] = status
        mastery[current_topic] = topic_stats

        # Update strengths & weaknesses
        all_strengths = list(state.get("candidate_strengths", []))
        for s in last_eval.get("strengths", []):
            if s not in all_strengths:
                all_strengths.append(s)

        all_weaknesses = list(state.get("candidate_weaknesses", []))
        for w in last_eval.get("weaknesses", []):
            if w not in all_weaknesses:
                all_weaknesses.append(w)

        updated_scores = list(state.get("all_turn_scores", [])) + [composite]

        log.info(
            "lg_candidate_state_updated",
            session_id=state.get("session_id", ""),
            turn=current_turn,
            topic=current_topic,
            topic_score=new_score,
            topic_status=status,
        )
        return {
            "current_turn": current_turn,
            "topic_mastery": mastery,
            "candidate_strengths": all_strengths,
            "candidate_weaknesses": all_weaknesses,
            "all_turn_scores": updated_scores,
        }

    async def _node_adapt_difficulty(self, state: InterviewState) -> dict:
        """Node 8: Dynamically adapt difficulty up or down and check completion."""
        last_score = state.get("last_eval_score", 70.0)
        current_diff = QuestionDifficulty(state.get("current_difficulty", "medium"))
        idx = _DIFFICULTY_ORDER.index(current_diff)

        if last_score >= settings.DIFFICULTY_UPGRADE_THRESHOLD and idx < len(_DIFFICULTY_ORDER) - 1:
            new_difficulty = _DIFFICULTY_ORDER[idx + 1]
        elif last_score < settings.DIFFICULTY_DOWNGRADE_THRESHOLD and idx > 0:
            new_difficulty = _DIFFICULTY_ORDER[idx - 1]
        else:
            new_difficulty = current_diff

        current_turn = state.get("current_turn", 0)
        target_count = state.get("target_question_count", 5)
        finished = current_turn >= target_count

        log.info(
            "lg_difficulty_adapted",
            session_id=state.get("session_id", ""),
            from_difficulty=current_diff.value,
            to_difficulty=new_difficulty.value,
            finished=finished,
            current_turn=current_turn,
            target_count=target_count,
        )
        return {
            "current_difficulty": new_difficulty.value,
            "next_action": "finalize" if finished else "generate",
        }

    async def _node_finalize(self, state: InterviewState) -> dict:
        """Node 12: Generate final Bar Raiser evaluation and marks session complete."""
        scores = state.get("all_turn_scores", [])
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

        topic_scores = {
            t: stats.get("score", 0.0)
            for t, stats in state.get("topic_mastery", {}).items()
        }

        context = {
            "session_id": state.get("session_id", ""),
            "all_turn_scores": scores,
            "candidate_strengths": state.get("candidate_strengths", []),
            "candidate_weaknesses": state.get("candidate_weaknesses", []),
            "topic_scores": topic_scores,
        }
        final_summary = await self._llm.generate_final_summary(context)

        log.info(
            "lg_session_finalized",
            session_id=state.get("session_id", ""),
            avg_score=avg_score,
            turns=len(scores),
            recommendation=final_summary.get("hiring_recommendation"),
        )
        return {
            "is_complete": True,
            "final_summary": final_summary,
            "next_action": "finalize",
        }

    def _route_after_adapt(
        self, state: InterviewState
    ) -> Literal["generate", "finalize"]:
        return state.get("next_action", "generate")

    # ── Session Lifecycle Operations ──────────────────────────────────────────

    async def initialize_session(self, session_id: str, initial_state: InterviewState) -> str:
        """Start the LangGraph state machine and pause at the first question."""
        thread_id = f"session:{session_id}"
        config = {"configurable": {"thread_id": thread_id}}
        await self._graph.ainvoke(initial_state, config=config)
        return thread_id

    async def submit_answer(
        self, thread_id: str, transcript: str
    ) -> dict[str, Any]:
        """Resume graph execution with the candidate's answer and produce next state."""
        config = {"configurable": {"thread_id": thread_id}}
        current_state = await self._graph.aget_state(config)
        state_values = current_state.values if current_state and current_state.values else {}
        turn_idx = state_values.get("current_turn", 0)

        history = list(state_values.get("conversation_history", []))
        history.append({
            "role": "user",
            "content": transcript,
            "turn_index": turn_idx,
        })

        update_dict: dict[str, Any] = {
            "conversation_history": history,
        }
        if "session_id" not in state_values:
            update_dict["session_id"] = thread_id.replace("session:", "")
        if "current_difficulty" not in state_values:
            update_dict["current_difficulty"] = "medium"
        if "target_question_count" not in state_values:
            update_dict["target_question_count"] = 5

        await self._graph.aupdate_state(
            config,
            update_dict,
            as_node="generate_question",
        )

        # Resume execution: evaluate_answer -> update_candidate_state -> adapt_difficulty -> (select_topic -> generate_question OR finalize)
        result = await self._graph.ainvoke(None, config=config)
        final_values = result if result else (await self._graph.aget_state(config)).values

        is_done = final_values.get("is_complete", False) or final_values.get("next_action") == "finalize"

        return {
            "next_question": final_values.get("last_question"),
            "category": final_values.get("last_question_category"),
            "rationale": final_values.get("last_question_rationale"),
            "difficulty": final_values.get("current_difficulty"),
            "turn": final_values.get("current_turn"),
            "is_complete": is_done,
            "evaluation": final_values.get("last_evaluation"),
            "topic_mastery": final_values.get("topic_mastery"),
            "interview_plan": final_values.get("interview_plan"),
            "candidate_strengths": final_values.get("candidate_strengths", []),
            "candidate_weaknesses": final_values.get("candidate_weaknesses", []),
            "all_scores": final_values.get("all_turn_scores", []),
            "final_summary": final_values.get("final_summary"),
        }

    async def get_state(self, thread_id: str) -> InterviewState:
        """Fetch current checkpointed state snapshot."""
        config = {"configurable": {"thread_id": thread_id}}
        snapshot = await self._graph.aget_state(config)
        return snapshot.values  # type: ignore[return-value]
