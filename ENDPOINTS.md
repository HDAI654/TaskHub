# TaskHub API Documentation

## Authentication Endpoints (`/api/v1/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| **POST** | `/register` | Register a new user account |
| **POST** | `/login` | Authenticate user and get tokens |
| **POST** | `/logout` | Invalidate tokens and logout |
| **POST** | `/refresh` | Refresh access token using refresh token |
| **POST** | `/set-password` | Change user password (authenticated) |
| **POST** | `/forget-password` | Request password reset token |
| **POST** | `/reset-password` | Reset password using reset token |
| **POST** | `/invite` | Invite a new user to join (authenticated) |
| **POST** | `/delete-account` | Delete user account (authenticated) |

---

## Organization Management (`/api/v1/mng`)

### Organizations

| Method | Endpoint | Description |
|--------|----------|-------------|
| **POST** | `/orgs` | Create a new organization (owner) |
| **GET** | `/orgs/{org_id}` | Get organization details |
| **PUT** | `/orgs/{org_id}` | Update organization name (owner only) |
| **DELETE** | `/orgs/{org_id}` | Delete organization (owner only) |
| **GET** | `/users/orgs` | Get all organizations where user is member |
| **GET** | `/orgs/{org_id}/members` | Get organization members (optional role filter) |
| **POST** | `/orgs/{org_id}/members` | Add member to organization (owner/admin) |
| **DELETE** | `/orgs/{org_id}/members/{user_id}` | Remove member from organization (owner/admin) |
| **PUT** | `/orgs/{org_id}/members/{user_id}/role` | Change user role (owner only) |

### Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| **POST** | `/orgs/{org_id}/projects` | Create a new project (owner/admin) |
| **GET** | `/projects/{project_id}` | Get project details |
| **PUT** | `/projects/{project_id}` | Update project (owner/admin) |
| **DELETE** | `/projects/{project_id}` | Delete project (owner/admin) |
| **GET** | `/orgs/{org_id}/projects` | Get all projects in organization |

### Boards

| Method | Endpoint | Description |
|--------|----------|-------------|
| **POST** | `/projects/{project_id}/boards` | Create a new board (owner/admin) |
| **GET** | `/boards/{board_id}` | Get board details |
| **PUT** | `/boards/{board_id}` | Update board (owner/admin) |
| **DELETE** | `/boards/{board_id}` | Delete board (owner/admin) |
| **GET** | `/projects/{project_id}/boards` | Get all boards in project |

### Columns

| Method | Endpoint | Description |
|--------|----------|-------------|
| **POST** | `/boards/{board_id}/columns` | Create a new column (owner/admin) |
| **GET** | `/columns/{column_id}` | Get column details |
| **PUT** | `/columns/{column_id}` | Update column (owner/admin) |
| **DELETE** | `/columns/{column_id}` | Delete column (owner/admin) |
| **GET** | `/boards/{board_id}/columns` | Get all columns in board (ordered) |

---

## Real-time WebSocket Card Operations (`/ws/boards/{board_id}`)

### Connection
```
ws://localhost:8000/ws/boards/{board_id}?access_token={token}
```

### Actions (Send JSON messages)

#### Card Operations

| Action | Required Fields | Optional Fields | Broadcast | Description |
|--------|----------------|-----------------|-----------|-------------|
| `create_card` | `column_id`, `title`, `description`, `priority`, `due_date` | - | `card_created` | Create new card (owner/admin) |
| `edit_card` | `card_id` | `new_column_id`, `new_title`, `new_description`, `new_priority`, `new_due_date` | `card_updated` | Edit existing card (owner/admin) |
| `delete_card` | `card_id` | - | `card_deleted` | Delete card (owner/admin) |
| `get_card_by_id` | `card_id` | - | No broadcast | Get card details |

#### Column Operations

| Action | Required Fields | Optional Fields | Broadcast | Description |
|--------|----------------|-----------------|-----------|-------------|
| `get_column_cards` | `column_id` | - | No broadcast | Get all cards in a column |

#### Assignee Operations

| Action | Required Fields | Optional Fields | Broadcast | Description |
|--------|----------------|-----------------|-----------|-------------|
| `add_assignee` | `card_id`, `assignee_id` | - | `assignee_added` | Add assignee to card (owner/admin) |
| `remove_assignee` | `card_id`, `assignee_id` | - | `assignee_removed` | Remove assignee from card (owner/admin) |
| `get_card_assignees` | `card_id` | - | No broadcast | Get all assignees of a card |

#### Label Operations

| Action | Required Fields | Optional Fields | Broadcast | Description |
|--------|----------------|-----------------|-----------|-------------|
| `add_label` | `card_id`, `label_name` | - | `label_added` | Add label to card (owner/admin) |
| `remove_label` | `card_id`, `label_name` | - | `label_removed` | Remove label from card (owner/admin) |
| `get_card_labels` | `card_id` | - | No broadcast | Get all labels of a card |

#### Checklist Operations

| Action | Required Fields | Optional Fields | Broadcast | Description |
|--------|----------------|-----------------|-----------|-------------|
| `add_checklist` | `card_id`, `title` | - | `checklist_added` | Add checklist to card (owner/admin) |
| `update_checklist` | `checklist_id` | `new_title`, `new_is_checked` | `checklist_updated` | Update checklist (owner/admin/member) |
| `delete_checklist` | `checklist_id` | - | `checklist_deleted` | Delete checklist (owner/admin) |
| `get_checklist_by_id` | `checklist_id` | - | No broadcast | Get checklist by ID |
| `get_card_checklists` | `card_id` | - | No broadcast | Get all checklists of a card |

---

## Example WebSocket Messages

### Create Card
```json
{
  "action": "create_card",
  "column_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "New Task",
  "description": "Complete the implementation",
  "priority": "high",
  "due_date": "2025-12-31T23:59:59+00:00"
}
```

### Response (Success)
```json
{
  "action": "create_card",
  "result": {
    "card_id": "550e8400-e29b-41d4-a716-446655440001",
    "title": "New Task",
    "column_id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "status": "success"
}
```

### Broadcast to Other Clients
```json
{
  "type": "card_created",
  "data": {
    "card_id": "550e8400-e29b-41d4-a716-446655440001",
    "title": "New Task",
    "column_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

---

## Priority Values
- `low`
- `medium`
- `high`
- `urgent`

## Role Values
- `owner` – Full control over organization
- `admin` – Can manage members, projects, boards, columns, cards (except delete organization)
- `member` – Can view and update checklists only
- `viewer` – Read-only access

## Authentication
All REST endpoints (except `/register` and `/login`) require Bearer token authentication:
```
Authorization: Bearer {access_token}
```

WebSocket connections require the token as a query parameter:
```
ws://localhost:8000/ws/boards/{board_id}?access_token={token}
```