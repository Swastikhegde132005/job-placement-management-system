import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_register_and_login_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        random_suffix = uuid.uuid4().hex[:6]
        test_email = f"student_{random_suffix}@example.com"
        test_password = "Password123!"

        # 1. Register student
        student_payload = {
            "email": test_email,
            "password": test_password,
            "role": "student"
        }
        reg_res = await ac.post("/auth/register", json=student_payload)
        assert reg_res.status_code == 201
        reg_data = reg_res.json()
        assert "access_token" in reg_data
        assert reg_data["role"] == "student"

        # 2. Login
        login_res = await ac.post(
            "/auth/login",
            data={"username": test_email, "password": test_password}
        )
        assert login_res.status_code == 200
        login_data = login_res.json()
        assert "access_token" in login_data
        assert login_data["role"] == "student"

@pytest.mark.asyncio
async def test_unauthorized_access():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/students/me")
        assert response.status_code == 401
