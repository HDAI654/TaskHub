import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.modules.core.database import engine, Base
from src.modules.core.redis_client import get_redis_client
from src.modules.core.jwt_decoder import JWTDecoder


class TestBoardMngE2E:
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

    async def test_complete_board_lifecycle(
        self, client, owner_data, admin_data, member_data
    ):
        """
        Complete board lifecycle:
        1. Register users (owner, admin, member)
        2. Create organization
        3. Add admin and member to organization
        4. Create project (by owner)
        5. Create board (by owner)
        6. Get board by ID
        7. Get project boards
        8. Update board (by admin)
        9. Delete board (by admin)
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
                "name": "Board Test Org",
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
                "description": "Project for boards",
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
                "description": "Initial description",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "board_id" in data
        board_id = data["board_id"]
        assert data["name"] == "Test Board"

        # ===== Get board by ID =====
        response = await client.get(
            f"/api/v1/mng/boards/{board_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["board_id"] == board_id
        assert data["project_id"] == project_id
        assert data["name"] == "Test Board"
        assert data["description"] == "Initial description"

        # ===== Get project boards =====
        response = await client.get(
            f"/api/v1/mng/projects/{project_id}/boards",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["boards"]) == 1
        assert data["boards"][0]["board_id"] == board_id

        # ===== Update board (by admin) =====
        response = await client.put(
            f"/api/v1/mng/boards/{board_id}",
            json={
                "access_token": admin_token,
                "new_name": "Updated Board",
                "new_description": "Updated description",
            },
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Board updated successfully"

        # Verify update
        response = await client.get(
            f"/api/v1/mng/boards/{board_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        data = response.json()
        assert data["name"] == "Updated Board"
        assert data["description"] == "Updated description"

        # ===== Delete board (by admin) =====
        response = await client.delete(
            f"/api/v1/mng/boards/{board_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Board deleted successfully"

        # Verify board deleted
        response = await client.get(
            f"/api/v1/mng/boards/{board_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert response.status_code == 404

    async def test_board_permissions(self, client, owner_data, member_data):
        """
        Test permission checks for boards:
        - Only owner/admin can create/update/delete boards
        - Member cannot create/update/delete boards
        - Member can view boards (if member of organization)
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

        # Member tries to create board (should fail)
        response = await client.post(
            f"/api/v1/mng/projects/{project_id}/boards",
            json={
                "access_token": member_token,
                "name": "Member Board",
                "description": "Should fail",
            },
        )
        assert response.status_code == 403

        # Create board as owner first
        response = await client.post(
            f"/api/v1/mng/projects/{project_id}/boards",
            json={
                "access_token": owner_token,
                "name": "Owner Board",
                "description": "desc",
            },
        )
        assert response.status_code == 201
        board_id = response.json()["board_id"]

        # Member tries to update board (should fail)
        response = await client.put(
            f"/api/v1/mng/boards/{board_id}",
            json={
                "access_token": member_token,
                "new_name": "Hacked",
            },
        )
        assert response.status_code == 403

        # Member tries to delete board (should fail)
        response = await client.delete(
            f"/api/v1/mng/boards/{board_id}",
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert response.status_code == 403

        # Member can view board (as member of organization)
        response = await client.get(
            f"/api/v1/mng/boards/{board_id}",
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert response.status_code == 200

        # Non-member cannot view board
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
            f"/api/v1/mng/boards/{board_id}",
            headers={"Authorization": f"Bearer {outsider_token}"},
        )
        assert response.status_code == 403

    async def test_get_nonexistent_board(self, client, owner_data):
        """Getting a non-existent board should return 404"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": owner_data["email"],
                "password": owner_data["password"],
            },
        )
        token = response.json()["access_token"]

        response = await client.get(
            "/api/v1/mng/boards/non-existent-id",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    async def _get_user_id_from_token(self, token: str) -> str:
        decoder = JWTDecoder()
        payload = decoder.decode_token(token)
        return payload["sub"]
