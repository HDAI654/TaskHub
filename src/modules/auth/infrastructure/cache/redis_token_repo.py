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
        logger.info("Adding token to blacklist: id=%s", token_id.value)
        key = f"blacklist:{token_id.value}"

        now = datetime.now(timezone.utc)
        expiry = datetime.fromtimestamp(expires_at, tz=timezone.utc)
        ttl_seconds = int((expiry - now).total_seconds())

        if ttl_seconds > 0:
            await self._execute_redis_operation(
                "setex", self._client.setex, key, ttl_seconds, "revoked"
            )
            logger.debug("Token blocked: id=%s, TTL=%ss", token_id.value, ttl_seconds)
        else:
            logger.debug(
                "Token already expired, no need to block: id=%s", token_id.value
            )

        logger.info("Token added to blacklist successfully: id=%s", token_id.value)

    async def is_token_blocked(self, token_id: ID) -> bool:
        """Check if a token is in blacklist."""
        logger.info("Checking token is in blacklist: id=%s", token_id.value)
        key = f"blacklist:{token_id.value}"
        exists = await self._execute_redis_operation(
            "check_exists", self._client.exists, key
        )
        logger.info("Token checked: id=%s, blocked=%s", token_id.value, bool(exists))
        return exists == 1

    async def get_user_version(self, user_id: ID) -> int:
        """Get current token version for a user."""
        logger.info("Getting user version: user_id=%s", user_id.value)
        key = f"token_version:{user_id.value}"
        version = await self._execute_redis_operation(
            "get_version", self._client.get, key
        )

        if version is None:
            version = 0

        logger.info("User version found successfully: user_id=%s", user_id.value)

        return int(version)

    async def increment_user_version(self, user_id: ID) -> int:
        """Increment user's token version (invalidates all previous tokens)."""
        logger.info(
            "Incrementing user version: user_id=%s",
            user_id.value,
        )
        key = f"token_version:{user_id.value}"
        new_version = await self._execute_redis_operation(
            "increment_version", self._client.incr, key
        )
        logger.info(
            "User version incremented: user_id=%s, new_version=%s,",
            user_id.value,
            new_version,
        )
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
