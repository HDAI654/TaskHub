from abc import ABC, abstractmethod
from src.modules.auth.domain.entities.session import SessionEntity
from src.modules.core.id_vo import ID


class ISessionRepository(ABC):
    """Repository interface for Session entities."""

    SESSION_TTL_SECONDS: int
    SESSION_KEY_PREFIX: str
    USER_SESSIONS_KEY_PREFIX: str

    @abstractmethod
    async def add(self, session: SessionEntity) -> None:
        """Create a new session in the database."""
        pass

    @abstractmethod
    async def extend_session(self, session_id: ID) -> None:
        """Extend the session's expiration time."""
        pass

    @abstractmethod
    async def delete(self, session_id: ID, user_id: ID) -> None:
        """Delete a single session by ID."""
        pass

    @abstractmethod
    async def delete_all_other_sessions(
        self, current_session_id: ID, user_id: ID
    ) -> None:
        """Delete all sessions for a user except the current one."""
        pass

    @abstractmethod
    async def get_by_id(self, session_id: ID) -> SessionEntity:
        """Get a session by ID."""
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: ID) -> list[SessionEntity]:
        """Get a session by UserID."""
        pass
