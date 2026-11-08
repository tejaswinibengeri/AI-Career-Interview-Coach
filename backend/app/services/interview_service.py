"""
AI Mock Interview Engine Service.
Manages session setup, 6-metric rubric evaluation via Ollama, multi-turn question progression,
browser refresh state persistence, and final performance reporting.
"""

import json
import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.integrations.ai import get_ai_provider
from app.integrations.ai.base import AIProvider
from app.models.interview import (
    InterviewAnswer,
    InterviewEvaluation,
    InterviewQuestion,
    InterviewSession,
)
from app.models.question import Question
from app.models.user import User
from app.schemas.interview import (
    AIAnswerEvaluationPayload,
    CreateInterviewSessionRequest,
    InterviewEvaluationResponse,
    InterviewQuestionResponse,
    InterviewResultsResponse,
    InterviewSessionResponse,
)
from app.services.question_service import seed_standard_questions_if_empty

logger = logging.getLogger(__name__)

EVALUATE_ANSWER_PROMPT_TEMPLATE = """You are an expert Executive Interviewer and Principal Assessor evaluating a candidate for {role}.
Evaluate the candidate's answer for the following mock interview question with high rigor and accuracy:

TARGET ROLE: {role}
DIFFICULTY: {difficulty}
QUESTION: {question_text}
REFERENCE ANSWER GUIDE: {question_explanation}

CANDIDATE'S ACTUAL SUBMITTED RESPONSE:
---
{user_answer}
---

EVALUATION RUBRIC & SCORING RULES:
Evaluate the candidate's response across 6 transparent dimensions (scores must be between 0.0 and 100.0):
1. Technical Correctness: Accuracy of domain concepts, technical logic, and facts.
   - 90-100: Flawless accuracy, accurate technical vocabulary, identifies trade-offs/edge cases.
   - 75-89: Solid and correct with minor gaps or omission of minor details.
   - 50-74: Partially correct, some conceptual confusion or missing core mechanisms.
   - <50: Factually incorrect or irrelevant.
2. Relevance: Direct alignment with the specific question asked.
3. Completeness: Coverage of key expected components and depth.
4. Communication: Professionalism, tone, and vocabulary.
5. Structure: Logical flow (e.g. STAR method or structured breakdown).
6. Clarity: Ease of understanding, conciseness, and precision.

CRITICAL:
- Be strictly objective and fair. Score grounded entirely on the candidate's submitted text.
- Calculate overall_score as the balanced average of the 6 dimensions.
- Provide actionable feedback, at least 2 specific strengths, at least 1-2 concrete improvements, and a complete sample ideal answer.

OUTPUT MUST BE VALID JSON ONLY matching this exact structure:
{{
  "technical_correctness": 88.0,
  "relevance": 90.0,
  "completeness": 85.0,
  "communication": 85.0,
  "structure": 85.0,
  "clarity": 90.0,
  "overall_score": 87.2,
  "feedback": "Constructive evaluation of the candidate's answer...",
  "strengths": ["Clear explanation of...", "Solid technical vocabulary"],
  "improvements": ["Elaborate further on...", "Provide a concrete project example"],
  "ideal_answer": "Comprehensive model answer covering key concepts and trade-offs..."
}}
"""


async def format_question_schema(q: InterviewQuestion) -> InterviewQuestionResponse:
    """Format InterviewQuestion ORM into response schema."""
    user_ans = q.answer.user_answer if q.answer else None
    eval_resp = None
    if q.answer and q.answer.evaluation:
        ev = q.answer.evaluation
        eval_resp = InterviewEvaluationResponse(
            id=ev.id,
            answer_id=ev.answer_id,
            technical_correctness=ev.technical_correctness,
            relevance=ev.relevance,
            completeness=ev.completeness,
            communication=ev.communication,
            structure=ev.structure,
            clarity=ev.clarity,
            overall_score=ev.overall_score,
            feedback=ev.feedback,
            strengths=ev.strengths or [],
            improvements=ev.improvements or [],
            ideal_answer=ev.ideal_answer,
            evaluated_at=ev.evaluated_at,
        )

    return InterviewQuestionResponse(
        id=q.id,
        question_text=q.question_text,
        category=q.category,
        difficulty=q.difficulty,
        question_order=q.question_order,
        explanation=q.explanation,
        user_answer=user_ans,
        evaluation=eval_resp,
    )


