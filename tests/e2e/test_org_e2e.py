import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.modules.core.database import engine, Base
from src.modules.core.redis_client import get_redis_client
from src.modules.org.domain.value_objects.id import ID
from src.modules.core.jwt_decoder import JWTDecoder


class TestOrgE2E:
    """End-to-end tests for organization management"""

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
    def user_data(self):
        return {
            "email": "owner@example.com",
            "password": "StrongP@ssw0rd123",
        }

    @pytest.fixture
    def second_user_data(self):
        return {
            "email": "member@example.com",
            "password": "StrongP@ssw0rd456",
        }

    @pytest.fixture(autouse=True)
    async def reset_rate_limits(self):
        redis = await get_redis_client()
        keys = await redis.keys("rl_*")
        for key in keys:
            await redis.delete(key)

    async def test_complete_org_lifecycle(self, client, user_data, second_user_data):
        """
        Complete organization lifecycle:
        1. Register owner and member users
        2. Create organization
        3. Add member to organization
        4. Get organization details
        5. Get user's organizations
        6. Get organization members
        7. Change member role
        8. Update organization name
        9. Remove member
        10. Delete organization
        """
        # ===== Register users =====
        # Owner registration
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": user_data["email"],
                "password": user_data["password"],
            },
        )
        assert response.status_code == 201
        owner_token = response.json()["access_token"]

        # Member registration
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": second_user_data["email"],
                "password": second_user_data["password"],
            },
        )
        assert response.status_code == 201
        member_token = response.json()["access_token"]
        member_user_id = await self._get_user_id_from_token(member_token)

        # ===== Create organization =====
        response = await client.post(
            "/api/v1/orgs",
            json={
                "access_token": owner_token,
                "name": "Test Org",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "org_id" in data
        org_id = data["org_id"]

        # ===== Add member to organization =====
        response = await client.post(
            "/api/v1/orgs/members",
            json={
                "access_token": owner_token,
                "org_id": org_id,
                "user_id": member_user_id,
                "role": "member",
            },
        )
        assert response.status_code == 201
        assert response.json()["message"] == "Member added successfully"

        # ===== Get organization details =====
        response = await client.post(
            "/api/v1/orgs/get",
            json={
                "access_token": owner_token,
                "org_id": org_id,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["org_id"] == org_id
        assert data["name"] == "Test Org"

        # ===== Get user's organizations =====
        response = await client.post(
            "/api/v1/users/orgs",
            json={
                "access_token": owner_token,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["orgs"]) == 1
        assert data["orgs"][0]["organization_id"] == org_id
        assert data["orgs"][0]["name"] == "Test Org"
        assert data["orgs"][0]["role"] == "owner"

        # ===== Get organization members =====
        response = await client.post(
            "/api/v1/orgs/members/list",
            json={
                "access_token": owner_token,
                "org_id": org_id,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["members"]) == 2  # owner + member
        roles = {m["user_id"]: m["role"] for m in data["members"]}
        assert roles[await self._get_user_id_from_token(owner_token)] == "owner"
        assert roles[member_user_id] == "member"

        # ===== Change member role =====
        response = await client.put(
            "/api/v1/orgs/members/role",
            json={
                "access_token": owner_token,
                "org_id": org_id,
                "user_id": member_user_id,
                "new_role": "admin",
            },
        )
        assert response.status_code == 200
        assert response.json()["message"] == "User role changed successfully"

        # Verify role changed
        response = await client.post(
            "/api/v1/orgs/members/list",
            json={
                "access_token": owner_token,
                "org_id": org_id,
            },
        )
        data = response.json()
        for m in data["members"]:
            if m["user_id"] == member_user_id:
                assert m["role"] == "admin"

        # ===== Update organization name =====
        response = await client.put(
            "/api/v1/orgs",
            json={
                "access_token": owner_token,
                "org_id": org_id,
                "new_name": "Updated Org Name",
            },
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Organization updated successfully"

        # Verify name updated
        response = await client.post(
            "/api/v1/orgs/get",
            json={
                "access_token": owner_token,
                "org_id": org_id,
            },
        )
        assert response.json()["name"] == "Updated Org Name"

        # ===== Remove member =====
        response = await client.post(
            "/api/v1/orgs/members/delete",
            json={
                "access_token": owner_token,
                "org_id": org_id,
                "user_id": member_user_id,
            },
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Member removed successfully"

        # Verify member removed
        response = await client.post(
            "/api/v1/orgs/members/list",
            json={
                "access_token": owner_token,
                "org_id": org_id,
            },
        )
        data = response.json()
        assert len(data["members"]) == 1
        assert data["members"][0]["user_id"] == await self._get_user_id_from_token(
            owner_token
        )

        # ===== Delete organization =====
        response = await client.post(
            "/api/v1/orgs/delete",
            json={
                "access_token": owner_token,
                "org_id": org_id,
            },
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Organization deleted successfully"

        # Verify organization no longer accessible
        response = await client.post(
            "/api/v1/orgs/get",
            json={
                "access_token": owner_token,
                "org_id": org_id,
            },
        )
        assert response.status_code == 404

    async def test_org_permissions(self, client, user_data, second_user_data):
        """
        Test permission checks:
        - Only owner can update/delete organization
        - Only owner/admin can add/remove members
        - Only owner can change roles
        """
        # Register users
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": user_data["email"],
                "password": user_data["password"],
            },
        )
        owner_token = response.json()["access_token"]

        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": second_user_data["email"],
                "password": second_user_data["password"],
            },
        )
        member_token = response.json()["access_token"]
        member_id = await self._get_user_id_from_token(member_token)

        # Create org as owner
        response = await client.post(
            "/api/v1/orgs",
            json={
                "access_token": owner_token,
                "name": "Permission Test Org",
            },
        )
        org_id = response.json()["org_id"]

        # Add member (owner can add)
        response = await client.post(
            "/api/v1/orgs/members",
            json={
                "access_token": owner_token,
                "org_id": org_id,
                "user_id": member_id,
                "role": "member",
            },
        )
        assert response.status_code == 201

        # Member tries to update org (should fail)
        response = await client.put(
            "/api/v1/orgs",
            json={
                "access_token": member_token,
                "org_id": org_id,
                "new_name": "Hacked Name",
            },
        )
        assert response.status_code == 403

        # Member tries to delete org (should fail)
        response = await client.post(
            "/api/v1/orgs/delete",
            json={
                "access_token": member_token,
                "org_id": org_id,
            },
        )
        assert response.status_code == 403

        # Member tries to add another user (should fail)
        response = await client.post(
            "/api/v1/orgs/members",
            json={
                "access_token": member_token,
                "org_id": org_id,
                "user_id": "some-id",
                "role": "member",
            },
        )
        assert response.status_code == 403

        # Member tries to remove someone (should fail)
        response = await client.post(
            "/api/v1/orgs/members/delete",
            json={
                "access_token": member_token,
                "org_id": org_id,
                "user_id": member_id,
            },
        )
        assert response.status_code == 403

        # Member tries to change role (should fail)
        response = await client.put(
            "/api/v1/orgs/members/role",
            json={
                "access_token": member_token,
                "org_id": org_id,
                "user_id": member_id,
                "new_role": "admin",
            },
        )
        assert response.status_code == 403

        # Owner changes member to admin
        response = await client.put(
            "/api/v1/orgs/members/role",
            json={
                "access_token": owner_token,
                "org_id": org_id,
                "user_id": member_id,
                "new_role": "admin",
            },
        )
        assert response.status_code == 200

        # Now member (admin) can add another user (but we don't have third user, so just check permission)
        # For now, we just verify admin can add - we need third user
        # Register third user
        third_user_data = {
            "email": "third@example.com",
            "password": "StrongP@ssw0rd789",
        }
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": third_user_data["email"],
                "password": third_user_data["password"],
            },
        )
        third_token = response.json()["access_token"]
        third_id = await self._get_user_id_from_token(third_token)

        response = await client.post(
            "/api/v1/orgs/members",
            json={
                "access_token": member_token,
                "org_id": org_id,
                "user_id": third_id,
                "role": "member",
            },
        )
        assert response.status_code == 201

        # Admin tries to change role (should fail - only owner)
        response = await client.put(
            "/api/v1/orgs/members/role",
            json={
                "access_token": member_token,
                "org_id": org_id,
                "user_id": third_id,
                "new_role": "admin",
            },
        )
        assert response.status_code == 403

        # Cleanup: delete org
        await client.post(
            "/api/v1/orgs/delete",
            json={
                "access_token": owner_token,
                "org_id": org_id,
            },
        )

    async def test_add_member_already_member(self, client, user_data, second_user_data):
        """Adding user who is already a member should fail"""
        # Register users
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": user_data["email"],
                "password": user_data["password"],
            },
        )
        owner_token = response.json()["access_token"]

        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": second_user_data["email"],
                "password": second_user_data["password"],
            },
        )
        member_token = response.json()["access_token"]
        member_id = await self._get_user_id_from_token(member_token)

        # Create org
        response = await client.post(
            "/api/v1/orgs",
            json={
                "access_token": owner_token,
                "name": "Test Org",
            },
        )
        org_id = response.json()["org_id"]

        # Add member once
        response = await client.post(
            "/api/v1/orgs/members",
            json={
                "access_token": owner_token,
                "org_id": org_id,
                "user_id": member_id,
                "role": "member",
            },
        )
        assert response.status_code == 201

        # Add again
        response = await client.post(
            "/api/v1/orgs/members",
            json={
                "access_token": owner_token,
                "org_id": org_id,
                "user_id": member_id,
                "role": "member",
            },
        )
        assert response.status_code == 409

    async def test_remove_nonexistent_member(self, client, user_data):
        """Removing a user who is not a member should fail"""
        # Register user
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": user_data["email"],
                "password": user_data["password"],
            },
        )
        token = response.json()["access_token"]

        # Create org
        response = await client.post(
            "/api/v1/orgs",
            json={
                "access_token": token,
                "name": "Test Org",
            },
        )
        org_id = response.json()["org_id"]

        # Remove non-existent member
        response = await client.post(
            "/api/v1/orgs/members/delete",
            json={
                "access_token": token,
                "org_id": org_id,
                "user_id": "non-existent-id",
            },
        )
        assert response.status_code == 404

    async def test_get_nonexistent_org(self, client, user_data):
        """Getting a non-existent organization should return 404"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": user_data["email"],
                "password": user_data["password"],
            },
        )
        token = response.json()["access_token"]

        response = await client.post(
            "/api/v1/orgs/get",
            json={
                "access_token": token,
                "org_id": "non-existent-id",
            },
        )
        assert response.status_code == 404

    async def _get_user_id_from_token(self, token: str) -> str:
        """Helper to extract user_id from JWT token"""
        decoder = JWTDecoder()
        payload = decoder.decode_token(token)
        return payload["sub"]
