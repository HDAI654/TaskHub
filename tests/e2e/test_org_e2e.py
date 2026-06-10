import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.modules.core.database import engine, Base
from src.modules.core.redis_client import get_redis_client
from src.modules.core.jwt_decoder import JWTDecoder


class TestOrgMngE2E:
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
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": user_data["email"],
                "password": user_data["password"],
            },
        )
        assert response.status_code == 201
        owner_token = response.json()["access_token"]

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
            "/api/v1/mng/orgs",
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
            f"/api/v1/mng/orgs/{org_id}/members",
            json={
                "access_token": owner_token,
                "user_id": member_user_id,
                "role": "member",
            },
        )
        assert response.status_code == 201
        assert response.json()["message"] == "Member added successfully"

        # ===== Get organization details =====
        response = await client.get(
            f"/api/v1/mng/orgs/{org_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["org_id"] == org_id
        assert data["name"] == "Test Org"

        # ===== Get user's organizations =====
        response = await client.get(
            "/api/v1/mng/users/orgs",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["orgs"]) == 1
        assert data["orgs"][0]["organization_id"] == org_id
        assert data["orgs"][0]["name"] == "Test Org"
        assert data["orgs"][0]["role"] == "owner"

        # ===== Get organization members =====
        response = await client.get(
            f"/api/v1/mng/orgs/{org_id}/members",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["members"]) == 2
        roles = {m["user_id"]: m["role"] for m in data["members"]}
        assert roles[await self._get_user_id_from_token(owner_token)] == "owner"
        assert roles[member_user_id] == "member"

        # ===== Change member role =====
        response = await client.put(
            f"/api/v1/mng/orgs/{org_id}/members/{member_user_id}/role",
            json={
                "access_token": owner_token,
                "new_role": "admin",
            },
        )
        assert response.status_code == 200
        assert response.json()["message"] == "User role changed successfully"

        # Verify role changed
        response = await client.get(
            f"/api/v1/mng/orgs/{org_id}/members",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        data = response.json()
        for m in data["members"]:
            if m["user_id"] == member_user_id:
                assert m["role"] == "admin"

        # ===== Update organization name =====
        response = await client.put(
            f"/api/v1/mng/orgs/{org_id}",
            json={
                "access_token": owner_token,
                "new_name": "Updated Org Name",
            },
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Organization updated successfully"

        # Verify name updated
        response = await client.get(
            f"/api/v1/mng/orgs/{org_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert response.json()["name"] == "Updated Org Name"

        # ===== Remove member =====
        response = await client.delete(
            f"/api/v1/mng/orgs/{org_id}/members/{member_user_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Member removed successfully"

        # Verify member removed
        response = await client.get(
            f"/api/v1/mng/orgs/{org_id}/members",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        data = response.json()
        assert len(data["members"]) == 1
        assert data["members"][0]["user_id"] == await self._get_user_id_from_token(
            owner_token
        )

        # ===== Delete organization =====
        response = await client.delete(
            f"/api/v1/mng/orgs/{org_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Organization deleted successfully"

        # Verify organization no longer accessible
        response = await client.get(
            f"/api/v1/mng/orgs/{org_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert response.status_code == 404

    async def test_org_permissions(self, client, user_data, second_user_data):
        """
        Test permission checks:
        - Only owner can update/delete organization
        - Only owner/admin can add/remove members
        - Only owner can change roles
        """
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

        response = await client.post(
            "/api/v1/mng/orgs",
            json={
                "access_token": owner_token,
                "name": "Permission Test Org",
            },
        )
        org_id = response.json()["org_id"]

        # Add member (owner can add)
        response = await client.post(
            f"/api/v1/mng/orgs/{org_id}/members",
            json={
                "access_token": owner_token,
                "user_id": member_id,
                "role": "member",
            },
        )
        assert response.status_code == 201

        # Member tries to update org (should fail)
        response = await client.put(
            f"/api/v1/mng/orgs/{org_id}",
            json={
                "access_token": member_token,
                "new_name": "Hacked Name",
            },
        )
        assert response.status_code == 403

        # Member tries to delete org (should fail)
        response = await client.delete(
            f"/api/v1/mng/orgs/{org_id}",
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert response.status_code == 403

        # Member tries to add another user (should fail)
        response = await client.post(
            f"/api/v1/mng/orgs/{org_id}/members",
            json={
                "access_token": member_token,
                "user_id": "some-id",
                "role": "member",
            },
        )
        assert response.status_code == 403

        # Member tries to remove someone (should fail)
        response = await client.delete(
            f"/api/v1/mng/orgs/{org_id}/members/{member_id}",
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert response.status_code == 403

        # Member tries to change role (should fail)
        response = await client.put(
            f"/api/v1/mng/orgs/{org_id}/members/{member_id}/role",
            json={
                "access_token": member_token,
                "new_role": "admin",
            },
        )
        assert response.status_code == 403

        # Owner changes member to admin
        response = await client.put(
            f"/api/v1/mng/orgs/{org_id}/members/{member_id}/role",
            json={
                "access_token": owner_token,
                "new_role": "admin",
            },
        )
        assert response.status_code == 200

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
            f"/api/v1/mng/orgs/{org_id}/members",
            json={
                "access_token": member_token,
                "user_id": third_id,
                "role": "member",
            },
        )
        assert response.status_code == 201

        # Admin tries to change role (should fail - only owner)
        response = await client.put(
            f"/api/v1/mng/orgs/{org_id}/members/{third_id}/role",
            json={
                "access_token": member_token,
                "new_role": "admin",
            },
        )
        assert response.status_code == 403

        # Cleanup: delete org
        await client.delete(
            f"/api/v1/mng/orgs/{org_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )

    async def test_add_member_already_member(self, client, user_data, second_user_data):
        """Adding user who is already a member should fail"""
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

        response = await client.post(
            "/api/v1/mng/orgs",
            json={
                "access_token": owner_token,
                "name": "Test Org",
            },
        )
        org_id = response.json()["org_id"]

        response = await client.post(
            f"/api/v1/mng/orgs/{org_id}/members",
            json={
                "access_token": owner_token,
                "user_id": member_id,
                "role": "member",
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
        assert response.status_code == 409

    async def test_remove_nonexistent_member(self, client, user_data):
        """Removing a user who is not a member should fail"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": user_data["email"],
                "password": user_data["password"],
            },
        )
        token = response.json()["access_token"]

        response = await client.post(
            "/api/v1/mng/orgs",
            json={
                "access_token": token,
                "name": "Test Org",
            },
        )
        org_id = response.json()["org_id"]

        response = await client.delete(
            f"/api/v1/mng/orgs/{org_id}/members/non-existent-id",
            headers={"Authorization": f"Bearer {token}"},
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

        response = await client.get(
            "/api/v1/mng/orgs/non-existent-id",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    async def _get_user_id_from_token(self, token: str) -> str:
        decoder = JWTDecoder()
        payload = decoder.decode_token(token)
        return payload["sub"]
