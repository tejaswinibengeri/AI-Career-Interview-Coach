"""
Tests for Notifications and Notification Preferences System (Module 19).
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_notifications_and_real_state_generation(client: AsyncClient, auth_headers: dict[str, str]):
    """GET /api/v1/notifications generates real-state notifications and returns unread count."""
    res = await client.get("/api/v1/notifications", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]

    assert "unread_count" in data
    assert "notifications" in data
    assert isinstance(data["notifications"], list)


@pytest.mark.asyncio
async def test_mark_notification_as_read(client: AsyncClient, auth_headers: dict[str, str]):
    """PATCH /api/v1/notifications/{id}/read updates notification read status."""
    res1 = await client.get("/api/v1/notifications", headers=auth_headers)
    notifications = res1.json()["data"]["notifications"]

    if notifications:
        notif_id = notifications[0]["id"]
        res_read = await client.patch(f"/api/v1/notifications/{notif_id}/read", headers=auth_headers)
        assert res_read.status_code == 200
        assert res_read.json()["data"]["is_read"] is True


@pytest.mark.asyncio
async def test_mark_all_notifications_as_read(client: AsyncClient, auth_headers: dict[str, str]):
    """PATCH /api/v1/notifications/read-all marks all notifications read."""
    # Populate notifications first
    res_before = await client.get("/api/v1/notifications", headers=auth_headers)
    assert res_before.status_code == 200

    # Mark all read
    res_mark = await client.patch("/api/v1/notifications/read-all", headers=auth_headers)
    assert res_mark.status_code == 200

    # Verify unread_count is 0
    res_after = await client.get("/api/v1/notifications", headers=auth_headers)
    assert res_after.json()["data"]["unread_count"] == 0


@pytest.mark.asyncio
async def test_notification_preferences_crud(client: AsyncClient, auth_headers: dict[str, str]):
    """GET and PUT /api/v1/notifications/preferences for user settings."""
    # Get preferences
    get_res = await client.get("/api/v1/notifications/preferences", headers=auth_headers)
    assert get_res.status_code == 200
    pref_data = get_res.json()["data"]
    assert pref_data["enable_roadmap_reminders"] is True

    # Update preferences
    update_payload = {
        "enable_roadmap_reminders": False,
        "enable_coding_reminders": True,
    }
    put_res = await client.put(
        "/api/v1/notifications/preferences", json=update_payload, headers=auth_headers
    )
    assert put_res.status_code == 200
    updated_pref = put_res.json()["data"]
    assert updated_pref["enable_roadmap_reminders"] is False
    assert updated_pref["enable_coding_reminders"] is True