async def format_session_schema(session: InterviewSession) -> InterviewSessionResponse:
    """Format InterviewSession ORM into response schema with current active question."""
    q_schemas = [await format_question_schema(q) for q in session.questions]

    current_q = None
    if 0 <= session.current_question_index < len(q_schemas):
        current_q = q_schemas[session.current_question_index]

    return InterviewSessionResponse(
        id=session.id,
        user_id=session.user_id,
        role=session.role,
        difficulty=session.difficulty,
        status=session.status,
        total_questions=session.total_questions,
        current_question_index=session.current_question_index,
        overall_score=session.overall_score,
        summary_feedback=session.summary_feedback,
        current_question=current_q,
        questions=q_schemas,
        created_at=session.created_at,
        completed_at=session.completed_at,
    )


async def create_interview_session(
    db: AsyncSession,
    user: User,
    request: CreateInterviewSessionRequest,
    ai_provider: AIProvider | None = None,
) -> InterviewSessionResponse:
    """Create new mock interview session and select/generate role-aligned questions."""
    await seed_standard_questions_if_empty(db)

    # 1. Query Question Bank for role & difficulty matches
    q_query = (
        select(Question)
        .where(
            Question.role.ilike(f"%{request.role}%"),
            Question.difficulty.ilike(f"%{request.difficulty}%"),
        )
        .order_by(Question.id.asc())
        .limit(request.total_questions)
    )
    res = await db.execute(q_query)
    q_bank_items = list(res.scalars().all())

    # 2. If not enough role-specific questions, query by difficulty alone
    if len(q_bank_items) < request.total_questions:
        additional_needed = request.total_questions - len(q_bank_items)
        existing_ids = [q.id for q in q_bank_items]
        diff_query = (
            select(Question)
            .where(
                Question.difficulty.ilike(f"%{request.difficulty}%"),
                Question.id.not_in(existing_ids) if existing_ids else True,
            )
            .limit(additional_needed)
        )
        diff_res = await db.execute(diff_query)
        q_bank_items.extend(diff_res.scalars().all())

    # 3. If still not enough questions, generate via Ollama if available
    if len(q_bank_items) < request.total_questions:
        try:
            from app.schemas.question import GenerateQuestionsRequest
            from app.services.question_service import generate_ai_questions

            gen_req = GenerateQuestionsRequest(
                role=request.role,
                difficulty=request.difficulty,
                category="Technical",
                count=request.total_questions - len(q_bank_items),
            )
            generated_qs = await generate_ai_questions(db, user=user, request=gen_req, ai_provider=ai_provider)
            gen_ids = [g.id for g in generated_qs]

            # Fetch fresh ORM objects for generated questions
            gen_orms_res = await db.execute(select(Question).where(Question.id.in_(gen_ids)))
            q_bank_items.extend(gen_orms_res.scalars().all())
        except Exception as exc:
            logger.warning("Could not generate additional interview questions via Ollama: %s", exc)

    # 4. Fallback to any available questions if bank is completely empty
    if not q_bank_items:
        fallback_res = await db.execute(select(Question).limit(request.total_questions))
        q_bank_items = list(fallback_res.scalars().all())

    session = InterviewSession(
        user_id=user.id,
        role=request.role,
        difficulty=request.difficulty,
        status="in_progress",
        total_questions=min(request.total_questions, len(q_bank_items)),
        current_question_index=0,
    )
    db.add(session)
    await db.flush()

    for idx, item in enumerate(q_bank_items[:request.total_questions]):
        iq = InterviewQuestion(
            session_id=session.id,
            question_bank_id=item.id,
            question_text=item.question,
            category=item.category,
            difficulty=item.difficulty,
            question_order=idx,
            explanation=item.explanation,
        )
        db.add(iq)

    await db.commit()
    return await get_interview_session(db, user_id=user.id, session_id=session.id)


