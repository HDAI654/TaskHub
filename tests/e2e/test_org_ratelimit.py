import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.modules.core.database import engine, Base
from src.modules.core.redis_client import get_redis_client
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.org.presentation.api.v1.create_org import (
    RATE_LIMIT_MAX_REQUESTS as CREATE_ORG_LIMIT,
)
from src.modules.org.presentation.api.v1.get_org import (
    RATE_LIMIT_MAX_REQUESTS as GET_ORG_LIMIT,
)
from src.modules.org.presentation.api.v1.update_org import (
    RATE_LIMIT_MAX_REQUESTS as UPDATE_ORG_LIMIT,
)
from src.modules.org.presentation.api.v1.delete_org import (
    RATE_LIMIT_MAX_REQUESTS as DELETE_ORG_LIMIT,
)
from src.modules.org.presentation.api.v1.add_member import (
    RATE_LIMIT_MAX_REQUESTS as ADD_MEMBER_LIMIT,
)
from src.modules.org.presentation.api.v1.remove_member import (
    RATE_LIMIT_MAX_REQUESTS as REMOVE_MEMBER_LIMIT,
)
from src.modules.org.presentation.api.v1.change_user_role import (
    RATE_LIMIT_MAX_REQUESTS as CHANGE_ROLE_LIMIT,
)
from src.modules.org.presentation.api.v1.get_user_orgs import (
    RATE_LIMIT_MAX_REQUESTS as GET_USER_ORGS_LIMIT,
)
from src.modules.org.presentation.api.v1.get_org_members import (
    RATE_LIMIT_MAX_REQUESTS as GET_ORG_MEMBERS_LIMIT,
)


