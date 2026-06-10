import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.modules.core.database import engine, Base
from src.modules.core.redis_client import get_redis_client
from src.modules.core.jwt_decoder import JWTDecoder


class TestProjectMngE2E:
    """End-to-end tests for project management (with /mng prefix)"""

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

    async def test_complete_project_lifecycle(
        self, client, owner_data, admin_data, member_data
    ):
        """
        Complete project lifecycle:
        1. Register users (owner, admin, member)
        2. Create organization
        3. Add admin and member to organization
        4. Create project (by owner)
        5. Get project by ID
        6. Get organization projects
        7. Update project (by admin)
        8. Delete project (by admin)
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
                "name": "Project Test Org",
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
                "description": "Initial description",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "project_id" in data
        project_id = data["project_id"]
        assert data["name"] == "Test Project"

        # ===== Get project by ID =====
        response = await client.get(
            f"/api/v1/mng/projects/{project_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project_id
        assert data["org_id"] == org_id
        assert data["name"] == "Test Project"
        assert data["description"] == "Initial description"

        # ===== Get organization projects =====
        response = await client.get(
            f"/api/v1/mng/orgs/{org_id}/projects",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["projects"]) == 1
        assert data["projects"][0]["project_id"] == project_id

        # ===== Update project (by admin) =====
        response = await client.put(
            f"/api/v1/mng/projects/{project_id}",
            json={
                "access_token": admin_token,
                "new_name": "Updated Project",
                "new_description": "Updated description",
            },
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Project updated successfully"

        # Verify update
        response = await client.get(
            f"/api/v1/mng/projects/{project_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        data = response.json()
        assert data["name"] == "Updated Project"
        assert data["description"] == "Updated description"

        # ===== Delete project (by admin) =====
        response = await client.delete(
            f"/api/v1/mng/projects/{project_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Project deleted successfully"

        # Verify project deleted
        response = await client.get(
            f"/api/v1/mng/projects/{project_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert response.status_code == 404

    async def test_project_permissions(self, client, owner_data, member_data):
        """
        Test permission checks for projects:
        - Only owner/admin can create/update/delete projects
        - Member cannot create/update/delete projects
        - Member can view projects (if member of organization)
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

        # Member tries to create project (should fail)
        response = await client.post(
            f"/api/v1/mng/orgs/{org_id}/projects",
            json={
                "access_token": member_token,
                "name": "Member Project",
                "description": "Should fail",
            },
        )
        assert response.status_code == 403

        # Create project as owner first
        response = await client.post(
            f"/api/v1/mng/orgs/{org_id}/projects",
            json={
                "access_token": owner_token,
                "name": "Owner Project",
                "description": "Owner desc",
            },
        )
        assert response.status_code == 201
        project_id = response.json()["project_id"]

        # Member tries to update project (should fail)
        response = await client.put(
            f"/api/v1/mng/projects/{project_id}",
            json={
                "access_token": member_token,
                "new_name": "Hacked",
            },
        )
        assert response.status_code == 403

        # Member tries to delete project (should fail)
        response = await client.delete(
            f"/api/v1/mng/projects/{project_id}",
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert response.status_code == 403

        # Member can view project (as member of organization)
        response = await client.get(
            f"/api/v1/mng/projects/{project_id}",
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert response.status_code == 200

        # Non-member cannot view project
        # Register a new user who is not a member
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
            f"/api/v1/mng/projects/{project_id}",
            headers={"Authorization": f"Bearer {outsider_token}"},
        )
        assert response.status_code == 403

        # Cleanup: delete project and org
        await client.delete(
            f"/api/v1/mng/projects/{project_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        await client.delete(
            f"/api/v1/mng/orgs/{org_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )

    async def test_create_project_duplicate_name(self, client, owner_data):
        """Creating project with same name in same org should be allowed (no unique constraint)"""
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
            "/api/v1/mng/orgs",
            json={
                "access_token": owner_token,
                "name": "Duplicate Test Org",
            },
        )
        org_id = response.json()["org_id"]

        response = await client.post(
            f"/api/v1/mng/orgs/{org_id}/projects",
            json={
                "access_token": owner_token,
                "name": "Same Name",
                "description": "First project",
            },
        )
        assert response.status_code == 201
        project1_id = response.json()["project_id"]

        response = await client.post(
            f"/api/v1/mng/orgs/{org_id}/projects",
            json={
                "access_token": owner_token,
                "name": "Same Name",
                "description": "Second project",
            },
        )
        assert response.status_code == 201
        project2_id = response.json()["project_id"]

        assert project1_id != project2_id

        # Cleanup
        await client.delete(
            f"/api/v1/mng/projects/{project1_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        await client.delete(
            f"/api/v1/mng/projects/{project2_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        await client.delete(
            f"/api/v1/mng/orgs/{org_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )

    async def test_get_nonexistent_project(self, client, owner_data):
        """Getting a non-existent project should return 404"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": owner_data["email"],
                "password": owner_data["password"],
            },
        )
        token = response.json()["access_token"]

        response = await client.get(
            "/api/v1/mng/projects/non-existent-id",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    async def _get_user_id_from_token(self, token: str) -> str:
        decoder = JWTDecoder()
        payload = decoder.decode_token(token)
        return payload["sub"]
