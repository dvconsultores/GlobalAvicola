"""Pytest configuration and shared fixtures."""
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTPX async client for testing the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def auth_headers(client: AsyncClient) -> dict:
    """Login as admin and return authorization headers."""
    resp = await client.post("/api/v1/login", json={
        "username": "admin",
        "password": "admin123",
    })
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    data = resp.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


