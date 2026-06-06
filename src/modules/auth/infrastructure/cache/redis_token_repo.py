import logging
from redis.asyncio import Redis
from datetime import datetime, timezone
from src.modules.core.id_vo import ID
from src.modules.auth.domain.ports.token_repo_interface import ITokenRepository
from redis.exceptions import RedisError, ConnectionError, TimeoutError
from src.modules.auth.exceptions import (
    CacheConnectionError,
    CacheTimeoutError,
    CacheOperationError,
)

logger = logging.getLogger(__name__)


class RedisTokenRepository(ITokenRepository):
    """Redis Repository for tokens."""

    def __init__(self, client: Redis):
        self._client = client

    async def block_token(self, token_id: ID, expires_at: float | int) -> None:
        """
        Add a token to blacklist.
        """
        key = f"blacklist:{token_id.value}"
        
        now = datetime.now(timezone.utc)
        expiry = datetime.fromtimestamp(expires_at, tz=timezone.utc)
        ttl_seconds = int((expiry - now).total_seconds())
        
        if ttl_seconds > 0:
            await self._client.setex(key, ttl_seconds, "revoked")
            logger.debug(f"Token blocked: {token_id.value}, TTL: {ttl_seconds}s")
        else:
            logger.debug(f"Token already expired, no need to block: {token_id.value}")

    async def is_token_blocked(self, token_id: ID) -> bool:
        """Check if a token is in blacklist."""
        key = f"blacklist:{token_id.value}"
        exists = await self._client.exists(key)
        logger.debug(f"Token check: {token_id.value}, blocked={bool(exists)}")
        return exists == 1

    async def get_user_version(self, user_id: ID) -> int:
        """Get current token version for a user."""
        key = f"token_version:{user_id.value}"
        version = await self._client.get(key)
        
        if version is None:
            return 0
        
        return int(version)

    async def increment_user_version(self, user_id: ID) -> int:
        """Increment user's token version (invalidates all previous tokens)."""
        key = f"token_version:{user_id.value}"
        new_version = await self._client.incr(key)
        logger.info(f"User version incremented: user_id={user_id.value}, new_version={new_version}")
        return new_version
    

    async def _execute_redis_operation(self, operation: str, coro, *args, **kwargs):
        """Generic wrapper for Redis operations with error handling"""
        try:
            return await coro(*args, **kwargs)
        except ConnectionError as e:
            logger.exception(f"Failed to connect to Redis during {operation}")
            raise CacheConnectionError(f"Failed to connect to cache: {e}") from e
        except TimeoutError as e:
            logger.exception(f"Redis timeout during {operation}")
            raise CacheTimeoutError(f"Cache operation timed out: {e}") from e
        except RedisError as e:
            logger.exception(f"Redis error during {operation}")
            raise CacheOperationError(f"Cache operation failed: {e}") from e