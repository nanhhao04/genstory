import pytest
from httpx import AsyncClient, ASGITransport
from src.backend.main import app

@pytest.mark.asyncio
async def test_read_root():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 307 # Redirect to /auth

@pytest.mark.asyncio
async def test_auth_page():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/auth")
    assert response.status_code == 200
    assert "GenStory" in response.text
