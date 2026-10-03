"""
Tests for Resume Version History & Side-by-Side Comparison System (Module 16).
"""

import fitz  # PyMuPDF
import pytest
from httpx import AsyncClient


def create_sample_pdf_bytes(text_content: str) -> bytes:
    """Helper to generate a valid PDF file in memory."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text_content)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.mark.asyncio
async def test_resume_version_history_and_comparison(client: AsyncClient, auth_headers: dict[str, str]):
    """Test uploading multiple versions, checking score evolution trajectory, comparing versions, and deleting versions."""
    # 1. Upload initial version (v1)
    pdf_v1 = create_sample_pdf_bytes("Alex Mercer - Software Developer with Python and SQL skills.")
    res1 = await client.post(
        "/api/v1/resumes",
        files={"file": ("resume_v1.pdf", pdf_v1, "application/pdf")},
        headers=auth_headers,
    )
    assert res1.status_code == 201
    resume_id = res1.json()["data"]["id"]

    # 2. Upload second version (v2) to same resume_id
    pdf_v2 = create_sample_pdf_bytes("Alex Mercer - Senior Engineer with Python, FastAPI, Docker, and React skills.")
    res2 = await client.post(
        "/api/v1/resumes",
        data={"resume_id": str(resume_id)},
        files={"file": ("resume_v2.pdf", pdf_v2, "application/pdf")},
        headers=auth_headers,
    )
    assert res2.status_code == 201
    assert res2.json()["data"]["current_version"]["version_number"] == 2

    # 3. GET /api/v1/resumes/{id}/history
    hist_res = await client.get(f"/api/v1/resumes/{resume_id}/history", headers=auth_headers)
    assert hist_res.status_code == 200
    hist_data = hist_res.json()["data"]
    assert hist_data["total_versions"] == 2
    assert len(hist_data["versions"]) == 2

    v1_id = hist_data["versions"][1]["id"]
    v2_id = hist_data["versions"][0]["id"]

    # 4. GET /api/v1/resumes/{id}/compare?v1={v1_id}&v2={v2_id}
    comp_res = await client.get(
        f"/api/v1/resumes/{resume_id}/compare?v1={v1_id}&v2={v2_id}",
        headers=auth_headers,
    )
    assert comp_res.status_code == 200
    comp_data = comp_res.json()["data"]
    assert comp_data["v1_version_number"] == 1
    assert comp_data["v2_version_number"] == 2

    # 5. DELETE /api/v1/resumes/{id}/versions/{v2_id}
    del_res = await client.delete(
        f"/api/v1/resumes/{resume_id}/versions/{v2_id}",
        headers=auth_headers,
    )
    assert del_res.status_code == 200

    # 6. Verify v1 is now current version
    check_res = await client.get(f"/api/v1/resumes/{resume_id}", headers=auth_headers)
    assert check_res.status_code == 200
    assert check_res.json()["data"]["current_version"]["version_number"] == 1
