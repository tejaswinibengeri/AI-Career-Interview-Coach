"""
Interview Question Bank API Router.
"""

from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.question import GenerateQuestionsRequest, QuestionResponse
from app.schemas.user import APIEnvelope
from app.services.question_service import (
    generate_ai_questions,
    get_question_by_id,
    get_random_question,
    list_questions,
    save_question_for_user,
    unsave_question_for_user,
)

router = APIRouter(prefix="/questions", tags=["Interview Question Bank"])


@router.get(
    "",
    response_model=APIEnvelope[List[QuestionResponse]],
    status_code=status.HTTP_200_OK,
    summary="Browse and filter interview questions",
)
async def get_questions(
    category: str | None = Query(None, description="Technical, HR, Behavioral, Coding, DSA, SQL, Aptitude, Role-specific"),
    difficulty: str | None = Query(None, description="Easy, Medium, Hard"),
    role: str | None = Query(None, description="Target job role"),
    q: str | None = Query(None, description="Search text query"),
    source_type: str | None = Query(None, description="standard or ai_generated"),
    saved_only: bool = Query(False, description="Filter for bookmarked questions"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[List[QuestionResponse]]:
    """Retrieve filtered interview questions from the question bank."""
    questions = await list_questions(
        db,
        user=current_user,
        category=category,
        difficulty=difficulty,
        role=role,
        q=q,
        source_type=source_type,
        saved_only=saved_only,
        page=page,
        limit=limit,
    )
    return APIEnvelope(
        status="success",
        message="Questions retrieved successfully.",
        data=questions,
    )


@router.get(
    "/random",
    response_model=APIEnvelope[QuestionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get a random practice question",
)
async def get_random(
    category: str | None = Query(None),
    difficulty: str | None = Query(None),
    role: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[QuestionResponse]:
    """Retrieve a single random practice question matching criteria."""
    question = await get_random_question(
        db, user=current_user, category=category, difficulty=difficulty, role=role
    )
    return APIEnvelope(
        status="success",
        message="Random practice question retrieved.",
        data=question,
    )


@router.post(
    "/generate",
    response_model=APIEnvelope[List[QuestionResponse]],
    status_code=status.HTTP_200_OK,
    summary="Generate personalized AI practice questions",
)
async def generate_questions(
    body: GenerateQuestionsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[List[QuestionResponse]]:
    """Generate structured practice questions using Ollama, explicitly marked as 'AI-generated practice question'."""
    questions = await generate_ai_questions(db, user=current_user, request=body)
    return APIEnvelope(
        status="success",
        message="AI practice questions generated successfully.",
        data=questions,
    )


@router.get(
    "/{id}",
    response_model=APIEnvelope[QuestionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get question detail by ID",
)
async def get_question(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[QuestionResponse]:
    """Retrieve full details for a specific interview question."""
    question = await get_question_by_id(db, question_id=id, user_id=current_user.id)
    return APIEnvelope(
        status="success",
        message="Question detail retrieved successfully.",
        data=question,
    )


@router.post(
    "/{id}/save",
    response_model=APIEnvelope[QuestionResponse],
    status_code=status.HTTP_200_OK,
    summary="Bookmark/Save an interview question",
)
async def save_question(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[QuestionResponse]:
    """Save an interview question to user's favorites list."""
    question = await save_question_for_user(db, user=current_user, question_id=id)
    return APIEnvelope(
        status="success",
        message="Question saved to bookmarks.",
        data=question,
    )


@router.delete(
    "/{id}/save",
    response_model=APIEnvelope[QuestionResponse],
    status_code=status.HTTP_200_OK,
    summary="Remove a question bookmark",
)
async def unsave_question(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[QuestionResponse]:
    """Remove a question from user's favorites list."""
    question = await unsave_question_for_user(db, user=current_user, question_id=id)
    return APIEnvelope(
        status="success",
        message="Question removed from bookmarks.",
        data=question,
    )
