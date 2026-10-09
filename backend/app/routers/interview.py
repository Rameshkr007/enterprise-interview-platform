from __future__ import annotations

import base64
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    SessionNotActiveException,
    SessionNotFoundException,
)
from app.database import get_db
from app.models.ats_analysis import AtsAnalysis
from app.models.interview_session import InterviewSession, QuestionDifficulty, SessionStatus
from app.models.interview_turn import InterviewTurn, QuestionCategory
from app.models.job_description import JobDescription
from app.models.resume import Resume
from app.schemas.interview import (
    AnswerEvaluationResult,
    AnswerSubmitRequest,
    FinalEvaluationSummary,
    InterviewPlanItem,
    NextQuestionResponse,
    SessionCreateRequest,
    SessionResponse,
    SessionStateResponse,
    TopicMasteryItem,
    TurnResponse,
)
from app.services.audio_pipeline import AudioAnalysisPipeline
from app.services.audit_service import AuditService
from app.config import get_settings
from app.services.embedding_service import EmbeddingService
from app.services.langgraph_engine import InterviewEngine, InterviewState
from app.services.llm_service import LLMService
from app.services.storage_service import StorageService
from app.services.whisper_client import WhisperClient

settings = get_settings()
log = structlog.get_logger(__name__)
router = APIRouter(prefix="/interview", tags=["Interview"])

_engine: InterviewEngine | None = None


def _get_engine() -> InterviewEngine:
    global _engine
    if _engine is None:
        _engine = InterviewEngine(LLMService())
    return _engine