async def get_interview_session(
    db: AsyncSession, user_id: int, session_id: int
) -> InterviewSessionResponse:
    """Get interview session state by ID."""
    res = await db.execute(
        select(InterviewSession).where(
            InterviewSession.id == session_id, InterviewSession.user_id == user_id
        )
    )
    session = res.scalar_one_or_none()

    if not session:
        raise AppException(message="Interview session not found.", status_code=404)

    return await format_session_schema(session)


async def submit_and_evaluate_answer(
    db: AsyncSession,
    user: User,
    session_id: int,
    question_id: int,
    user_answer: str,
    ai_provider: AIProvider | None = None,
) -> InterviewSessionResponse:
    """Evaluate candidate answer using Ollama against 6-metric rubric and advance session progress."""
    res = await db.execute(
        select(InterviewSession).where(
            InterviewSession.id == session_id, InterviewSession.user_id == user.id
        )
    )
    session = res.scalar_one_or_none()

    if not session:
        raise AppException(message="Interview session not found.", status_code=404)

    if session.status != "in_progress":
        raise AppException(message="This interview session has already been completed.", status_code=400)

    # Verify active question
    q_res = await db.execute(
        select(InterviewQuestion).where(
            InterviewQuestion.id == question_id, InterviewQuestion.session_id == session.id
        )
    )
    active_q = q_res.scalar_one_or_none()

    if not active_q:
        raise AppException(message="Invalid question for this session.", status_code=404)

    # Formulate evaluation prompt
    provider = ai_provider or get_ai_provider()
    prompt = EVALUATE_ANSWER_PROMPT_TEMPLATE.format(
        role=session.role,
        difficulty=session.difficulty,
        question_text=active_q.question_text,
        question_explanation=active_q.explanation or "Not provided",
        user_answer=user_answer,
    )

    try:
        raw_response = await provider.generate(
            prompt,
            format="json",
            options={"num_predict": 900, "num_ctx": 4096, "temperature": 0.2},
        )
    except ConnectionError as exc:
        logger.warning("Ollama connection error during answer evaluation: %s", exc)
        raise AppException(
            message="AI Service (Ollama) is currently unavailable. Please ensure Ollama is running.",
            status_code=503,
        ) from exc
    except Exception as exc:
        logger.error("Ollama generation error evaluating answer: %s", exc)
        raise AppException(message=f"AI evaluation error: {exc}", status_code=502) from exc

    # Parse and validate AI payload strictly using robust JSON extractor
    from app.integrations.ai.json_utils import extract_and_parse_json

    parsed = extract_and_parse_json(raw_response)
    if not isinstance(parsed, dict):
        logger.warning("AI answer evaluation returned non-dict response: %s", raw_response)
        raise AppException(
            message="AI provider failed to generate a valid rubric evaluation. Please try again.",
            status_code=502,
        )

    tech_score = float(parsed.get("technical_correctness", 75.0))
    overall = float(parsed.get("overall_score", tech_score))

    eval_payload = AIAnswerEvaluationPayload(
        technical_correctness=tech_score,
        relevance=float(parsed.get("relevance", tech_score)),
        completeness=float(parsed.get("completeness", tech_score)),
        communication=float(parsed.get("communication", 80.0)),
        structure=float(parsed.get("structure", 80.0)),
        clarity=float(parsed.get("clarity", tech_score)),
        overall_score=overall,
        feedback=str(parsed.get("feedback", "Answer evaluation completed.")),
        strengths=list(parsed.get("strengths", ["Addressed the core question"])),
        improvements=list(parsed.get("improvements", ["Elaborate on implementation details and trade-offs"])),
        ideal_answer=parsed.get("ideal_answer"),
    )


    # Create Answer and Evaluation ORM records
    answer_orm = InterviewAnswer(
        session_id=session.id,
        question_id=active_q.id,
        user_answer=user_answer,
    )
    db.add(answer_orm)
    await db.flush()

    eval_orm = InterviewEvaluation(
        answer_id=answer_orm.id,
        technical_correctness=eval_payload.technical_correctness,
        relevance=eval_payload.relevance,
        completeness=eval_payload.completeness,
        communication=eval_payload.communication,
        structure=eval_payload.structure,
        clarity=eval_payload.clarity,
        overall_score=eval_payload.overall_score,
        feedback=eval_payload.feedback,
        strengths=eval_payload.strengths,
        improvements=eval_payload.improvements,
        ideal_answer=eval_payload.ideal_answer,
    )
    db.add(eval_orm)

    # Advance current question index
    session.current_question_index += 1

    # Check if session completed
    if session.current_question_index >= session.total_questions:
        session.status = "completed"
        session.completed_at = datetime.now()

        # Compute overall session score
        evals_query = select(InterviewEvaluation).join(InterviewAnswer).where(InterviewAnswer.session_id == session.id)
        evals_res = await db.execute(evals_query)
        all_evals = evals_res.scalars().all()

        if all_evals:
            session.overall_score = round(sum(ev.overall_score for ev in all_evals) / len(all_evals), 1)
            session.summary_feedback = f"Completed mock interview for {session.role} with an overall score of {session.overall_score}%."

    await db.commit()
    return await get_interview_session(db, user_id=user.id, session_id=session.id)


