import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.modules.core.database import engine, Base
from src.modules.core.redis_client import get_redis_client
from src.modules.core.jwt_decoder import JWTDecoder


class TestColumnMngE2E:
    @pytest.fixture(autouse=True)
    async def setup_db(self):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    @pytest.fixture
    async def client(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    @pytest.fixture
    def owner_data(self):
        return {
            "email": "owner@example.com",
            "password": "StrongP@ssw0rd123",
        }

    @pytest.fixture
    def admin_data(self):
        return {
            "email": "admin@example.com",
            "password": "StrongP@ssw0rd456",
        }

    @pytest.fixture
    def member_data(self):
        return {
            "email": "member@example.com",
            "password": "StrongP@ssw0rd789",
        }

    @pytest.fixture(autouse=True)
    async def reset_rate_limits(self):
        redis = await get_redis_client()
        keys = await redis.keys("rl_*")
        for key in keys:
            await redis.delete(key)

    async def test_complete_column_lifecycle(
        self, client, owner_data, admin_data, member_data
    ):
        """
        Complete column lifecycle:
        1. Register users (owner, admin, member)
        2. Create organization
        3. Add admin and member to organization
        4. Create project (by owner)
        5. Create board (by owner)
        6. Create column (by owner)
        7. Get column by ID
        8. Get board columns
        9. Update column (by admin)
        10. Delete column (by admin)
        """
        # ===== Register users =====
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": owner_data["email"],
                "password": owner_data["password"],
            },
        )
        assert response.status_code == 201
        owner_token = response.json()["access_token"]
        owner_id = await self._get_user_id_from_token(owner_token)

        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": admin_data["email"],
                "password": admin_data["password"],
            },
        )
        assert response.status_code == 201
        admin_token = response.json()["access_token"]
        admin_id = await self._get_user_id_from_token(admin_token)

        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": member_data["email"],
                "password": member_data["password"],
            },
        )
        assert response.status_code == 201
        member_token = response.json()["access_token"]
        member_id = await self._get_user_id_from_token(member_token)

        # ===== Create organization =====
        response = await client.post(
            "/api/v1/mng/orgs",
            json={
                "access_token": owner_token,
                "name": "Column Test Org",
            },
        )
        assert response.status_code == 201
        org_id = response.json()["org_id"]

        # ===== Add admin and member to organization =====
        response = await client.post(
            f"/api/v1/mng/orgs/{org_id}/members",
            json={
                "access_token": owner_token,
                "user_id": admin_id,
                "role": "admin",
            },
        )
        assert response.status_code == 201

        response = await client.post(
            f"/api/v1/mng/orgs/{org_id}/members",
            json={
                "access_token": owner_token,
                "user_id": member_id,
                "role": "member",
            },
        )
        assert response.status_code == 201

        # ===== Create project (by owner) =====
        response = await client.post(
            f"/api/v1/mng/orgs/{org_id}/projects",
            json={
                "access_token": owner_token,
                "name": "Test Project",
                "description": "Project for columns",
            },
        )
        assert response.status_code == 201
        project_id = response.json()["project_id"]

        # ===== Create board (by owner) =====
        response = await client.post(
            f"/api/v1/mng/projects/{project_id}/boards",
            json={
                "access_token": owner_token,
                "name": "Test Board",
                "description": "Board description",
            },
        )
        assert response.status_code == 201
        board_id = response.json()["board_id"]

        # ===== Create column (by owner) =====
        response = await client.post(
            f"/api/v1/mng/boards/{board_id}/columns",
            json={
                "access_token": owner_token,
                "name": "Test Column",
                "order": 1,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "column_id" in data
        column_id = data["column_id"]
        assert data["name"] == "Test Column"
        assert data["order"] == 1

        # ===== Get column by ID =====
        response = await client.get(
            f"/api/v1/mng/columns/{column_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["column_id"] == column_id
        assert data["board_id"] == board_id
        assert data["name"] == "Test Column"
        assert data["order"] == 1

        # ===== Get board columns =====
        response = await client.get(
            f"/api/v1/mng/boards/{board_id}/columns",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["columns"]) == 1
        assert data["columns"][0]["column_id"] == column_id

        # ===== Update column (by admin) =====
        response = await client.put(
            f"/api/v1/mng/columns/{column_id}",
            json={
                "access_token": admin_token,
                "new_name": "Updated Column",
                "new_order": 2,
            },
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Column updated successfully"

        # Verify update
        response = await client.get(
            f"/api/v1/mng/columns/{column_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        data = response.json()
        assert data["name"] == "Updated Column"
        assert data["order"] == 2

        # ===== Delete column (by admin) =====
        response = await client.delete(
            f"/api/v1/mng/columns/{column_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Column deleted successfully"

        # Verify column deleted
        response = await client.get(
            f"/api/v1/mng/columns/{column_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert response.status_code == 404

    async def test_column_permissions(self, client, owner_data, member_data):
        """
        Test permission checks for columns:
        - Only owner/admin can create/update/delete columns
        - Member cannot create/update/delete columns
        - Member can view columns (if member of organization)
        """
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": owner_data["email"],
                "password": owner_data["password"],
            },
        )
        owner_token = response.json()["access_token"]
        owner_id = await self._get_user_id_from_token(owner_token)

        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": member_data["email"],
                "password": member_data["password"],
            },
        )
        member_token = response.json()["access_token"]
        member_id = await self._get_user_id_from_token(member_token)

        response = await client.post(
            "/api/v1/mng/orgs",
            json={
                "access_token": owner_token,
                "name": "Permission Test Org",
            },
        )
        org_id = response.json()["org_id"]

        # Add member as member (not admin/owner)
        response = await client.post(
            f"/api/v1/mng/orgs/{org_id}/members",
            json={
                "access_token": owner_token,
                "user_id": member_id,
                "role": "member",
            },
        )
        assert response.status_code == 201

        # Create project as owner
        response = await client.post(
            f"/api/v1/mng/orgs/{org_id}/projects",
            json={
                "access_token": owner_token,
                "name": "Project for permissions",
                "description": "desc",
            },
        )
        assert response.status_code == 201
        project_id = response.json()["project_id"]

        # Create board as owner
        response = await client.post(
            f"/api/v1/mng/projects/{project_id}/boards",
            json={
                "access_token": owner_token,
                "name": "Test Board",
                "description": "desc",
            },
        )
        assert response.status_code == 201
        board_id = response.json()["board_id"]

        # Member tries to create column (should fail)
        response = await client.post(
            f"/api/v1/mng/boards/{board_id}/columns",
            json={
                "access_token": member_token,
                "name": "Member Column",
                "order": 1,
            },
        )
        assert response.status_code == 403

        # Create column as owner first
        response = await client.post(
            f"/api/v1/mng/boards/{board_id}/columns",
            json={
                "access_token": owner_token,
                "name": "Owner Column",
                "order": 1,
            },
        )
        assert response.status_code == 201
        column_id = response.json()["column_id"]

        # Member tries to update column (should fail)
        response = await client.put(
            f"/api/v1/mng/columns/{column_id}",
            json={
                "access_token": member_token,
                "new_name": "Hacked",
            },
        )
        assert response.status_code == 403

        # Member tries to delete column (should fail)
        response = await client.delete(
            f"/api/v1/mng/columns/{column_id}",
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert response.status_code == 403

        # Member can view column (as member of organization)
        response = await client.get(
            f"/api/v1/mng/columns/{column_id}",
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert response.status_code == 200

        # Non-member cannot view column
        outsider_data = {
            "email": "outsider@example.com",
            "password": "StrongP@ssw0rd999",
        }
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": outsider_data["email"],
                "password": outsider_data["password"],
            },
        )
        outsider_token = response.json()["access_token"]

        response = await client.get(
            f"/api/v1/mng/columns/{column_id}",
            headers={"Authorization": f"Bearer {outsider_token}"},
        )
        assert response.status_code == 403

    async def test_get_nonexistent_column(self, client, owner_data):
        """Getting a non-existent column should return 404"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": owner_data["email"],
                "password": owner_data["password"],
            },
        )
        token = response.json()["access_token"]

        response = await client.get(
            "/api/v1/mng/columns/non-existent-id",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    async def _get_user_id_from_token(self, token: str) -> str:
        decoder = JWTDecoder()
        payload = decoder.decode_token(token)
        return payload["sub"]
