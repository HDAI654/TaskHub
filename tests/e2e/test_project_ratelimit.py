import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.modules.core.database import engine, Base
from src.modules.core.redis_client import get_redis_client
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.org.presentation.api.v1.create_project import (
    RATE_LIMIT_MAX_REQUESTS as CREATE_PROJECT_LIMIT,
)
from src.modules.org.presentation.api.v1.update_project import (
    RATE_LIMIT_MAX_REQUESTS as UPDATE_PROJECT_LIMIT,
)
from src.modules.org.presentation.api.v1.delete_project import (
    RATE_LIMIT_MAX_REQUESTS as DELETE_PROJECT_LIMIT,
)
from src.modules.org.presentation.api.v1.get_project import (
    RATE_LIMIT_MAX_REQUESTS as GET_PROJECT_LIMIT,
)
from src.modules.org.presentation.api.v1.get_org_projects import (
    RATE_LIMIT_MAX_REQUESTS as GET_ORG_PROJECTS_LIMIT,
)


class TestProjectMngRateLimit:
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
    async def org_id(self, client, user_token):
        response = await client.post(
            "/api/v1/mng/orgs",
            json={
                "access_token": user_token,
                "name": "Project RateLimit Org",
            },
        )
        assert response.status_code == 201
        return response.json()["org_id"]

    @pytest.fixture
    async def project_id(self, client, user_token, org_id):
        response = await client.post(
            f"/api/v1/mng/orgs/{org_id}/projects",
            json={
                "access_token": user_token,
                "name": "Test Project",
                "description": "Test desc",
            },
        )
        assert response.status_code == 201
        return response.json()["project_id"]

    async def test_rate_limiting_create_project(self, client, user_token, org_id):
        for i in range(CREATE_PROJECT_LIMIT):
            response = await client.post(
                f"/api/v1/mng/orgs/{org_id}/projects",
                json={
                    "access_token": user_token,
                    "name": f"Project_{i}",
                    "description": f"Desc_{i}",
                },
            )
            assert response.status_code == 201

        response = await client.post(
            f"/api/v1/mng/orgs/{org_id}/projects",
            json={
                "access_token": user_token,
                "name": "RateLimitedProject",
                "description": "Should be rate limited",
            },
        )
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]

    async def test_rate_limiting_update_project(self, client, user_token, project_id):
        for i in range(UPDATE_PROJECT_LIMIT):
            response = await client.put(
                f"/api/v1/mng/projects/{project_id}",
                json={
                    "access_token": user_token,
                    "new_name": f"UpdatedName_{i}",
                },
            )
            assert response.status_code == 200

        response = await client.put(
            f"/api/v1/mng/projects/{project_id}",
            json={
                "access_token": user_token,
                "new_name": "RateLimitedName",
            },
        )
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]

    async def test_rate_limiting_delete_project(self, client, user_token):
        # Need to create projects first
        response = await client.post(
            "/api/v1/mng/orgs",
            json={
                "access_token": user_token,
                "name": "Temp Org for Delete Test",
            },
        )
        assert response.status_code == 201
        temp_org_id = response.json()["org_id"]

        project_ids = []
        for i in range(DELETE_PROJECT_LIMIT + 1):
            resp = await client.post(
                f"/api/v1/mng/orgs/{temp_org_id}/projects",
                json={
                    "access_token": user_token,
                    "name": f"DelProject_{i}",
                    "description": f"Desc_{i}",
                },
            )
            assert resp.status_code == 201
            project_ids.append(resp.json()["project_id"])

        for i in range(DELETE_PROJECT_LIMIT):
            response = await client.delete(
                f"/api/v1/mng/projects/{project_ids[i]}",
                headers={"Authorization": f"Bearer {user_token}"},
            )
            assert response.status_code == 200

        response = await client.delete(
            f"/api/v1/mng/projects/{project_ids[DELETE_PROJECT_LIMIT]}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]

    async def test_rate_limiting_get_project(self, client, user_token, project_id):
        for i in range(GET_PROJECT_LIMIT):
            response = await client.get(
                f"/api/v1/mng/projects/{project_id}",
                headers={"Authorization": f"Bearer {user_token}"},
            )
            assert response.status_code == 200

        response = await client.get(
            f"/api/v1/mng/projects/{project_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]

    async def test_rate_limiting_get_org_projects(self, client, user_token, org_id):
        for i in range(GET_ORG_PROJECTS_LIMIT):
            response = await client.get(
                f"/api/v1/mng/orgs/{org_id}/projects",
                headers={"Authorization": f"Bearer {user_token}"},
            )
            assert response.status_code == 200

        response = await client.get(
            f"/api/v1/mng/orgs/{org_id}/projects",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]

    async def test_rate_limit_headers_are_returned_for_project(
        self, client, user_token, org_id
    ):
        for i in range(CREATE_PROJECT_LIMIT):
            response = await client.post(
                f"/api/v1/mng/orgs/{org_id}/projects",
                json={
                    "access_token": user_token,
                    "name": f"HeaderProject_{i}",
                    "description": "Test",
                },
            )
            assert response.status_code == 201

        response = await client.post(
            f"/api/v1/mng/orgs/{org_id}/projects",
            json={
                "access_token": user_token,
                "name": "HeaderLimited",
                "description": "Should be rate limited",
            },
        )
        assert response.status_code == 429
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        limit = int(response.headers["X-RateLimit-Limit"])
        assert limit == CREATE_PROJECT_LIMIT
