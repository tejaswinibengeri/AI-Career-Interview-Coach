"""
Coding Challenge System API Router (Module 12).
"""

from typing import List, Optional
from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.coding import (
    AIHintResponse,
    CodingChallengeResponse,
    CodingSubmissionResponse,
    GenerateChallengeRequest,
    SubmitCodeRequest,
)
from app.schemas.user import APIEnvelope
from app.services.coding_service import (
    generate_ai_hint,
    get_challenge_by_id_or_slug,
    list_challenges,
    list_user_submissions,
    submit_code_solution,
)

router = APIRouter(prefix="/coding", tags=["Coding Challenge System"])


@router.get(
    "/challenges",
    response_model=APIEnvelope[List[CodingChallengeResponse]],
    status_code=status.HTTP_200_OK,
    summary="List coding challenges",
)
async def get_challenges(
    category: Optional[str] = Query(None, description="Python, SQL, DSA"),
    difficulty: Optional[str] = Query(None, description="Easy, Medium, Hard"),
    search: Optional[str] = Query(None, description="Search keyword"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[List[CodingChallengeResponse]]:
    """Retrieve available coding challenges filtered by category, difficulty, or keyword."""
    challenges = await list_challenges(
        db, user=current_user, category=category, difficulty=difficulty, search=search
    )
    return APIEnvelope(
        status="success",
        message="Coding challenges retrieved successfully.",
        data=challenges,
    )


@router.post(
    "/challenges/generate",
    response_model=APIEnvelope[CodingChallengeResponse],
    status_code=status.HTTP_200_OK,
    summary="Generate a custom AI coding challenge",
)
async def generate_custom_challenge(
    payload: GenerateChallengeRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[CodingChallengeResponse]:
    """Generate a custom coding problem using AI for a specific topic/skill."""
    from app.services.coding_service import generate_ai_coding_challenge
    challenge = await generate_ai_coding_challenge(
        db, topic=payload.topic, category=payload.category, difficulty=payload.difficulty
    )
    return APIEnvelope(
        status="success",
        message="Custom AI coding challenge generated successfully.",
        data=challenge,
    )


@router.get(
    "/challenges/{identifier}",

    response_model=APIEnvelope[CodingChallengeResponse],
    status_code=status.HTTP_200_OK,
    summary="Get coding challenge detail by ID or Slug",
)
async def get_challenge_detail(
    identifier: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[CodingChallengeResponse]:
    """Retrieve problem statement, starter code, and sample test cases for a coding challenge."""
    challenge = await get_challenge_by_id_or_slug(db, user=current_user, identifier=identifier)
    return APIEnvelope(
        status="success",
        message="Coding challenge retrieved successfully.",
        data=challenge,
    )


@router.post(
    "/challenges/{id}/submit",
    response_model=APIEnvelope[CodingSubmissionResponse],
    status_code=status.HTTP_200_OK,
    summary="Submit solution for sandbox evaluation",
)
async def submit_challenge(
    id: int,
    body: SubmitCodeRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[CodingSubmissionResponse]:
    """Execute candidate code safely in an isolated sandbox and record submission results."""
    submission = await submit_code_solution(
        db, user=current_user, challenge_id=id, request=body
    )
    return APIEnvelope(
        status="success",
        message="Code submitted and evaluated in sandbox.",
        data=submission,
    )


@router.get(
    "/challenges/{id}/submissions",
    response_model=APIEnvelope[List[CodingSubmissionResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get submission history for a challenge",
)
async def get_submissions(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[List[CodingSubmissionResponse]]:
    """Retrieve candidate's previous submission history and test results for a specific challenge."""
    submissions = await list_user_submissions(db, user=current_user, challenge_id=id)
    return APIEnvelope(
        status="success",
        message="Submissions history retrieved.",
        data=submissions,
    )


@router.post(
    "/challenges/{id}/hint",
    response_model=APIEnvelope[AIHintResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Ollama AI coding hint and explanation",
)
async def get_coding_hint(
    id: int,
    body: SubmitCodeRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[AIHintResponse]:
    """Request Ollama AI guidance and algorithm hints for the challenge (does NOT decide test execution status)."""
    hint_resp = await generate_ai_hint(
        db, user=current_user, challenge_id=id, code=body.code
    )
    return APIEnvelope(
        status="success",
        message="AI coding hint generated successfully.",
        data=hint_resp,
    )
