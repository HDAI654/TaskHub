import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.modules.core.database import engine, Base
from src.modules.core.redis_client import get_redis_client
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.org.presentation.api.v1.create_column import (
    RATE_LIMIT_MAX_REQUESTS as CREATE_COLUMN_LIMIT,
)
from src.modules.org.presentation.api.v1.update_column import (
    RATE_LIMIT_MAX_REQUESTS as UPDATE_COLUMN_LIMIT,
)
from src.modules.org.presentation.api.v1.delete_column import (
    RATE_LIMIT_MAX_REQUESTS as DELETE_COLUMN_LIMIT,
)
from src.modules.org.presentation.api.v1.get_column import (
    RATE_LIMIT_MAX_REQUESTS as GET_COLUMN_LIMIT,
)
from src.modules.org.presentation.api.v1.get_board_columns import (
    RATE_LIMIT_MAX_REQUESTS as GET_BOARD_COLUMNS_LIMIT,
)


class TestColumnMngRateLimit:
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
                "name": "Column RateLimit Org",
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

    @pytest.fixture
    async def board_id(self, client, user_token, project_id):
        response = await client.post(
            f"/api/v1/mng/projects/{project_id}/boards",
            json={
                "access_token": user_token,
                "name": "Test Board",
                "description": "Test desc",
            },
        )
        assert response.status_code == 201
        return response.json()["board_id"]

    @pytest.fixture
    async def column_id(self, client, user_token, board_id):
        response = await client.post(
            f"/api/v1/mng/boards/{board_id}/columns",
            json={
                "access_token": user_token,
                "name": "Test Column",
                "order": 1,
            },
        )
        assert response.status_code == 201
        return response.json()["column_id"]

    async def test_rate_limiting_create_column(self, client, user_token, board_id):
        for i in range(CREATE_COLUMN_LIMIT):
            response = await client.post(
                f"/api/v1/mng/boards/{board_id}/columns",
                json={
                    "access_token": user_token,
                    "name": f"Column_{i}",
                    "order": i,
                },
            )
            assert response.status_code == 201

        response = await client.post(
            f"/api/v1/mng/boards/{board_id}/columns",
            json={
                "access_token": user_token,
                "name": "RateLimitedColumn",
                "order": 999,
            },
        )
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]

    async def test_rate_limiting_update_column(self, client, user_token, column_id):
        for i in range(UPDATE_COLUMN_LIMIT):
            response = await client.put(
                f"/api/v1/mng/columns/{column_id}",
                json={
                    "access_token": user_token,
                    "new_name": f"UpdatedName_{i}",
                },
            )
            assert response.status_code == 200

        response = await client.put(
            f"/api/v1/mng/columns/{column_id}",
            json={
                "access_token": user_token,
                "new_name": "RateLimitedName",
            },
        )
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]

    async def test_rate_limiting_delete_column(self, client, user_token, board_id):
        # Need to create columns first
        column_ids = []
        for i in range(DELETE_COLUMN_LIMIT + 1):
            resp = await client.post(
                f"/api/v1/mng/boards/{board_id}/columns",
                json={
                    "access_token": user_token,
                    "name": f"DelColumn_{i}",
                    "order": i,
                },
            )
            assert resp.status_code == 201
            column_ids.append(resp.json()["column_id"])

        for i in range(DELETE_COLUMN_LIMIT):
            response = await client.delete(
                f"/api/v1/mng/columns/{column_ids[i]}",
                headers={"Authorization": f"Bearer {user_token}"},
            )
            assert response.status_code == 200

        response = await client.delete(
            f"/api/v1/mng/columns/{column_ids[DELETE_COLUMN_LIMIT]}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]

    async def test_rate_limiting_get_column(self, client, user_token, column_id):
        for i in range(GET_COLUMN_LIMIT):
            response = await client.get(
                f"/api/v1/mng/columns/{column_id}",
                headers={"Authorization": f"Bearer {user_token}"},
            )
            assert response.status_code == 200

        response = await client.get(
            f"/api/v1/mng/columns/{column_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]

    async def test_rate_limiting_get_board_columns(self, client, user_token, board_id):
        for i in range(GET_BOARD_COLUMNS_LIMIT):
            response = await client.get(
                f"/api/v1/mng/boards/{board_id}/columns",
                headers={"Authorization": f"Bearer {user_token}"},
            )
            assert response.status_code == 200

        response = await client.get(
            f"/api/v1/mng/boards/{board_id}/columns",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]

    async def test_rate_limit_headers_are_returned_for_column(
        self, client, user_token, board_id
    ):
        for i in range(CREATE_COLUMN_LIMIT):
            response = await client.post(
                f"/api/v1/mng/boards/{board_id}/columns",
                json={
                    "access_token": user_token,
                    "name": f"HeaderColumn_{i}",
                    "order": i,
                },
            )
            assert response.status_code == 201

        response = await client.post(
            f"/api/v1/mng/boards/{board_id}/columns",
            json={
                "access_token": user_token,
                "name": "HeaderLimited",
                "order": 999,
            },
        )
        assert response.status_code == 429
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        limit = int(response.headers["X-RateLimit-Limit"])
        assert limit == CREATE_COLUMN_LIMIT
