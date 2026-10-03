"""
Tests for Achievements and Badges System (Module 18).
"""

import fitz  # PyMuPDF
import pytest
from httpx import AsyncClient


def create_sample_pdf_bytes(text_content: str = "Test resume content") -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text_content)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.mark.asyncio
async def test_get_initial_user_achievements(client: AsyncClient, auth_headers: dict[str, str]):
    """GET /api/v1/achievements initializes catalog and returns initial locked states for new user."""
    res = await client.get("/api/v1/achievements", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["total_achievements"] >= 9
    assert data["earned_count"] == 0
    assert data["completion_percentage"] == 0.0

    # Verify locked status for new user
    for ach in data["achievements"]:
        assert ach["is_earned"] is False


@pytest.mark.asyncio
async def test_achievement_automatic_unlock_on_real_user_activity(client: AsyncClient, auth_headers: dict[str, str]):
    """Achievement is automatically awarded when real user action (e.g. uploading a resume) occurs."""
    # 1. Initially first_resume achievement is locked
    res1 = await client.get("/api/v1/achievements", headers=auth_headers)
    ach_list1 = res1.json()["data"]["achievements"]
    first_resume_ach1 = next(a for a in ach_list1 if a["slug"] == "first_resume")
    assert first_resume_ach1["is_earned"] is False

    # 2. User performs real activity: Uploads a resume
    pdf_bytes = create_sample_pdf_bytes("Alex Mercer - Senior Software Engineer")
    upload_res = await client.post(
        "/api/v1/resumes",
        files={"file": ("my_resume.pdf", pdf_bytes, "application/pdf")},
        headers=auth_headers,
    )
    assert upload_res.status_code == 201

    # 3. GET /api/v1/achievements automatically evaluates and awards 'first_resume' badge
    res2 = await client.get("/api/v1/achievements", headers=auth_headers)
    ach_list2 = res2.json()["data"]["achievements"]
    first_resume_ach2 = next(a for a in ach_list2 if a["slug"] == "first_resume")

    assert first_resume_ach2["is_earned"] is True
    assert first_resume_ach2["current_progress"] == 1
    assert first_resume_ach2["earned_at"] is not None
    assert res2.json()["data"]["earned_count"] >= 1
