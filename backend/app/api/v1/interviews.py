"""
AI Mock Interview API Router.
"""

from typing import List
from fastapi import APIRouter, Depends, Body, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.interview import (
    CreateInterviewSessionRequest,
    InterviewResultsResponse,
    InterviewSessionResponse,
    SubmitAnswerRequest,
)
from app.schemas.user import APIEnvelope
from app.services.interview_service import (
    create_interview_session,
    get_interview_results,
    get_interview_session,
    list_user_interviews,
    submit_and_evaluate_answer,
)

router = APIRouter(prefix="/interviews", tags=["AI Mock Interview"])


@router.post(
    "",
    response_model=APIEnvelope[InterviewSessionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Start a new AI Mock Interview session",
)
async def create_session(
    body: CreateInterviewSessionRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[InterviewSessionResponse]:
    """Initiate a new interactive mock interview session with relevant questions."""
    session = await create_interview_session(db, user=current_user, request=body)
    return APIEnvelope(
        status="success",
        message="Mock interview session initiated successfully.",
        data=session,
    )


@router.get(
    "",
    response_model=APIEnvelope[List[InterviewSessionResponse]],
    status_code=status.HTTP_200_OK,
    summary="List user's mock interview history",
)
async def list_interviews(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[List[InterviewSessionResponse]]:
    """Retrieve history of user's past and active mock interview sessions."""
    sessions = await list_user_interviews(db, user_id=current_user.id)
    return APIEnvelope(
        status="success",
        message="Interview sessions retrieved successfully.",
        data=sessions,
    )


@router.get(
    "/{id}",
    response_model=APIEnvelope[InterviewSessionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get active interview session state",
)
async def get_session(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[InterviewSessionResponse]:
    """Retrieve state and current active question for an interview session (supports browser refresh)."""
    session = await get_interview_session(db, user_id=current_user.id, session_id=id)
    return APIEnvelope(
        status="success",
        message="Interview session state retrieved.",
        data=session,
    )


@router.post(
    "/{id}/answer",
    response_model=APIEnvelope[InterviewSessionResponse],
    status_code=status.HTTP_200_OK,
    summary="Submit answer and evaluate via Ollama",
)
async def submit_answer(
    id: int,
    body: SubmitAnswerRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[InterviewSessionResponse]:
    """Submit candidate response for evaluation against 6-metric rubric via Ollama."""
    session = await submit_and_evaluate_answer(
        db,
        user=current_user,
        session_id=id,
        question_id=body.question_id,
        user_answer=body.user_answer,
    )
    return APIEnvelope(
        status="success",
        message="Answer evaluated and recorded successfully.",
        data=session,
    )


@router.get(
    "/{id}/results",
    response_model=APIEnvelope[InterviewResultsResponse],
    status_code=status.HTTP_200_OK,
    summary="Get final interview performance report",
)
async def get_results(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[InterviewResultsResponse]:
    """Retrieve completed interview performance report, metric breakdown, and full question transcript."""
    results = await get_interview_results(db, user_id=current_user.id, session_id=id)
    return APIEnvelope(
        status="success",
        message="Interview results report retrieved successfully.",
        data=results,
    )
