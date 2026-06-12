import pytest
import json
import asyncio
import websockets
import httpx
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
WS_BASE_URL = "ws://localhost:8000"


class TestCardWebSocketLiveE2E:
    """Full E2E tests against running application on localhost:8000"""

    @pytest.fixture
    async def http_client(self):
        """HTTP client for REST API calls."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            yield client

    @pytest.fixture
    def owner_data(self):
        return {
            "email": f"owner_{int(datetime.now().timestamp())}@cardws.com",
            "password": "StrongP@ssw0rd123",
        }

    @pytest.fixture
    def admin_data(self):
        return {
            "email": f"admin_{int(datetime.now().timestamp())}@cardws.com",
            "password": "StrongP@ssw0rd456",
        }

    @pytest.fixture
    def member_data(self):
        return {
            "email": f"member_{int(datetime.now().timestamp())}@cardws.com",
            "password": "StrongP@ssw0rd789",
        }

    async def _get_user_id_from_token(self, token: str, http_client) -> str:
        """Extract user ID from token by decoding locally."""
        import base64

        parts = token.split(".")
        if len(parts) != 3:
            return None
        # Add padding if needed
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += "=" * padding
        decoded = json.loads(base64.b64decode(payload).decode("utf-8"))
        return decoded.get("sub")

    async def test_complete_card_lifecycle_with_websocket_broadcast(
        self, http_client, owner_data, admin_data, member_data
    ):
        """
        Complete real-time collaboration test:
        1. Register 3 users (owner, admin, member)
        2. Create organization, project, board, column
        3. Add admin and member to organization
        4. Open WebSocket connections for owner and admin
        5. Test all card operations with real-time broadcast verification
        """
        print("\n" + "=" * 60)
        print("STARTING COMPLETE CARD LIFECYCLE TEST")
        print("=" * 60)

        # ===== 1. Register users =====
        print("\n📝 Registering users...")

        resp = await http_client.post("/api/v1/auth/register", json=owner_data)
        assert resp.status_code == 201, f"Owner registration failed: {resp.text}"
        owner_token = resp.json()["access_token"]
        print(f"✅ Owner registered: {owner_data['email']}")

        resp = await http_client.post("/api/v1/auth/register", json=admin_data)
        assert resp.status_code == 201, f"Admin registration failed: {resp.text}"
        admin_token = resp.json()["access_token"]
        print(f"✅ Admin registered: {admin_data['email']}")

        resp = await http_client.post("/api/v1/auth/register", json=member_data)
        assert resp.status_code == 201, f"Member registration failed: {resp.text}"
        member_token = resp.json()["access_token"]
        print(f"✅ Member registered: {member_data['email']}")

        # Get user IDs
        owner_id = await self._get_user_id_from_token(owner_token, http_client)
        admin_id = await self._get_user_id_from_token(admin_token, http_client)
        member_id = await self._get_user_id_from_token(member_token, http_client)
        print(f"📝 Owner ID: {owner_id}")
        print(f"📝 Admin ID: {admin_id}")
        print(f"📝 Member ID: {member_id}")

        # ===== 2. Create organization =====
        print("\n🏢 Creating organization...")
        resp = await http_client.post(
            "/api/v1/mng/orgs",
            json={"access_token": owner_token, "name": "Live Test Org"},
        )
        assert resp.status_code == 201
        org_id = resp.json()["org_id"]
        print(f"✅ Organization created: {org_id}")

        # ===== 3. Create project =====
        print("\n📁 Creating project...")
        resp = await http_client.post(
            f"/api/v1/mng/orgs/{org_id}/projects",
            json={
                "access_token": owner_token,
                "name": "Live Project",
                "description": "Test project",
            },
        )
        assert resp.status_code == 201
        project_id = resp.json()["project_id"]
        print(f"✅ Project created: {project_id}")

        # ===== 4. Create board =====
        print("\n📋 Creating board...")
        resp = await http_client.post(
            f"/api/v1/mng/projects/{project_id}/boards",
            json={
                "access_token": owner_token,
                "name": "Live Board",
                "description": "Test board",
            },
        )
        assert resp.status_code == 201
        board_id = resp.json()["board_id"]
        print(f"✅ Board created: {board_id}")

        # ===== 5. Add admin and member to organization =====
        print("\n👥 Adding members to organization...")
        resp = await http_client.post(
            f"/api/v1/mng/orgs/{org_id}/members",
            json={"access_token": owner_token, "user_id": admin_id, "role": "admin"},
        )
        assert resp.status_code == 201
        print(f"✅ Admin added: {admin_id}")

        resp = await http_client.post(
            f"/api/v1/mng/orgs/{org_id}/members",
            json={"access_token": owner_token, "user_id": member_id, "role": "member"},
        )
        assert resp.status_code == 201
        print(f"✅ Member added: {member_id}")

        # ===== 6. Create column =====
        print("\n📊 Creating column...")
        resp = await http_client.post(
            f"/api/v1/mng/boards/{board_id}/columns",
            json={"access_token": owner_token, "name": "Todo", "order": 1},
        )
        assert resp.status_code == 201
        column_id = resp.json()["column_id"]
        print(f"✅ Column created: {column_id}")

        # ===== 7. Open WebSocket connections =====
        print("\n🔌 Opening WebSocket connections...")

        owner_ws_url = f"{WS_BASE_URL}/ws/boards/{board_id}?access_token={owner_token}"
        admin_ws_url = f"{WS_BASE_URL}/ws/boards/{board_id}?access_token={admin_token}"

        owner_ws = await websockets.connect(owner_ws_url)
        admin_ws = await websockets.connect(admin_ws_url)
        print("✅ Both WebSocket connections established")

        # Helper functions
        async def recv_json(ws, timeout=10):
            """Receive and parse JSON from WebSocket."""
            msg = await asyncio.wait_for(ws.recv(), timeout=timeout)
            return json.loads(msg)

        async def send_action(ws, action, **kwargs):
            """Send an action and return the response."""
            msg = {"action": action, **kwargs}
            await ws.send(json.dumps(msg))
            # Wait for response (message with "status" field)
            while True:
                response = await recv_json(ws)
                if "status" in response:
                    return response
                print(f"  ⚠️ Unexpected message while waiting for response: {response}")

        async def wait_for_broadcast(ws, expected_type, timeout=10):
            """Wait for a specific broadcast message type."""
            while True:
                msg = await recv_json(ws, timeout)
                if msg.get("type") == expected_type:
                    return msg
                print(
                    f"  ⚠️ Received broadcast type {msg.get('type')}, waiting for {expected_type}"
                )

        # ===== 8. Test: Create card =====
        print("\n➕ Testing: Create card...")
        create_result = await send_action(
            owner_ws,
            "create_card",
            column_id=column_id,
            title="Live Test Card",
            description="Created via WebSocket",
            priority="high",
            due_date="2025-12-31T23:59:59+00:00",
        )
        assert create_result["status"] == "success"
        card_id = create_result["result"]["card_id"]
        print(f"✅ Card created: {card_id}")

        # Verify admin receives broadcast
        admin_broadcast = await wait_for_broadcast(admin_ws, "card_created")
        assert admin_broadcast["data"]["card_id"] == card_id
        print("✅ Admin received card_created broadcast")

        # ===== 9. Test: Add checklist =====
        print("\n✅ Testing: Add checklist...")
        add_checklist_result = await send_action(
            admin_ws, "add_checklist", card_id=card_id, title="Initial Checklist"
        )
        assert add_checklist_result["status"] == "success"
        print("✅ Checklist added")

        # Verify owner receives broadcast
        owner_broadcast = await wait_for_broadcast(owner_ws, "checklist_added")
        print(f"  📨 Received broadcast: {owner_broadcast}")
        assert owner_broadcast["type"] == "checklist_added"
        print("✅ Owner received checklist_added broadcast")

        # ===== 10. Test: Get card checklists (no broadcast) =====
        print("\n📋 Testing: Get card checklists...")
        get_checklists_result = await send_action(
            admin_ws, "get_card_checklists", card_id=card_id
        )
        assert get_checklists_result["action"] == "get_card_checklists"
        assert len(get_checklists_result["result"]) == 1
        checklist_id = get_checklists_result["result"][0]["id"]
        print(f"✅ Retrieved checklist ID: {checklist_id}")

        # ===== 11. Test: Update checklist =====
        print("\n✏️ Testing: Update checklist...")
        update_result = await send_action(
            admin_ws,
            "update_checklist",
            checklist_id=checklist_id,
            new_title="Updated Checklist",
            new_is_checked=True,
        )
        assert update_result["status"] == "success"
        print("✅ Checklist updated")

        # Verify owner receives broadcast
        owner_broadcast = await wait_for_broadcast(owner_ws, "checklist_updated")
        assert owner_broadcast["type"] == "checklist_updated"
        print("✅ Owner received checklist_updated broadcast")

        # ===== 12. Test: Add label =====
        print("\n🏷️ Testing: Add label...")
        add_label_result = await send_action(
            admin_ws, "add_label", card_id=card_id, label_name="urgent"
        )
        assert add_label_result["status"] == "success"
        print("✅ Label added")

        # Verify owner receives broadcast
        owner_broadcast = await wait_for_broadcast(owner_ws, "label_added")
        assert owner_broadcast["type"] == "label_added"
        print("✅ Owner received label_added broadcast")

        # ===== 13. Test: Get card labels (no broadcast) =====
        print("\n🏷️ Testing: Get card labels...")
        get_labels_result = await send_action(
            admin_ws, "get_card_labels", card_id=card_id
        )
        assert get_labels_result["action"] == "get_card_labels"
        assert len(get_labels_result["result"]) == 1
        assert get_labels_result["result"][0]["name"] == "urgent"
        print("✅ Retrieved labels successfully")

        # ===== 14. Test: Remove label =====
        print("\n🗑️ Testing: Remove label...")
        remove_label_result = await send_action(
            admin_ws, "remove_label", card_id=card_id, label_name="urgent"
        )
        assert remove_label_result["status"] == "success"
        print("✅ Label removed")

        # Verify owner receives broadcast
        owner_broadcast = await wait_for_broadcast(owner_ws, "label_removed")
        assert owner_broadcast["type"] == "label_removed"
        print("✅ Owner received label_removed broadcast")

        # ===== 15. Test: Add assignee =====
        print("\n👤 Testing: Add assignee...")
        add_assignee_result = await send_action(
            admin_ws, "add_assignee", card_id=card_id, assignee_id=member_id
        )
        assert add_assignee_result["status"] == "success"
        print("✅ Assignee added")

        # Verify owner receives broadcast
        owner_broadcast = await wait_for_broadcast(owner_ws, "assignee_added")
        assert owner_broadcast["type"] == "assignee_added"
        print("✅ Owner received assignee_added broadcast")

        # ===== 16. Test: Get card assignees (no broadcast) =====
        print("\n👥 Testing: Get card assignees...")
        get_assignees_result = await send_action(
            admin_ws, "get_card_assignees", card_id=card_id
        )
        assert get_assignees_result["action"] == "get_card_assignees"
        assert len(get_assignees_result["result"]) == 1
        assert get_assignees_result["result"][0]["user_id"] == member_id
        print("✅ Retrieved assignees successfully")

        # ===== 17. Test: Remove assignee =====
        print("\n👤 Testing: Remove assignee...")
        remove_assignee_result = await send_action(
            admin_ws, "remove_assignee", card_id=card_id, assignee_id=member_id
        )
        assert remove_assignee_result["status"] == "success"
        print("✅ Assignee removed")

        # Verify owner receives broadcast
        owner_broadcast = await wait_for_broadcast(owner_ws, "assignee_removed")
        assert owner_broadcast["type"] == "assignee_removed"
        print("✅ Owner received assignee_removed broadcast")

        # ===== 18. Test: Edit card =====
        print("\n✏️ Testing: Edit card...")
        edit_result = await send_action(
            admin_ws,
            "edit_card",
            card_id=card_id,
            new_title="Edited Live Card",
            new_priority="urgent",
        )
        assert edit_result["status"] == "success"
        print("✅ Card edited")

        # Verify owner receives broadcast
        owner_broadcast = await wait_for_broadcast(owner_ws, "card_updated")
        assert owner_broadcast["type"] == "card_updated"
        print("✅ Owner received card_updated broadcast")

        # ===== 19. Test: Get card by ID (no broadcast) =====
        print("\n🔍 Testing: Get card by ID...")
        get_card_result = await send_action(admin_ws, "get_card_by_id", card_id=card_id)
        assert get_card_result["action"] == "get_card_by_id"
        assert get_card_result["result"]["title"] == "Edited Live Card"
        assert get_card_result["result"]["priority"] == "urgent"
        print("✅ Retrieved card details successfully")

        # ===== 20. Test: Delete checklist =====
        print("\n🗑️ Testing: Delete checklist...")
        delete_checklist_result = await send_action(
            admin_ws, "delete_checklist", checklist_id=checklist_id
        )
        assert delete_checklist_result["status"] == "success"
        print("✅ Checklist deleted")

        # Verify owner receives broadcast
        owner_broadcast = await wait_for_broadcast(owner_ws, "checklist_deleted")
        assert owner_broadcast["type"] == "checklist_deleted"
        print("✅ Owner received checklist_deleted broadcast")

        # ===== 21. Test: Delete card =====
        print("\n🗑️ Testing: Delete card...")
        delete_card_result = await send_action(admin_ws, "delete_card", card_id=card_id)
        assert delete_card_result["status"] == "success"
        print("✅ Card deleted")

        # Verify owner receives broadcast
        owner_broadcast = await wait_for_broadcast(owner_ws, "card_deleted")
        assert owner_broadcast["type"] == "card_deleted"
        print("✅ Owner received card_deleted broadcast")

        # ===== 22. Cleanup =====
        print("\n🧹 Cleaning up...")
        await owner_ws.close()
        await admin_ws.close()

        # Delete board, project, org via REST
        await http_client.delete(
            f"/api/v1/mng/boards/{board_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        await http_client.delete(
            f"/api/v1/mng/projects/{project_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        await http_client.delete(
            f"/api/v1/mng/orgs/{org_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        print("\n" + "=" * 60)
        print(
            "🎉 ALL TESTS PASSED! Complete card lifecycle verified with real-time broadcasting"
        )
        print("=" * 60)
