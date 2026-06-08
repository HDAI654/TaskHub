import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.modules.auth.infrastructure.persistence.models import Base
from src.modules.core.database import engine
from src.modules.core.redis_client import get_redis_client
from src.modules.auth.presentation.api.v1.signup import RATE_LIMIT_MAX_REQUESTS as SIGNUP_RATE_LIMIT_MAX_REQUESTS
from src.modules.auth.presentation.api.v1.login import RATE_LIMIT_MAX_REQUESTS as LOGIN_RATE_LIMIT_MAX_REQUESTS
from src.modules.auth.presentation.api.v1.forget_password import RATE_LIMIT_MAX_REQUESTS as FORGET_PASS_RATE_LIMIT_MAX_REQUESTS
from src.modules.auth.presentation.api.v1.set_password import RATE_LIMIT_MAX_REQUESTS as SET_PASS_RATE_LIMIT_MAX_REQUESTS
from src.modules.auth.presentation.api.v1.reset_password import RATE_LIMIT_MAX_REQUESTS as RESET_PASS_RATE_LIMIT_MAX_REQUESTS
from src.modules.auth.presentation.api.v1.refresh import RATE_LIMIT_MAX_REQUESTS as REFRESH_RATE_LIMIT_MAX_REQUESTS
from src.modules.auth.presentation.api.v1.logout import RATE_LIMIT_MAX_REQUESTS as LOGOUT_RATE_LIMIT_MAX_REQUESTS


