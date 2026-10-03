"""
Admin Panel System API Router (Module 20).
All endpoints strictly protected by get_current_admin_user dependency.
"""

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user, get_db
from app.models.user import User
from app.schemas.admin import (
    AdminQuestionCreate,
    AdminResourceCreate,
    AdminSystemStatsResponse,
    AdminUserResponse,
    AdminUserRoleUpdate,
)
from app.schemas.learning_resource import LearningResourceResponse
from app.schemas.question import QuestionResponse
from app.schemas.user import APIEnvelope
from app.services.admin_service import (
    create_admin_question,
    create_admin_resource,
    delete_admin_question,
    delete_admin_resource,
    delete_admin_user,
    get_admin_questions,
    get_admin_resources,
    get_admin_system_statistics,
    get_admin_users,
    update_admin_user,
)

router = APIRouter(prefix="/admin", tags=["Admin Panel System"])


@router.get(
    "/statistics",
    response_model=APIEnvelope[AdminSystemStatsResponse],
    status_code=status.HTTP_200_OK,
    summary="Get real database aggregated system statistics",
)
async def get_system_statistics(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[AdminSystemStatsResponse]:
    """Calculate and return real database aggregated application metrics."""
    stats = await get_admin_system_statistics(db)
    return APIEnvelope(
        status="success",
        message="System statistics calculated successfully.",
        data=stats,
    )


@router.get(
    "/users",
    response_model=APIEnvelope[list[AdminUserResponse]],
    status_code=status.HTTP_200_OK,
    summary="List all registered users",
)
async def list_users(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[list[AdminUserResponse]]:
    """Retrieve user list with privacy protection (no private resume text dumped)."""
    users = await get_admin_users(db)
    return APIEnvelope(
        status="success",
        message="Users list retrieved.",
        data=users,
    )


@router.patch(
    "/users/{id}/role",
    response_model=APIEnvelope[AdminUserResponse],
    status_code=status.HTTP_200_OK,
    summary="Update user role or active status",
)
async def update_user_role(
    id: int,
    body: AdminUserRoleUpdate = Body(...),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[AdminUserResponse]:
    """Promote/demote user role or toggle active state."""
    updated = await update_admin_user(db, target_user_id=id, payload=body)
    return APIEnvelope(
        status="success",
        message="User permissions updated.",
        data=updated,
    )


@router.delete(
    "/users/{id}",
    response_model=APIEnvelope[None],
    status_code=status.HTTP_200_OK,
    summary="Delete a user",
)
async def remove_user(
    id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[None]:
    """Delete user from platform."""
    await delete_admin_user(db, target_user_id=id)
    return APIEnvelope(
        status="success",
        message="User deleted successfully.",
        data=None,
    )


@router.get(
    "/questions",
    response_model=APIEnvelope[list[QuestionResponse]],
    status_code=status.HTTP_200_OK,
    summary="List all question bank items",
)
async def list_questions(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[list[QuestionResponse]]:
    """List questions in question bank."""
    questions = await get_admin_questions(db)
    items = [QuestionResponse.model_validate(q) for q in questions]
    return APIEnvelope(
        status="success",
        message="Questions retrieved.",
        data=items,
    )


@router.post(
    "/questions",
    response_model=APIEnvelope[QuestionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new question bank item",
)
async def add_question(
    body: AdminQuestionCreate = Body(...),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[QuestionResponse]:
    """Add a question to question bank."""
    q = await create_admin_question(db, payload=body)
    return APIEnvelope(
        status="success",
        message="Question created successfully.",
        data=QuestionResponse.model_validate(q),
    )


@router.delete(
    "/questions/{id}",
    response_model=APIEnvelope[None],
    status_code=status.HTTP_200_OK,
    summary="Delete a question bank item",
)
async def remove_question(
    id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[None]:
    """Delete a question."""
    await delete_admin_question(db, question_id=id)
    return APIEnvelope(
        status="success",
        message="Question deleted successfully.",
        data=None,
    )


@router.get(
    "/resources",
    response_model=APIEnvelope[list[LearningResourceResponse]],
    status_code=status.HTTP_200_OK,
    summary="List verified learning resources",
)
async def list_resources(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[list[LearningResourceResponse]]:
    """List verified learning resources catalog."""
    resources = await get_admin_resources(db)
    items = [LearningResourceResponse.model_validate(r) for r in resources]
    return APIEnvelope(
        status="success",
        message="Learning resources retrieved.",
        data=items,
    )


@router.post(
    "/resources",
    response_model=APIEnvelope[LearningResourceResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new learning resource",
)
async def add_resource(
    body: AdminResourceCreate = Body(...),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[LearningResourceResponse]:
    """Add verified learning resource."""
    lr = await create_admin_resource(db, payload=body)
    return APIEnvelope(
        status="success",
        message="Resource created successfully.",
        data=LearningResourceResponse.model_validate(lr),
    )


@router.delete(
    "/resources/{id}",
    response_model=APIEnvelope[None],
    status_code=status.HTTP_200_OK,
    summary="Delete a learning resource",
)
async def remove_resource(
    id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[None]:
    """Delete learning resource."""
    await delete_admin_resource(db, resource_id=id)
    return APIEnvelope(
        status="success",
        message="Resource deleted successfully.",
        data=None,
    )
