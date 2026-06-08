import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.modules.auth.infrastructure.persistence.models import Base
from src.modules.core.database import engine
from src.modules.core.redis_client import get_redis_client
from datetime import datetime, timezone
import jwt
from src.modules.core.conf import Config
from src.modules.core.jwt_decoder import JWTDecoder


class TestAuthE2E:
    """End-to-end tests for complete authentication flow"""

    @pytest.fixture(autouse=True)
    async def setup_db(self):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    @pytest.fixture
    async def client(self):
        """HTTP client for testing"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    @pytest.fixture
    def user_data(self):
        return {
            "email": "e2e_test@example.com",
            "password": "StrongP@ssw0rd123",
        }

    @pytest.fixture
    def weak_password_data(self):
        return {
            "email": "weak@example.com",
            "password": "weak",
        }

    @pytest.fixture(autouse=True)
    async def reset_rate_limits(self):
        """Reset rate limit counters for testing"""
        redis = await get_redis_client()

        keys = await redis.keys(f"rl_*")
        for key in keys:
            await redis.delete(key)

    # ========== Test Auth Flow ==========
    async def test_complete_auth_flow(self, client, user_data):
        """
        Complete user journey:
        1. Register
        2. Login
        3. Change password
        4. Login with new password
        5. Logout
        """
        email = user_data["email"]
        password = user_data["password"]

        # ===== Register =====
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]

        # ===== Login with registered credentials =====
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]

        # ===== Change password =====
        new_password = "NewStrongP@ssw0rd456"
        response = await client.post(
            "/api/v1/auth/set-password",
            json={
                "access_token": access_token,
                "old_password": password,
                "new_password": new_password,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        new_access_token = data["access_token"]
        new_refresh_token = data["refresh_token"]

        # ===== Login with new password =====
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": new_password,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

        # ===== Logout =====
        response = await client.post(
            "/api/v1/auth/logout",
            json={
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
            },
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Logged out successfully"

    async def test_password_reset_flow(self, client, user_data):
        """
        Password reset journey:
        1. Register
        2. Request password reset (forget-password)
        3. Reset password with token
        4. Login with new password
        """
        email = user_data["email"]
        password = user_data["password"]
        new_password = "ResetP@ssw0rd789"

        # ===== Register =====
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
            },
        )
        assert response.status_code == 201
        access_token = response.json()["access_token"]

        # ===== Request password reset =====
        response = await client.post(
            "/api/v1/auth/forget-password",
            json={
                "access_token": access_token,
            },
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Password reset token sent to email"

        # Note: In real scenario, token would be sent via email
        # For testing, we need to get the token from Redis
        redis = await get_redis_client()

        # Find the reset token
        keys = await redis.keys("password_reset:*")
        assert len(keys) == 1
        reset_token = keys[0].split(":")[1]

        # ===== Reset password using token =====
        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "access_token": access_token,
                "token": reset_token,
                "new_password": new_password,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

        # ===== Login with new password =====
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": new_password,
            },
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    async def test_token_refresh_flow(self, client, user_data):
        """
        Token refresh journey:
        1. Register
        2. Refresh token before expiration
        3. Use new token for authenticated operation
        """
        email = user_data["email"]
        password = user_data["password"]

        # ===== Register =====
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
            },
        )
        assert response.status_code == 201
        refresh_token = response.json()["refresh_token"]

        # ===== Refresh token =====
        response = await client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": refresh_token,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        new_access_token = data["access_token"]

        # ===== Use new token for logout =====

        response = await client.post(
            "/api/v1/auth/logout",
            json={
                "access_token": new_access_token,
                "refresh_token": refresh_token,
            },
        )
        assert response.status_code == 200

    # ========== Error Cases ==========
    async def test_register_with_existing_email(self, client, user_data):
        """Register with already used email should fail"""
        # First registration
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": user_data["email"],
                "password": user_data["password"],
            },
        )
        assert response.status_code == 201

        # Second registration with same email
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": user_data["email"],
                "password": "DifferentP@ss123",
            },
        )
        assert response.status_code == 400

    async def test_login_with_wrong_password(self, client, user_data):
        """Login with wrong password should fail"""
        # Register first
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": user_data["email"],
                "password": user_data["password"],
            },
        )

        # Login with wrong password
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": user_data["email"],
                "password": "WrongPassword123!",
            },
        )
        assert response.status_code == 400

    async def test_register_with_weak_password(self, client, weak_password_data):
        """Register with weak password should fail"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": weak_password_data["email"],
                "password": weak_password_data["password"],
            },
        )
        assert response.status_code == 400

    async def test_logout_with_invalid_token(self, client):
        """Logout with invalid token should fail"""
        response = await client.post(
            "/api/v1/auth/logout",
            json={
                "access_token": "invalid_token_12345",
                "refresh_token": "invalid_token_67890",
            },
        )
        assert response.status_code == 401

    async def test_refresh_with_expired_token(self, client, user_data):
        """Refresh with expired token should fail"""
        # Register
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": user_data["email"],
                "password": user_data["password"],
            },
        )
        assert response.status_code == 201
        refresh_token = response.json()["refresh_token"]

        # create expired token
        decoder = JWTDecoder()
        payload = decoder.decode_token(refresh_token)
        exp = datetime.now(timezone.utc)
        payload = {
            "sub": payload["sub"],
            "jti": payload["jti"],
            "ver": payload["ver"],
            "exp": exp.timestamp(),
            "type": payload["type"],
            "iat": payload["iat"],
        }
        refresh_token = jwt.encode(
            payload, Config.JWT_PRIVATE_KEY, algorithm=Config.JWT_ALGORITHM
        )

        # Try to refresh
        response = await client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": refresh_token,
            },
        )
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]

    # ========== Concurrent Access ==========
    async def test_concurrent_login_same_user(self, client, user_data):
        """Multiple devices can login with same user"""
        # Register
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": user_data["email"],
                "password": user_data["password"],
            },
        )

        # Device 1 login
        response1 = await client.post(
            "/api/v1/auth/login",
            json={
                "email": user_data["email"],
                "password": user_data["password"],
            },
        )
        assert response1.status_code == 200

        # Device 2 login
        response2 = await client.post(
            "/api/v1/auth/login",
            json={
                "email": user_data["email"],
                "password": user_data["password"],
            },
        )
        assert response2.status_code == 200

        # Both should have different tokens
        assert response1.json()["access_token"] != response2.json()["access_token"]

    # ========== Change Password Invalidates Old Tokens ==========
    async def test_change_password_invalidates_old_tokens(self, client, user_data):
        """After password change, old tokens should not work"""
        email = user_data["email"]
        password = user_data["password"]
        new_password = "NewP@ssw0rd456"

        # Register and login
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
            },
        )
        old_access_token = response.json()["access_token"]

        # Change password
        response = await client.post(
            "/api/v1/auth/set-password",
            json={
                "access_token": old_access_token,
                "old_password": password,
                "new_password": new_password,
            },
        )
        assert response.status_code == 200
        new_access_token = response.json()["access_token"]

        # Try to use old token for logout (should fail)
        response = await client.post(
            "/api/v1/auth/logout",
            json={
                "access_token": old_access_token,
                "refresh_token": "dummy",
            },
        )
        assert response.status_code == 401

        # New token should work
        # Get current refresh token first
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": new_password,
            },
        )
        new_refresh_token = response.json()["refresh_token"]

        response = await client.post(
            "/api/v1/auth/logout",
            json={
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
            },
        )
        assert response.status_code == 200
