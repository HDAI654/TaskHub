from abc import ABC, abstractmethod
from src.modules.core.id_vo import ID


class ITokenRepository(ABC):
    """Repository for token management (blacklist + user version)."""
    
    @abstractmethod
    async def block_token(self, token_id: ID, ttl_seconds: int) -> None:
        """
        Add a token to blacklist.
        
        Args:
            token_id: JWT ID (jti) of the token
            ttl_seconds: Remaining lifetime of the token (will auto-expire)
        """
        pass

    @abstractmethod
    async def is_token_blocked(self, token_id: ID) -> bool:
        """Check if a token is in blacklist."""
        pass
    
    @abstractmethod
    async def get_user_version(self, user_id: ID) -> int:
        """
        Get current token version for a user.
        """
        pass

    @abstractmethod
    async def increment_user_version(self, user_id: ID) -> int:
        """
        Increment user's token version.
        This invalidates ALL previous tokens for this user.
        
        Returns:
            The new version number
        """
        pass