@router.post("/session", response_model=SessionResponse, status_code=201)
async def create_session(
    body: SessionCreateRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InterviewSession:
    """Create and initialize a stateful adaptive interview session with LangGraph."""
    session = InterviewSession(
        user_id=current_user.id,
        org_id=current_user.org_id,
        resume_id=body.resume_id,
        jd_id=body.jd_id,
        ats_analysis_id=body.ats_analysis_id,
        target_question_count=body.target_question_count,
        current_difficulty=body.starting_difficulty,
        session_config={
            "adaptive_mode": body.adaptive_mode,
            "focus_categories": body.focus_categories,
        },
        status=SessionStatus.active,
        started_at=datetime.now(UTC),
    )
    db.add(session)
    await db.flush()

    # Load context data for graph initialization
    resume_text = ""
    jd_text = ""
    skill_gaps: list[dict] = []

    if body.resume_id:
        resume = await db.get(Resume, body.resume_id)
        if resume:
            resume_text = resume.parsed_text

    if body.jd_id:
        jd = await db.get(JobDescription, body.jd_id)
        if jd:
            jd_text = jd.raw_text

    if body.ats_analysis_id:
        ats = await db.get(AtsAnalysis, body.ats_analysis_id)
        if ats:
            skill_gaps = ats.skill_gaps or []

    initial_state = InterviewState(
        session_id=str(session.id),
        user_id=str(current_user.id),
        resume_text=resume_text,
        jd_text=jd_text,
        ats_skill_gaps=skill_gaps,
        focus_categories=body.focus_categories,
        target_question_count=body.target_question_count,
        current_turn=0,
        current_difficulty=body.starting_difficulty.value,
        current_topic="Distributed Systems Architecture",
        interview_plan=[],
        topic_mastery={},
        candidate_strengths=[],
        candidate_weaknesses=[],
        conversation_history=[],
        last_question="",
        last_question_category="technical",
        last_question_rationale="",
        last_evaluation=None,
        last_eval_score=0.0,
        all_turn_scores=[],
        next_action="generate",
        is_complete=False,
        final_summary=None,
        error=None,
    )

    engine = _get_engine()
    thread_id = await engine.initialize_session(str(session.id), initial_state)

    # Fetch initial graph state snapshot after load_profile -> analyze_job -> build_plan -> select_topic -> generate_question
    state = await engine.get_state(thread_id)

    session.langgraph_thread_id = thread_id
    session.current_topic = state.get("current_topic")
    session.session_config["interview_plan"] = state.get("interview_plan", [])
    session.session_config["topic_mastery"] = state.get("topic_mastery", {})
    session.session_config["last_question"] = state.get("last_question", "")
    session.session_config["last_question_category"] = state.get("last_question_category", "technical")
    session.session_config["last_question_rationale"] = state.get("last_question_rationale", "")

    db.add(session)
    await db.flush()
    await db.refresh(session)

    # Enterprise audit logging
    audit = AuditService(db)
    await audit.log_event(
        user_id=current_user.id,
        action="interview.session_created",
        entity_type="interview_session",
        entity_id=str(session.id),
        org_id=current_user.org_id,
        payload={
            "target_questions": body.target_question_count,
            "starting_difficulty": body.starting_difficulty.value,
            "topic": session.current_topic,
        },
    )

    log.info(
        "interview_session_created",
        session_id=str(session.id),
        user_id=str(current_user.id),
        thread_id=thread_id,
        initial_topic=session.current_topic,
    )
    return session


@router.get("/sessions", response_model=list[SessionResponse])
async def list_user_sessions(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 20,
) -> list[InterviewSession]:
    """List recent interview sessions for current user."""
    stmt = (
        select(InterviewSession)
        .where(InterviewSession.user_id == current_user.id)
        .order_by(InterviewSession.created_at.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InterviewSession:
    """Retrieve session details and metadata."""
    session = await db.get(InterviewSession, session_id)
    if session is None:
        raise SessionNotFoundException()
    if session.user_id != current_user.id and current_user.role.value not in ("admin", "recruiter"):
        raise ForbiddenException("Access denied to interview session")
    return session



@router.get("/session/{session_id}/state", response_model=SessionStateResponse)
async def get_session_state(
    session_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionStateResponse:
    """Fetch current live LangGraph state machine snapshot (plan, topic mastery, strengths, weaknesses)."""
    session = await db.get(InterviewSession, session_id)
    if session is None:
        raise SessionNotFoundException()
    if session.user_id != current_user.id and current_user.role.value not in ("admin", "recruiter"):
        raise ForbiddenException("Access denied to interview session state")

    engine = _get_engine()
    thread_id = session.langgraph_thread_id or f"session:{session.id}"
    state = await engine.get_state(thread_id)

    plan_items = [
        InterviewPlanItem(**item) for item in state.get("interview_plan", [])
    ]
    mastery_items = {
        k: TopicMasteryItem(**v) for k, v in state.get("topic_mastery", {}).items()
    }
    last_eval = None
    if state.get("last_evaluation"):
        last_eval = AnswerEvaluationResult(**state["last_evaluation"])

    final_sum = None
    if state.get("final_summary"):
        final_sum = FinalEvaluationSummary(**state["final_summary"])

    return SessionStateResponse(
        session_id=str(session.id),
        status=session.status.value,
        current_turn=state.get("current_turn", session.current_question_index),
        target_question_count=state.get("target_question_count", session.target_question_count),
        current_difficulty=state.get("current_difficulty", session.current_difficulty.value),
        current_topic=state.get("current_topic", session.current_topic),
        interview_plan=plan_items,
        topic_mastery=mastery_items,
        candidate_strengths=state.get("candidate_strengths", []),
        candidate_weaknesses=state.get("candidate_weaknesses", []),
        last_question=state.get("last_question"),
        last_evaluation=last_eval,
        all_turn_scores=state.get("all_turn_scores", []),
        is_complete=state.get("is_complete", session.status == SessionStatus.completed),
        final_summary=final_sum,
    )


@router.get("/session/{session_id}/turns", response_model=list[TurnResponse])
async def get_session_turns(
    session_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[InterviewTurn]:
    """Retrieve full history of interview turns including evaluations and audio metrics."""
    session = await db.get(InterviewSession, session_id)
    if session is None:
        raise SessionNotFoundException()
    if session.user_id != current_user.id and current_user.role.value not in ("admin", "recruiter"):
        raise ForbiddenException("Access denied to interview turns")

    res = await db.execute(
        select(InterviewTurn)
        .where(InterviewTurn.session_id == session_id)
        .order_by(InterviewTurn.turn_index.asc())
    )
    return list(res.scalars().all())


@router.post("/answer", response_model=NextQuestionResponse)
async def submit_answer(
    body: AnswerSubmitRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NextQuestionResponse:
    """Submit candidate answer (audio or text transcript) and advance LangGraph state machine."""
    session = await db.get(InterviewSession, body.session_id)
    if session is None or session.user_id != current_user.id:
        raise SessionNotFoundException()
    if session.status != SessionStatus.active:
        raise SessionNotActiveException()

    if not body.audio_bytes_b64 and not body.answer_text:
        raise BadRequestException("Either audio_bytes_b64 or answer_text must be provided")

    transcript = ""
    audio_metrics_dict: dict | None = None
    s3_key: str | None = None

    if body.audio_bytes_b64:
        try:
            audio_bytes = base64.b64decode(body.audio_bytes_b64)
        except Exception as exc:
            raise BadRequestException(f"Invalid base64 audio payload: {exc}")

        whisper = WhisperClient()
        transcript = await whisper.transcribe(audio_bytes, language=body.language)

        pipeline = AudioAnalysisPipeline()
        metrics = pipeline.analyze_audio_bytes(audio_bytes)
        metrics = pipeline.enrich_with_transcript(metrics, transcript)
        audio_metrics_dict = metrics.to_dict()

        storage = StorageService()
        s3_key = await storage.upload_audio(str(session.id), body.turn_index, audio_bytes)
    else:
        transcript = (body.answer_text or "").strip()
        word_count = len(transcript.split())
        audio_metrics_dict = {
            "duration_s": round(word_count / 2.5, 2),
            "silence_intervals": [],
            "silence_count": 0,
            "silence_ratio": 0.05,
            "pitch_mean_hz": 120.0,
            "pitch_std_hz": 15.0,
            "pitch_variance_score": 0.5,
            "speech_rate_wpm": 130.0,
            "energy_mean": 0.02,
            "energy_std": 0.005,
            "filler_words": [],
            "filler_word_rate": 0.0,
        }

    # Execute LangGraph answer evaluation and state progression
    engine = _get_engine()
    thread_id = session.langgraph_thread_id or f"session:{session.id}"
    result = await engine.submit_answer(
        thread_id=thread_id,
        transcript=transcript,
    )

    # Embed candidate answer for semantic search & RAG
    embedding_svc = EmbeddingService()
    answer_embedding = await embedding_svc.embed_text(transcript)

    # Persist interview turn
    question_asked = session.session_config.get("last_question") or "Interview Question"
    rationale_asked = session.session_config.get("last_question_rationale")
    category_asked = session.session_config.get("last_question_category", "technical")

    try:
        cat_enum = QuestionCategory(category_asked)
    except Exception:
        cat_enum = QuestionCategory.technical

    eval_data = result.get("evaluation") or {}
    eval_feedback = eval_data.get("recommended_follow_up") or (
        " ".join(eval_data.get("strengths", [])) if eval_data.get("strengths") else None
    )

    turn = InterviewTurn(
        session_id=session.id,
        turn_index=body.turn_index,
        question_text=question_asked,
        question_category=cat_enum,
        question_difficulty=session.current_difficulty.value,
        question_rationale=rationale_asked,
        raw_transcript=transcript,
        corrected_transcript=transcript,
        audio_metrics=audio_metrics_dict,
        eval_scores=eval_data,
        eval_feedback=eval_feedback,
        eval_model=settings.OPENAI_CHAT_MODEL,
        answer_embedding=answer_embedding,
        s3_audio_key=s3_key,
    )
    db.add(turn)

    # Update session state
    new_turn_idx = result.get("turn", body.turn_index + 1)
    new_diff_str = result.get("difficulty", session.current_difficulty.value)
    try:
        session.current_difficulty = QuestionDifficulty(new_diff_str)
    except Exception:
        pass

    session.current_question_index = new_turn_idx
    session.session_config["last_question"] = result.get("next_question", "")
    session.session_config["last_question_category"] = result.get("category", "technical")
    session.session_config["last_question_rationale"] = result.get("rationale", "")
    session.session_config["topic_mastery"] = result.get("topic_mastery", {})
    session.session_config["interview_plan"] = result.get("interview_plan", [])

    is_complete = bool(result.get("is_complete"))
    if is_complete:
        session.status = SessionStatus.completed
        session.completed_at = datetime.now(UTC)
        scores = result.get("all_scores", [])
        if scores:
            session.aggregate_score = round(sum(scores) / len(scores), 1)

    db.add(session)
    await db.flush()

    # Log audit event
    audit = AuditService(db)
    await audit.log_event(
        user_id=current_user.id,
        action="interview.turn_completed",
        entity_type="interview_turn",
        entity_id=str(turn.id),
        org_id=current_user.org_id,
        payload={
            "session_id": str(session.id),
            "turn_index": body.turn_index,
            "overall_score": eval_data.get("overall_score"),
            "next_difficulty": session.current_difficulty.value,
            "is_complete": is_complete,
        },
    )

    eval_model_obj = AnswerEvaluationResult(**eval_data) if eval_data else None
    topic_mastery_dict = None
    if result.get("topic_mastery"):
        topic_mastery_dict = {
            k: TopicMasteryItem(**v) for k, v in result["topic_mastery"].items()
        }

    final_sum_obj = None
    if result.get("final_summary"):
        final_sum_obj = FinalEvaluationSummary(**result["final_summary"])

    return NextQuestionResponse(
        question_text=result.get("next_question") or "",
        category=result.get("category") or "technical",
        difficulty=session.current_difficulty.value,
        rationale=result.get("rationale") or "",
        turn_index=new_turn_idx,
        is_complete=is_complete,
        evaluation=eval_model_obj,
        topic_mastery=topic_mastery_dict,
        final_summary=final_sum_obj,
    )


@router.post("/session/{session_id}/finalize", response_model=SessionResponse)
async def finalize_session(
    session_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InterviewSession:
    """Manually finalize session, calculate aggregate score, and complete LangGraph execution."""
    session = await db.get(InterviewSession, session_id)
    if session is None or session.user_id != current_user.id:
        raise SessionNotFoundException()

    turns_res = await db.execute(
        select(InterviewTurn).where(InterviewTurn.session_id == session_id)
    )
    turns = list(turns_res.scalars().all())
    scores = [
        t.eval_scores.get("overall_score", 0.0)
        for t in turns
        if t.eval_scores and "overall_score" in t.eval_scores
    ]

    session.status = SessionStatus.completed
    session.completed_at = datetime.now(UTC)
    session.aggregate_score = round(sum(scores) / len(scores), 1) if scores else 0.0

    db.add(session)
    await db.flush()
    await db.refresh(session)

    audit = AuditService(db)
    await audit.log_event(
        user_id=current_user.id,
        action="interview.session_finalized",
        entity_type="interview_session",
        entity_id=str(session.id),
        org_id=current_user.org_id,
        payload={"aggregate_score": session.aggregate_score, "turns_count": len(turns)},
    )
    return session
