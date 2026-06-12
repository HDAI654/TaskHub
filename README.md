# TaskHub

## Overview

TaskHub is a **real-time collaborative project management platform** built with a hybrid architecture combining **Hexagonal (Ports & Adapters)** and **Layered Architecture** principles. It features REST APIs for CRUD operations and WebSocket for real-time collaboration on boards.

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| **Web Framework** | FastAPI (ASGI) |
| **Database** | PostgreSQL (async via aiosqlite) |
| **ORM** | SQLAlchemy 2.0 (async) |
| **Caching & Token Storage** | Redis |
| **Authentication** | JWT (RS256) |
| **Real-time Communication** | WebSockets |
| **Password Hashing** | bcrypt |
| **Testing** | pytest, pytest-asyncio, httpx |
| **Background Tasks** | Celery (workers) |

---

## Hybrid Architecture: Hexagonal + Layered

TaskHub combines the **dependency inversion** of Hexagonal Architecture with the **clear separation of concerns** of Layered Architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                         │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐    │
│  │ REST API v1  │  │ WebSocket    │  │Rate Limit Middleware│    │
│  │ (FastAPI)    │  │ Endpoints    │  │                     │    │
│  └──────────────┘  └──────────────┘  └─────────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│                       APPLICATION LAYER                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Services (Use Cases)                                     │   │
│  │ • Auth: Login, Signup, Logout, Token Rotation, etc       │   │
│  │ • Org: CreateOrg, UpdateOrg, AddMember, etc.             │   │
│  │ • Card: CreateCard, EditCard, DeleteCard, etc.           │   │
│  └──────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                         DOMAIN LAYER                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Entities • Value Objects • Factories • Domain Exceptions │   │
│  │                                                          │   │
│  │ Ports (Interfaces) - The "Hexagonal" Core               │   │
│  │  • IUserRepository • ITokenRepository • ICardRepository  │   │
│  │  • IOrgRepository • IProjectRepository • IBoardRepository│   │
│  │  • IColumnRepository • IUnitOfWork                       │   │
│  └──────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                     INFRASTRUCTURE LAYER                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐   │
│  │ SQLAlchemy │  │ Redis      │  │ JWT        │  │ Password │   │
│  │Repositories│  │Repositories│  │ Encoder    │  │ Hasher   │   │
│  │ (Adapters) │  │ (Adapters) │  │ (Adapter)  │  │ (Adapter)│   │
│  └────────────┘  └────────────┘  └────────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**How the hybrid approach works:**
- **Layered separation**: Presentation, Application, Domain, Infrastructure
- **Hexagonal ports**: Domain defines interfaces (ports), Infrastructure implements them (adapters)
- **Dependency inversion**: Outer layers depend on inner layers, never the reverse

---

## Module Structure

```
module/
├── application/     # Use cases (orchestrates domain objects)
├── domain/          # Entities, value objects, repository interfaces (ports)
├── infrastructure/  # Repository implementations (adapters: SQLAlchemy, Redis)
└── presentation/    # REST API endpoints / WebSocket endpoint (driving adapters)
```

---

## Design Patterns

### 1. Hybrid Hexagonal + Layered Architecture
- **Layers**: Clear vertical separation (Presentation, Application, Domain, Infrastructure)
- **Ports**: Domain interfaces define what the application needs
- **Adapters**: Infrastructure implements those interfaces
- **Dependency Rule**: Outer layers depend only on inner layers (never inward)

### 2. Repository Pattern (Port)
```python
# Domain Port
class IUserRepository(ABC):
    @abstractmethod
    async def add(self, user: UserEntity) -> None: pass

# Infrastructure Adapter
class SQLAL_UserRepository(IUserRepository):
    async def add(self, user: UserEntity) -> None:
        # SQLAlchemy implementation
```

### 3. Unit of Work Pattern
Manages transactions across multiple repositories:
- Ensures data consistency
- Enables rollback on failures
- All repositories share the same session

### 4. Value Objects (Immutable)
- Encapsulate validation logic
- No identity, only attributes
- Examples: Email, Password, Title, Priority

### 5. Factory Pattern
Encapsulates complex entity creation with validation

### 6. Dependency Injection (FastAPI Depends)
- Decouples service creation from usage
- Enables easy mocking in tests

### 7. Connection Manager (Room-based Broadcasting)
- Manages WebSocket connections per board
- Broadcasts events to all members of a room

---

## Security Design

### Authentication
- **JWT with RS256** (private/public key pair)
- Access token: short-lived (15-30 min)
- Refresh token: longer-lived, rotated on each use
- Token version stored in Redis for invalidation

### Authorization (Role-Based)
| Role | Permissions |
|------|-------------|
| **owner** | Full control (delete org, change roles) |
| **admin** | Manage members, projects, boards, columns, cards |
| **member** | View cards, update checklists |
| **viewer** | Read-only access |

### Rate Limiting
- Redis-based sliding window
- Different limits per endpoint:
  - Auth endpoints: 5-10 req/min
  - CRUD endpoints: 20-30 req/min

### Token Blacklisting
- On logout, tokens added to Redis blacklist
- On password change, user version incremented (invalidates all tokens)

---

## Testing Strategy

### Unit Tests (`tests/unit/`)
- Domain entities and value objects
- Application services (mocked dependencies)
- Repository implementations (in-memory SQLite)

### End-to-End Tests (`tests/e2e/`)
- Complete API flows with real database
- Multi-user WebSocket collaboration
- Rate limiting validation

---

## Conclusion

TaskHub is a **modular, testable, and extensible** real-time collaboration platform. Its hybrid architecture combines the **dependency inversion** benefits of Hexagonal Architecture with the **clear layer separation** of Layered Architecture. WebSocket integration provides seamless real-time updates, while the design prioritizes security, maintainability, and a clean developer experience.