class TestOrgRateLimit:
    @pytest.fixture(autouse=True)
    async def setup_db(self):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    @pytest.fixture(autouse=True)
    async def reset_rate_limits(self):
        redis = await get_redis_client()
        keys = await redis.keys("rl_*")
        for key in keys:
            await redis.delete(key)

    @pytest.fixture
    async def client(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    @pytest.fixture
    async def user_token(self, client):
        # Register a user and return access token
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "owner@ratelimit.com",
                "password": "StrongP@ssw0rd123",
            },
        )
        assert response.status_code == 201
        return response.json()["access_token"]

    @pytest.fixture
    async def second_user_token(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "member@ratelimit.com",
                "password": "StrongP@ssw0rd456",
            },
        )
        assert response.status_code == 201
        return response.json()["access_token"]

    @pytest.fixture
    async def org_id(self, client, user_token):
        response = await client.post(
            "/api/v1/orgs",
            json={
                "access_token": user_token,
                "name": "RateLimit Org",
            },
        )
        assert response.status_code == 201
        return response.json()["org_id"]

    async def test_rate_limiting_create_org(self, client, user_token):
        for i in range(CREATE_ORG_LIMIT):
            response = await client.post(
                "/api/v1/orgs",
                json={
                    "access_token": user_token,
                    "name": f"Org_{i}",
                },
            )
            assert response.status_code == 201

        response = await client.post(
            "/api/v1/orgs",
            json={
                "access_token": user_token,
                "name": "RateLimitedOrg",
            },
        )
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]

    async def test_rate_limiting_get_org(self, client, user_token, org_id):
        for i in range(GET_ORG_LIMIT):
            response = await client.post(
                "/api/v1/orgs/get",
                json={
                    "access_token": user_token,
                    "org_id": org_id,
                },
            )
            assert response.status_code == 200

        response = await client.post(
            "/api/v1/orgs/get",
            json={
                "access_token": user_token,
                "org_id": org_id,
            },
        )
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]

    async def test_rate_limiting_update_org(self, client, user_token, org_id):
        for i in range(UPDATE_ORG_LIMIT):
            response = await client.put(
                "/api/v1/orgs",
                json={
                    "access_token": user_token,
                    "org_id": org_id,
                    "new_name": f"UpdatedName_{i}",
                },
            )
            assert response.status_code == 200

        response = await client.put(
            "/api/v1/orgs",
            json={
                "access_token": user_token,
                "org_id": org_id,
                "new_name": "RateLimitedName",
            },
        )
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]

    async def test_rate_limiting_delete_org(self, client, user_token):
        for i in range(DELETE_ORG_LIMIT):
            response = await client.post(
                "/api/v1/orgs/delete",
                json={
                    "access_token": user_token,
                    "org_id": "FakeID",
                },
            )
            assert response.status_code != 429

        response = await client.post(
            "/api/v1/orgs/delete",
            json={
                "access_token": user_token,
                "org_id": "FakeID",
            },
        )
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]

    async def test_rate_limiting_add_member(
        self, client, user_token, second_user_token, org_id
    ):
        # Need user_id of second user
        from src.modules.core.jwt_decoder import JWTDecoder

        decoder = JWTDecoder()
        payload = decoder.decode_token(second_user_token)
        second_user_id = payload["sub"]

        for i in range(ADD_MEMBER_LIMIT):
            response = await client.post(
                "/api/v1/orgs/members",
                json={
                    "access_token": user_token,
                    "org_id": org_id,
                    "user_id": second_user_id,
                    "role": "member",
                },
            )
            assert response.status_code in (201, 409)

        # Next request should be rate limited
        response = await client.post(
            "/api/v1/orgs/members",
            json={
                "access_token": user_token,
                "org_id": org_id,
                "user_id": second_user_id,
                "role": "member",
            },
        )
        assert response.status_code == 429

    async def test_rate_limiting_remove_member(
        self, client, user_token, second_user_token, org_id
    ):
        decoder = JWTDecoder()
        payload = decoder.decode_token(second_user_token)
        second_user_id = payload["sub"]

        # Add member first (once)
        await client.post(
            "/api/v1/orgs/members",
            json={
                "access_token": user_token,
                "org_id": org_id,
                "user_id": second_user_id,
                "role": "member",
            },
        )

        for i in range(REMOVE_MEMBER_LIMIT):
            response = await client.post(
                "/api/v1/orgs/members/delete",
                json={
                    "access_token": user_token,
                    "org_id": org_id,
                    "user_id": second_user_id,
                },
            )
            # After first removal, subsequent will be 404, but no rate limit yet
            assert response.status_code in (200, 404)

        # Next request should be rate limited
        response = await client.post(
            "/api/v1/orgs/members/delete",
            json={
                "access_token": user_token,
                "org_id": org_id,
                "user_id": second_user_id,
            },
        )
        assert response.status_code == 429

    async def test_rate_limiting_change_user_role(
        self, client, user_token, second_user_token, org_id
    ):
        decoder = JWTDecoder()
        payload = decoder.decode_token(second_user_token)
        second_user_id = payload["sub"]

        # Add member first
        await client.post(
            "/api/v1/orgs/members",
            json={
                "access_token": user_token,
                "org_id": org_id,
                "user_id": second_user_id,
                "role": "member",
            },
        )

        for i in range(CHANGE_ROLE_LIMIT):
            response = await client.put(
                "/api/v1/orgs/members/role",
                json={
                    "access_token": user_token,
                    "org_id": org_id,
                    "user_id": second_user_id,
                    "new_role": "admin" if i % 2 == 0 else "member",
                },
            )
            assert response.status_code == 200

        response = await client.put(
            "/api/v1/orgs/members/role",
            json={
                "access_token": user_token,
                "org_id": org_id,
                "user_id": second_user_id,
                "new_role": "viewer",
            },
        )
        assert response.status_code == 429

    async def test_rate_limiting_get_user_orgs(self, client, user_token):
        for i in range(GET_USER_ORGS_LIMIT):
            response = await client.post(
                "/api/v1/users/orgs",
                json={
                    "access_token": user_token,
                },
            )
            assert response.status_code == 200

        response = await client.post(
            "/api/v1/users/orgs",
            json={
                "access_token": user_token,
            },
        )
        assert response.status_code == 429

    async def test_rate_limiting_get_org_members(self, client, user_token, org_id):
        for i in range(GET_ORG_MEMBERS_LIMIT):
            response = await client.post(
                "/api/v1/orgs/members/list",
                json={
                    "access_token": user_token,
                    "org_id": org_id,
                },
            )
            assert response.status_code == 200

        response = await client.post(
            "/api/v1/orgs/members/list",
            json={
                "access_token": user_token,
                "org_id": org_id,
            },
        )
        assert response.status_code == 429

    async def test_rate_limit_headers_are_returned(self, client, user_token):
        # Exhaust the limit for create_org
        for i in range(CREATE_ORG_LIMIT):
            response = await client.post(
                "/api/v1/orgs",
                json={
                    "access_token": user_token,
                    "name": f"HeaderTest_{i}",
                },
            )
            assert response.status_code == 201

        response = await client.post(
            "/api/v1/orgs",
            json={
                "access_token": user_token,
                "name": "HeaderLimited",
            },
        )
        assert response.status_code == 429
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        limit = int(response.headers["X-RateLimit-Limit"])
        assert limit == CREATE_ORG_LIMIT
