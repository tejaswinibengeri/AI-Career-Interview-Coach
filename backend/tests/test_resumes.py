"""
Comprehensive test suite for Resume Management (Module 03).
"""

import io
import fitz  # PyMuPDF
import docx
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.user import User


def create_sample_pdf_bytes(text_content: str = "Alex Mercer - Senior Software Engineer with Python skills.") -> bytes:
    """Helper to generate a valid PDF file in memory."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text_content)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_sample_docx_bytes(text_content: str = "John Doe - Senior Data Analyst with SQL and Python.") -> bytes:
    """Helper to generate a valid DOCX file in memory."""
    doc = docx.Document()
    doc.add_paragraph(text_content)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_pdf_resume_upload_success(client: AsyncClient, auth_headers: dict[str, str]):
    """Upload a valid PDF resume file and verify text extraction and metadata."""
    pdf_bytes = create_sample_pdf_bytes("Alex Mercer - Expert Full Stack Engineer")

    files = {
        "file": ("alex_mercer_resume.pdf", pdf_bytes, "application/pdf")
    }
    response = await client.post("/api/v1/resumes", files=files, headers=auth_headers)
    assert response.status_code == 201

    payload = response.json()
    assert payload["status"] == "success"
    data = payload["data"]

    assert data["title"] == "alex_mercer_resume.pdf"
    assert data["current_version"] is not None
    cur_ver = data["current_version"]
    assert cur_ver["version_number"] == 1
    assert cur_ver["file_type"] == "pdf"
    assert cur_ver["is_current"] is True
    assert "Alex Mercer" in cur_ver["extracted_text"]


@pytest.mark.asyncio
async def test_docx_resume_upload_success(client: AsyncClient, auth_headers: dict[str, str]):
    """Upload a valid DOCX resume file and verify text extraction and metadata."""
    docx_bytes = create_sample_docx_bytes("Jane Doe - Lead AI Researcher & Python Dev")

    files = {
        "file": ("jane_doe_cv.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    }
    response = await client.post("/api/v1/resumes", files=files, headers=auth_headers)
    assert response.status_code == 201

    payload = response.json()
    data = payload["data"]

    assert data["title"] == "jane_doe_cv.docx"
    cur_ver = data["current_version"]
    assert cur_ver["file_type"] == "docx"
    assert "Jane Doe" in cur_ver["extracted_text"]


@pytest.mark.asyncio
async def test_resume_versioning(client: AsyncClient, auth_headers: dict[str, str]):
    """Upload initial resume v1, then upload a new version v2 to the existing resume."""
    # Step 1: Upload version 1
    pdf_v1 = create_sample_pdf_bytes("Version 1 content")
    res1 = await client.post(
        "/api/v1/resumes",
        files={"file": ("resume_v1.pdf", pdf_v1, "application/pdf")},
        headers=auth_headers,
    )
    assert res1.status_code == 201
    resume_id = res1.json()["data"]["id"]

    # Step 2: Upload version 2 linked to existing resume_id
    pdf_v2 = create_sample_pdf_bytes("Version 2 updated content")
    res2 = await client.post(
        "/api/v1/resumes",
        files={"file": ("resume_v2.pdf", pdf_v2, "application/pdf")},
        data={"resume_id": str(resume_id)},
        headers=auth_headers,
    )
    assert res2.status_code == 201
    data2 = res2.json()["data"]

    assert data2["id"] == resume_id
    assert len(data2["versions"]) == 2
    assert data2["current_version"]["version_number"] == 2
    assert "Version 2" in data2["current_version"]["extracted_text"]


@pytest.mark.asyncio
async def test_invalid_file_extension(client: AsyncClient, auth_headers: dict[str, str]):
    """Uploading unsupported file formats (.txt, .exe) should fail with 400 Bad Request."""
    files = {
        "file": ("script.sh", b"#!/bin/bash\necho hello", "text/plain")
    }
    response = await client.post("/api/v1/resumes", files=files, headers=auth_headers)
    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["message"]


@pytest.mark.asyncio
async def test_oversized_file(client: AsyncClient, auth_headers: dict[str, str]):
    """Uploading a file exceeding max size limit (10MB) should return 400 Bad Request."""
    # Create fake oversized buffer (>10MB)
    large_bytes = b"0" * (10 * 1024 * 1024 + 1024)
    files = {
        "file": ("large_file.pdf", large_bytes, "application/pdf")
    }
    response = await client.post("/api/v1/resumes", files=files, headers=auth_headers)
    assert response.status_code == 400
    assert "exceeds maximum allowed limit" in response.json()["message"]


@pytest.mark.asyncio
async def test_empty_document(client: AsyncClient, auth_headers: dict[str, str]):
    """Uploading a 0-byte file should return 400 Bad Request."""
    files = {
        "file": ("empty.pdf", b"", "application/pdf")
    }
    response = await client.post("/api/v1/resumes", files=files, headers=auth_headers)
    assert response.status_code == 400
    assert "empty" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_corrupted_document(client: AsyncClient, auth_headers: dict[str, str]):
    """Uploading a file with invalid/corrupt structure should return 400 Bad Request."""
    corrupt_bytes = b"%PDF-1.4 INVALID_CORRUPT_HEADER_NO_STRUCTURE"
    files = {
        "file": ("corrupt.pdf", corrupt_bytes, "application/pdf")
    }
    response = await client.post("/api/v1/resumes", files=files, headers=auth_headers)
    assert response.status_code == 400
    assert "Corrupted or invalid" in response.json()["message"]


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    """Endpoints should require valid authentication token (401 Unauthorized)."""
    get_res = await client.get("/api/v1/resumes")
    assert get_res.status_code == 401

    post_res = await client.post("/api/v1/resumes")
    assert post_res.status_code == 401


@pytest.mark.asyncio
async def test_cross_user_isolation(
    client: AsyncClient, db_session: AsyncSession, sample_user: User, auth_headers: dict[str, str]
):
    """User B cannot view, download, or delete User A's resume."""
    # User A uploads a resume
    pdf_bytes = create_sample_pdf_bytes("User A secret resume")
    upload_res = await client.post(
        "/api/v1/resumes",
        files={"file": ("user_a_resume.pdf", pdf_bytes, "application/pdf")},
        headers=auth_headers,
    )
    assert upload_res.status_code == 201
    resume_a_id = upload_res.json()["data"]["id"]

    # Create User B
    user_b = User(
        email="user_b_resume@example.com",
        name="User B",
        hashed_password=get_password_hash("Password123!"),
        is_active=True,
    )
    db_session.add(user_b)
    await db_session.commit()

    token_b = create_access_token({"sub": str(user_b.id), "email": user_b.email})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B attempts to GET User A's resume -> 404
    get_res = await client.get(f"/api/v1/resumes/{resume_a_id}", headers=headers_b)
    assert get_res.status_code == 404

    # User B attempts to Download User A's resume -> 404
    dl_res = await client.get(f"/api/v1/resumes/{resume_a_id}/download", headers=headers_b)
    assert dl_res.status_code == 404

    # User B attempts to Delete User A's resume -> 404
    del_res = await client.delete(f"/api/v1/resumes/{resume_a_id}", headers=headers_b)
    assert del_res.status_code == 404


@pytest.mark.asyncio
async def test_download_and_delete_resume(client: AsyncClient, auth_headers: dict[str, str]):
    """Test downloading the resume file and deleting it."""
    pdf_bytes = create_sample_pdf_bytes("Downloadable and deletable resume text")
    upload_res = await client.post(
        "/api/v1/resumes",
        files={"file": ("download_test.pdf", pdf_bytes, "application/pdf")},
        headers=auth_headers,
    )
    assert upload_res.status_code == 201
    resume_id = upload_res.json()["data"]["id"]

    # Download resume
    dl_res = await client.get(f"/api/v1/resumes/{resume_id}/download", headers=auth_headers)
    assert dl_res.status_code == 200
    assert dl_res.content == pdf_bytes

    # Delete resume
    del_res = await client.delete(f"/api/v1/resumes/{resume_id}", headers=auth_headers)
    assert del_res.status_code == 200

    # Verify resume no longer exists
    get_res = await client.get(f"/api/v1/resumes/{resume_id}", headers=auth_headers)
    assert get_res.status_code == 404
