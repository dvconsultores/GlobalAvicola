"""Tests for Auth module — login, token, user CRUD."""
import pytest


@pytest.mark.asyncio
async def test_login_success(client):
    """Admin login should return access + refresh tokens."""
    resp = await client.post("/api/v1/login", json={
        "username": "admin",
        "password": "admin123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(client):
    """Wrong password should return 401."""
    resp = await client.post("/api/v1/login", json={
        "username": "admin",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_invalid_user(client):
    """Nonexistent user should return 401."""
    resp = await client.post("/api/v1/login", json={
        "username": "nonexistent",
        "password": "admin123",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me(auth_headers, client):
    """Authenticated user should get their profile."""
    resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "admin"
    assert data["is_super_admin"] == True


@pytest.mark.asyncio
async def test_health_check(client):
    """Health endpoint should return ok."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_list_roles(auth_headers, client):
    """List roles should return all active roles."""
    resp = await client.get("/api/v1/roles", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 5  # At least 5 roles seeded


@pytest.mark.asyncio
async def test_list_users(auth_headers, client):
    """List users should return seeded users."""
    resp = await client.get("/api/v1/users", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1  # At least admin user
