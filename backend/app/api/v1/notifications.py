"""
Notifications API Router (Module 19).
"""

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationPreferenceRequest,
    NotificationPreferenceResponse,
    NotificationResponse,
)
from app.schemas.user import APIEnvelope
from app.services.notification_service import (
    delete_notification,
    get_user_notification_preferences,
    get_user_notifications,
    mark_all_notifications_as_read,
    mark_notification_as_read,
    update_user_notification_preferences,
)

router = APIRouter(prefix="/notifications", tags=["Notifications System"])


@router.get(
    "",
    response_model=APIEnvelope[NotificationListResponse],
    status_code=status.HTTP_200_OK,
    summary="List in-app notifications and unread counter",
)
async def list_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[NotificationListResponse]:
    """Retrieve notifications generated from real candidate application state."""
    data = await get_user_notifications(db, user=current_user)
    return APIEnvelope(
        status="success",
        message="Notifications retrieved successfully.",
        data=data,
    )


@router.patch(
    "/{id}/read",
    response_model=APIEnvelope[NotificationResponse],
    status_code=status.HTTP_200_OK,
    summary="Mark single notification as read",
)
async def read_notification(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[NotificationResponse]:
    """Update notification state to read."""
    updated = await mark_notification_as_read(db, user=current_user, notification_id=id)
    return APIEnvelope(
        status="success",
        message="Notification marked as read.",
        data=updated,
    )


@router.patch(
    "/read-all",
    response_model=APIEnvelope[None],
    status_code=status.HTTP_200_OK,
    summary="Mark all notifications as read",
)
async def read_all_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[None]:
    """Mark all unread notifications as read."""
    await mark_all_notifications_as_read(db, user=current_user)
    return APIEnvelope(
        status="success",
        message="All notifications marked as read.",
        data=None,
    )


@router.delete(
    "/{id}",
    response_model=APIEnvelope[None],
    status_code=status.HTTP_200_OK,
    summary="Delete a notification",
)
async def remove_notification(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[None]:
    """Delete a notification."""
    await delete_notification(db, user=current_user, notification_id=id)
    return APIEnvelope(
        status="success",
        message="Notification deleted.",
        data=None,
    )


@router.get(
    "/preferences",
    response_model=APIEnvelope[NotificationPreferenceResponse],
    status_code=status.HTTP_200_OK,
    summary="Get user notification preferences",
)
async def get_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[NotificationPreferenceResponse]:
    """Retrieve candidate notification category preferences."""
    pref = await get_user_notification_preferences(db, user=current_user)
    return APIEnvelope(
        status="success",
        message="Notification preferences retrieved.",
        data=pref,
    )


@router.put(
    "/preferences",
    response_model=APIEnvelope[NotificationPreferenceResponse],
    status_code=status.HTTP_200_OK,
    summary="Update user notification preferences",
)
async def update_preferences(
    body: NotificationPreferenceRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIEnvelope[NotificationPreferenceResponse]:
    """Update candidate notification category preferences."""
    pref = await update_user_notification_preferences(db, user=current_user, request=body)
    return APIEnvelope(
        status="success",
        message="Notification preferences updated successfully.",
        data=pref,
    )
