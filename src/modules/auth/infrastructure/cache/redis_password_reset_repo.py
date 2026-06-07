# src/modules/auth/infrastructure/cache/redis_password_reset_repo.py
import logging
from redis.asyncio import Redis
from src.modules.auth.domain.value_objects.id import ID
from src.modules.auth.domain.ports.password_reset_repo_interface import (
    IPasswordResetRepository,
)
from redis.exceptions import RedisError, ConnectionError, TimeoutError
from src.modules.auth.exceptions import (
    CacheConnectionError,
    CacheTimeoutError,
    CacheOperationError,
)

logger = logging.getLogger(__name__)


class RedisPasswordResetRepository(IPasswordResetRepository):
    """Redis Repository for password reset tokens"""

    KEY_PREFIX = "password_reset:"

    def __init__(self, client: Redis):
        self._client = client

    async def add(self, token: str, user_id: ID, ttl_seconds: int = 900) -> None:
        logger.info(
            "storing user's password reset token: user_id=%s, TTL=%ss",
            user_id.value,
            ttl_seconds,
        )
        key = f"{self.KEY_PREFIX}{token}"
        await self._execute_redis_operation(
            "store_user_password_reset _token",
            self._client.setex,
            key,
            ttl_seconds,
            user_id.value,
        )
        logger.info(
            "Password reset token stored successfully: user_id=%s, TTL=%ss",
            user_id.value,
            ttl_seconds,
        )

    async def get(self, token: str) -> ID | None:
        logger.debug("Getting password reset token: token=%s...", token[:8])
        key = f"{self.KEY_PREFIX}{token}"
        user_id = await self._execute_redis_operation(
            "get_pass_reset_token", self._client.get, key
        )

        if user_id is None:
            logger.debug(
                "Password reset token not found or expired: token=%s...", token[:8]
            )
            return None

        logger.debug(
            f"Password reset token found successfully: user_id=%s, token=%s...",
            user_id,
            token[:8],
        )
        return ID(user_id)

    async def delete(self, token: str) -> None:
        logger.debug(f"Deleting password reset token deleted: token={token[:8]}...")
        key = f"{self.KEY_PREFIX}{token}"
        await self._execute_redis_operation(
            "delete_pass_reset_token", self._client.delete, key
        )
        logger.debug(f"Password reset token deleted: token={token[:8]}...")

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
