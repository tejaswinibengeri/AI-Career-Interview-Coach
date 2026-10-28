"""
Enterprise Security Verification & Penetration Regression Test Suite.
Validates all hardened controls implemented during the security engagement:
1. Python Code Execution Sandbox RCE & Escape Defenses (CRIT-01)
2. SQL Sandbox Query Boundary Defenses (CRIT-01)
3. Password Recovery Anti-Enumeration & Production Secret Suppression (CRIT-02)
4. Password Complexity Enforcement (MED-02)
5. Server-Side Token Revocation & Invalidation on Logout (HIGH-01)
6. Enterprise Security Response Headers Injection (MED-01)
7. Request Payload Size Limiting (HIGH-03)
8. Administrator Self-Lockout & Self-Deletion Protection (MED-05)
9. File Upload Magic Byte Signature Verification (MED-03)
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.services.code_executor import execute_code_safely


# =============================================================================
# 1. Python & SQL Sandbox Security Verification (CRIT-01)
# =============================================================================

def test_sandbox_blocks_os_import():
    """Verify that importing 'os' is blocked by AST security analyzer."""
    malicious_code = "import os\ndef solution(): return os.getcwd()"
    test_cases = [{"input": "", "expected_output": ""}]
    status, passed, total, _, results = execute_code_safely("python", malicious_code, test_cases)
    assert status == "Security Violation"
    assert passed == 0
    assert "prohibited" in results[0].error_output.lower()


def test_sandbox_blocks_subprocess_import():
    """Verify that importing 'subprocess' is blocked."""
    malicious_code = "from subprocess import run\ndef solution(): return run('whoami')"
    test_cases = [{"input": "", "expected_output": ""}]
    status, passed, total, _, results = execute_code_safely("python", malicious_code, test_cases)
    assert status == "Security Violation"
    assert "prohibited" in results[0].error_output.lower()


def test_sandbox_blocks_open_call():
    """Verify that calling 'open()' is blocked."""
    malicious_code = "def solution():\n    with open('.env') as f: return f.read()"
    test_cases = [{"input": "", "expected_output": ""}]
    status, passed, total, _, results = execute_code_safely("python", malicious_code, test_cases)
    assert status == "Security Violation"
    assert "open()" in results[0].error_output


def test_sandbox_blocks_reflection_escape():
    """Verify that accessing '__subclasses__' or dunder attributes is blocked."""
    malicious_code = "def solution(): return ().__class__.__bases__[0].__subclasses__()"
    test_cases = [{"input": "", "expected_output": ""}]
    status, passed, total, _, results = execute_code_safely("python", malicious_code, test_cases)
    assert status == "Security Violation"


def test_sql_sandbox_blocks_attach_database():
    """Verify that SQL queries with ATTACH DATABASE are blocked."""
    malicious_sql = "ATTACH DATABASE 'career_coach.db' AS stolen; SELECT * FROM stolen.users;"
    test_cases = [{"input": "test", "expected_output": "[]"}]
    status, passed, total, _, results = execute_code_safely("sql", malicious_sql, test_cases)
    assert status == "Security Violation"
    assert "not permitted" in results[0].error_output


# =============================================================================
# 2. Password Reset Anti-Enumeration & Production Suppression (CRIT-02)
# =============================================================================

@pytest.mark.asyncio
async def test_forgot_password_anti_enumeration(client: AsyncClient):
    """Requesting password reset for non-existent account returns identical 200 message."""
    resp = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "completely_unregistered_ghost_email@example.com"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "dispatched" in data["message"].lower()


@pytest.mark.asyncio
async def test_forgot_password_suppresses_token_in_production(client: AsyncClient, sample_user: User):
    """In production environment, reset_token is strictly omitted from the API response."""
    original_env = settings.ENVIRONMENT
    try:
        settings.ENVIRONMENT = "production"
        resp = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": sample_user.email},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["reset_token"] is None
    finally:
        settings.ENVIRONMENT = original_env


# =============================================================================
# 3. Password Complexity Enforcement (MED-02)
# =============================================================================

@pytest.mark.asyncio
async def test_register_rejects_weak_password(client: AsyncClient):
    """Registration rejects passwords under 8 characters or lacking required character classes."""
    # Under 8 chars
    resp_short = await client.post(
        "/api/v1/auth/register",
        json={"name": "Test User", "email": "weak1@example.com", "password": "123"},
    )
    assert resp_short.status_code == 422

    # 8 chars but only numbers (no letters)
    resp_digits = await client.post(
        "/api/v1/auth/register",
        json={"name": "Test User", "email": "weak2@example.com", "password": "12345678"},
    )
    assert resp_digits.status_code == 422

    # 8 chars but only letters (no digits or symbols)
    resp_letters = await client.post(
        "/api/v1/auth/register",
        json={"name": "Test User", "email": "weak3@example.com", "password": "abcdefgh"},
    )
    assert resp_letters.status_code == 422


# =============================================================================
# 4. Server-Side Token Revocation on Logout (HIGH-01)
# =============================================================================

@pytest.mark.asyncio
async def test_logout_revokes_token_server_side(client: AsyncClient, sample_user: User):
    """Logging out revokes the bearer token immediately; subsequent requests are rejected."""
    token = create_access_token({"sub": str(sample_user.id), "email": sample_user.email})
    headers = {"Authorization": f"Bearer {token}"}

    # Verify token works initially
    me_resp = await client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200

    # Log out
    logout_resp = await client.post("/api/v1/auth/logout", headers=headers)
    assert logout_resp.status_code == 200

    # Verify revoked token is immediately rejected with 401
    me_after = await client.get("/api/v1/auth/me", headers=headers)
    assert me_after.status_code == 401
    assert "revoked" in me_after.json()["message"].lower()


# =============================================================================
# 5. Security Response Headers (MED-01)
# =============================================================================

@pytest.mark.asyncio
async def test_security_headers_present(client: AsyncClient):
    """Responses include enterprise-grade OWASP security headers."""
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200

    headers = resp.headers
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "default-src" in headers.get("content-security-policy", "")
    assert "camera=()" in headers.get("permissions-policy", "")


# =============================================================================
# 6. Request Size Limiter (HIGH-03)
# =============================================================================

@pytest.mark.asyncio
async def test_oversized_payload_rejected(client: AsyncClient):
    """Requests with Content-Length exceeding allowed limit receive 413 Payload Too Large."""
    # 5MB header on standard JSON route (limit is 2MB)
    headers = {"Content-Length": str(5 * 1024 * 1024)}
    resp = await client.post("/api/v1/auth/login", headers=headers, json={"email": "x@x.com", "password": "x"})
    assert resp.status_code == 413
    assert "Payload Too Large" in resp.json()["message"]


# =============================================================================
# 7. Administrator Self-Protection & Lockout Prevention (MED-05)
# =============================================================================

@pytest.mark.asyncio
async def test_admin_cannot_delete_or_demote_self(
    client: AsyncClient, sample_user: User, db_session: AsyncSession
):
    """Admins cannot delete their own active account or revoke their own admin permissions."""
    sample_user.is_superuser = True
    sample_user.role = "admin"
    await db_session.commit()

    token = create_access_token({"sub": str(sample_user.id), "email": sample_user.email})
    admin_headers = {"Authorization": f"Bearer {token}"}

    # Attempt self-deletion -> 400 Bad Request
    del_resp = await client.delete(f"/api/v1/admin/users/{sample_user.id}", headers=admin_headers)
    assert del_resp.status_code == 400
    assert "cannot delete their own" in del_resp.json()["message"]

    # Attempt self-demotion -> 400 Bad Request
    demote_resp = await client.patch(
        f"/api/v1/admin/users/{sample_user.id}/role",
        headers=admin_headers,
        json={"role": "user"},
    )
    assert demote_resp.status_code == 400
    assert "cannot revoke their own admin permissions" in demote_resp.json()["message"]


# =============================================================================
# 8. File Upload Magic Byte Signature Verification (MED-03)
# =============================================================================

@pytest.mark.asyncio
async def test_spoofed_file_extension_rejected(client: AsyncClient, auth_headers: dict[str, str]):
    """Uploading plain text or executable bytes disguised as PDF/DOCX is rejected."""
    # Fake PDF (plain text lacking %PDF- header)
    fake_pdf = b"This is plain text pretending to be a PDF."
    resp_pdf = await client.post(
        "/api/v1/resumes",
        files={"file": ("fake_resume.pdf", fake_pdf, "application/pdf")},
        headers=auth_headers,
    )
    assert resp_pdf.status_code == 400
    assert "%pdf-" in resp_pdf.json()["message"].lower()

    # Fake DOCX (plain text lacking PK\x03\x04 zip header)
    fake_docx = b"This is plain text pretending to be a DOCX."
    resp_docx = await client.post(
        "/api/v1/resumes",
        files={"file": ("fake_resume.docx", fake_docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        headers=auth_headers,
    )
    assert resp_docx.status_code == 400
    assert "signature" in resp_docx.json()["message"].lower()


# =============================================================================
# 9. Rate Limiter Throttling Enforcement (HIGH-02)
# =============================================================================

@pytest.mark.asyncio
async def test_rate_limiter_throttles_excessive_requests(client: AsyncClient):
    """Sending requests beyond the quota returns 429 Too Many Requests."""
    simulated_ip = "198.51.100.77"
    headers = {"X-Forwarded-For": simulated_ip}

    # Burst 65 requests to auth login
    hit_429 = False
    for _ in range(65):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "wrong@example.com", "password": "wrong"},
            headers=headers,
        )
        if resp.status_code == 429:
            hit_429 = True
            assert "Rate limit exceeded" in resp.json()["message"]
            assert resp.headers.get("retry-after") == "60"
            break

    assert hit_429 is True
