"""
Tests for Authentication endpoints (/api/v1/auth/*).
"""

import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """POST /api/v1/auth/register should create user and return JWT token."""
    payload = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "password": "SecurePassword123!",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["status"] == "success"
    assert "access_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"
    assert data["data"]["user"]["email"] == "jane@example.com"
    assert data["data"]["user"]["name"] == "Jane Doe"
    assert "hashed_password" not in data["data"]["user"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, sample_user: User):
    """Registration with an already existing email should return 400 error."""
    payload = {
        "name": "Another User",
        "email": sample_user.email,
        "password": "NewPassword123!",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400

    data = response.json()
    assert data["status"] == "error"
    assert "already exists" in data["message"].lower()


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, sample_user: User):
    """POST /api/v1/auth/login with valid credentials returns 200 and access token."""
    payload = {
        "email": sample_user.email,
        "password": "Password123!",
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert "access_token" in data["data"]
    assert data["data"]["user"]["email"] == sample_user.email


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, sample_user: User):
    """POST /api/v1/auth/login with invalid password returns 401."""
    payload = {
        "email": sample_user.email,
        "password": "WrongPassword999!",
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401

    data = response.json()
    assert data["status"] == "error"
    assert "invalid email or password" in data["message"].lower()


@pytest.mark.asyncio
async def test_get_me_authenticated(
    client: AsyncClient, sample_user: User, auth_headers: dict[str, str]
):
    """GET /api/v1/auth/me returns current user data when authenticated."""
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["id"] == sample_user.id
    assert data["data"]["email"] == sample_user.email
    assert data["data"]["name"] == sample_user.name
    assert data["data"]["profile"]["education"] == "MIT"


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    """GET /api/v1/auth/me returns 401 without Bearer token."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401

    data = response.json()
    assert data["status"] == "error"


@pytest.mark.asyncio
async def test_logout_endpoint(client: AsyncClient):
    """POST /api/v1/auth/logout acknowledges session logout."""
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


@pytest.mark.asyncio
async def test_forgot_and_reset_password_flow(client: AsyncClient, sample_user: User):
    """Full forgot-password and reset-password token cycle."""
    # 1. Request reset
    forgot_resp = await client.post(
        "/api/v1/auth/forgot-password", json={"email": sample_user.email}
    )
    assert forgot_resp.status_code == 200
    forgot_data = forgot_resp.json()
    token = forgot_data["data"]["reset_token"]
    assert token is not None

    # 2. Reset password using token
    new_password = "BrandNewPassword2026!"
    reset_resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": new_password},
    )
    assert reset_resp.status_code == 200

    # 3. Login with old password fails
    old_login = await client.post(
        "/api/v1/auth/login",
        json={"email": sample_user.email, "password": "Password123!"},
    )
    assert old_login.status_code == 401

    # 4. Login with new password succeeds
    new_login = await client.post(
        "/api/v1/auth/login",
        json={"email": sample_user.email, "password": new_password},
    )
    assert new_login.status_code == 200


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client: AsyncClient):
    """Resetting password with non-existent token returns 400 error."""
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": "completely-invalid-token", "new_password": "ValidPassword123!"},
    )
    assert response.status_code == 400