async def get_interview_results(
    db: AsyncSession, user_id: int, session_id: int
) -> InterviewResultsResponse:
    """Retrieve final interview performance report and rubric metric breakdown."""
    session_resp = await get_interview_session(db, user_id=user_id, session_id=session_id)

    evals_query = select(InterviewEvaluation).join(InterviewAnswer).where(InterviewAnswer.session_id == session_id)
    evals_res = await db.execute(evals_query)
    all_evals = evals_res.scalars().all()

    if not all_evals:
        raise AppException(message="No answer evaluations found for this interview session.", status_code=404)

    tech_avg = round(sum(e.technical_correctness for e in all_evals) / len(all_evals), 1)
    rel_avg = round(sum(e.relevance for e in all_evals) / len(all_evals), 1)
    comp_avg = round(sum(e.completeness for e in all_evals) / len(all_evals), 1)
    comm_avg = round(sum(e.communication for e in all_evals) / len(all_evals), 1)
    struct_avg = round(sum(e.structure for e in all_evals) / len(all_evals), 1)
    clar_avg = round(sum(e.clarity for e in all_evals) / len(all_evals), 1)
    overall_avg = session_resp.overall_score or round(sum(e.overall_score for e in all_evals) / len(all_evals), 1)

    all_strengths: list[str] = []
    all_improvements: list[str] = []
    for e in all_evals:
        all_strengths.extend(e.strengths or [])
        all_improvements.extend(e.improvements or [])

    unique_strengths = list(set(all_strengths))[:5]
    unique_improvements = list(set(all_improvements))[:5]

    return InterviewResultsResponse(
        session_id=session_resp.id,
        user_id=user_id,
        role=session_resp.role,
        difficulty=session_resp.difficulty,
        overall_score=overall_avg,
        metrics_breakdown={
            "Technical Correctness": tech_avg,
            "Relevance": rel_avg,
            "Completeness": comp_avg,
            "Communication": comm_avg,
            "Structure": struct_avg,
            "Clarity": clar_avg,
        },
        summary_feedback=session_resp.summary_feedback or f"Completed {session_resp.role} interview evaluation.",
        strengths=unique_strengths,
        improvements=unique_improvements,
        questions_transcript=session_resp.questions,
        completed_at=session_resp.completed_at,
    )


async def list_user_interviews(db: AsyncSession, user_id: int) -> list[InterviewSessionResponse]:
    """Retrieve history of user's past and active mock interview sessions."""
    query = (
        select(InterviewSession)
        .where(InterviewSession.user_id == user_id)
        .order_by(InterviewSession.created_at.desc())
    )
    res = await db.execute(query)
    sessions = res.scalars().all()

    return [await format_session_schema(s) for s in sessions]