class TestAuthRateLimit:
    @pytest.fixture(autouse=True)
    async def setup_db(self):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    @pytest.fixture(autouse=True)
    async def reset_rate_limits(self):
        """Reset rate limit counters for testing"""
        redis = await get_redis_client()

        keys = await redis.keys(f"rl_*")
        for key in keys:
            await redis.delete(key)

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

    # ========== Rate Limiting ==========
    async def test_rate_limiting_on_register(self, client, user_data):
        for i in range(SIGNUP_RATE_LIMIT_MAX_REQUESTS):
            response = await client.post("/api/v1/auth/register", json={
                "email": f"register_test_{i}@example.com",
                "password": user_data["password"],
            })
            assert response.status_code == 201

        # Next request should be rate limited
        response = await client.post("/api/v1/auth/register", json={
            "email": "register_rate_limited@example.com",
            "password": user_data["password"],
        })
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]

    async def test_rate_limiting_on_login(self, client, user_data):
        # First create a user
        await client.post("/api/v1/auth/register", json={
            "email": user_data["email"],
            "password": user_data["password"],
        })

        for i in range(LOGIN_RATE_LIMIT_MAX_REQUESTS):
            response = await client.post("/api/v1/auth/login", json={
                "email": user_data["email"],
                "password": user_data["password"],
            })
            assert response.status_code == 200

        # Next request should be rate limited
        response = await client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"],
        })
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]

    async def test_rate_limiting_on_forget_password(self, client, user_data):
        # Register first
        response = await client.post("/api/v1/auth/register", json={
            "email": user_data["email"],
            "password": user_data["password"],
        })
        access_token = response.json()["access_token"]

        for i in range(FORGET_PASS_RATE_LIMIT_MAX_REQUESTS):
            response = await client.post("/api/v1/auth/forget-password", json={
                "access_token": access_token,
            })
            assert response.status_code == 200

        # Next request should be rate limited
        response = await client.post("/api/v1/auth/forget-password", json={
            "access_token": access_token,
        })
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]

    async def test_rate_limiting_on_set_password(self, client, user_data):
        # Register first
        response = await client.post("/api/v1/auth/register", json={
            "email": user_data["email"],
            "password": user_data["password"],
        })
        access_token = response.json()["access_token"]
        current_password = user_data["password"]

        for i in range(SET_PASS_RATE_LIMIT_MAX_REQUESTS):
            response = await client.post("/api/v1/auth/set-password", json={
                "access_token": access_token,
                "old_password": current_password,
                "new_password": f"NewP@ss{i}123",
            })
            assert response.status_code == 200
            # Update access_token for next request
            access_token = response.json()["access_token"]
            current_password = f"NewP@ss{i}123" 

        # Next request should be rate limited
        response = await client.post("/api/v1/auth/set-password", json={
            "access_token": access_token,
            "old_password": current_password,
            "new_password": "FinalP@ss123",
        })
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]

    async def test_rate_limiting_on_reset_password(self, client, user_data):
        # Register first
        response = await client.post("/api/v1/auth/register", json={
            "email": user_data["email"],
            "password": user_data["password"],
        })
        access_token = response.json()["access_token"]

        # Try reset password with different tokens
        for i in range(RESET_PASS_RATE_LIMIT_MAX_REQUESTS):
            response = await client.post("/api/v1/auth/reset-password", json={
                "access_token": access_token,
                "token": "FakeToken",
                "new_password": f"ResetP@ss{i}123",
            })
            assert response.status_code != 429

        # Next request should be rate limited
        response = await client.post("/api/v1/auth/reset-password", json={
            "access_token": access_token,
            "token": "FakeToken",
            "new_password": "TooManyP@ss123",
        })
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]

    async def test_rate_limiting_on_refresh(self, client, user_data):
        # Register first
        response = await client.post("/api/v1/auth/register", json={
            "email": user_data["email"],
            "password": user_data["password"],
        })
        refresh_token = response.json()["refresh_token"]

        for i in range(REFRESH_RATE_LIMIT_MAX_REQUESTS):
            response = await client.post("/api/v1/auth/refresh", json={
                "refresh_token": refresh_token,
            })
            assert response.status_code == 200

        # Next request should be rate limited
        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]

    async def test_rate_limiting_on_logout(self, client, user_data):
        # Register first
        response = await client.post("/api/v1/auth/register", json={
            "email": user_data["email"],
            "password": user_data["password"],
        })
        access_token = response.json()["access_token"]
        refresh_token = response.json()["refresh_token"]

        for i in range(LOGOUT_RATE_LIMIT_MAX_REQUESTS):            
            response = await client.post("/api/v1/auth/logout", json={
                "access_token": access_token,
                "refresh_token": refresh_token,
            })
            assert response.status_code != 429

        # Next request should be rate limited
        response = await client.post("/api/v1/auth/logout", json={
            "access_token": access_token,
            "refresh_token": refresh_token,
        })
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]
    
    
    # ========== Test Headers ==========
    async def test_rate_limit_headers_are_returned(self, client, user_data):
        """Verify rate limit headers are present in response"""
        for i in range(SIGNUP_RATE_LIMIT_MAX_REQUESTS+1):
            response = await client.post("/api/v1/auth/register", json={
                "email": f"register_test_{i}@example.com",
                "password": user_data["password"],
            })
        
        assert response.status_code == 429
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        
        # Verify header values
        limit = int(response.headers["X-RateLimit-Limit"])
        
        assert limit == SIGNUP_RATE_LIMIT_MAX_REQUESTS

    # ========== Test Independent RateLimit ==========
    async def test_rate_limits_are_independent_per_endpoint(self, client, user_data):
        """Each endpoint should have its own rate limit counter"""
        # Register first
        response = await client.post("/api/v1/auth/register", json={
            "email": user_data["email"],
            "password": user_data["password"],
        })
        access_token = response.json()["access_token"]
        refresh_token = response.json()["refresh_token"]

        # Make login requests
        for i in range(LOGIN_RATE_LIMIT_MAX_REQUESTS):
            response = await client.post("/api/v1/auth/login", json={
                "email": user_data["email"],
                "password": user_data["password"],
            })
            assert response.status_code == 200
        
        # Register should still work (independent counter)
        response = await client.post("/api/v1/auth/register", json={
            "email": "independent_test@example.com",
            "password": user_data["password"],
        })
        assert response.status_code == 201
        
        # Login should be exhausted
        response = await client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"],
        })
        assert response.status_code == 429