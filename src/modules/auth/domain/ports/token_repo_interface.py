from abc import ABC, abstractmethod
from src.modules.core.id_vo import ID


class ITokenRepository(ABC):
    """Repository interface for token management (blacklist + user version)."""
    
    @abstractmethod
    async def block_token(self, token_id: ID, expires_at: float | int) -> None:
        """Add a token to blacklist."""
        pass

    @abstractmethod
    async def is_token_blocked(self, token_id: ID) -> bool:
        """Check if a token is in blacklist."""
        pass
    
    @abstractmethod
    async def get_user_version(self, user_id: ID) -> int:
        """Get current token version for a user."""
        pass

    @abstractmethod
    async def increment_user_version(self, user_id: ID) -> int:
        """Increment user's token version."""
        pass