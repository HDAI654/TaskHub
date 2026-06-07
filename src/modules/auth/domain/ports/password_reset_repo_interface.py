from abc import ABC, abstractmethod
from src.modules.core.id_vo import ID


class IPasswordResetRepository(ABC):
    """Repository for password reset tokens (one-time use, TTL-based)"""

    @abstractmethod
    async def add(self, token: str, user_id: ID, ttl_seconds: int) -> None:
        """Store reset token with expiration"""
        pass

    @abstractmethod
    async def get(self, token: str) -> ID | None:
        """Get user_id by token, returns None if not found or expired"""
        pass

    @abstractmethod
    async def delete(self, token: str) -> None:
        """Delete token after use (optional but recommended)"""
        pass
