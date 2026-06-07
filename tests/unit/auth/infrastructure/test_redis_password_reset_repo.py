import pytest
import fakeredis.aioredis
from uuid import uuid4
from src.modules.auth.domain.value_objects.id import ID
from src.modules.auth.infrastructure.cache.redis_password_reset_repo import (
    RedisPasswordResetRepository,
)
from src.modules.core.crypto_utils import IDGenerator


class TestRedisPasswordResetRepository:
    @pytest.fixture
    async def redis_client(self):
        client = fakeredis.aioredis.FakeRedis(decode_responses=True)
        yield client
        await client.flushall()
        await client.aclose()

    @pytest.fixture
    async def repo(self, redis_client):
        return RedisPasswordResetRepository(redis_client)

    async def test_add_and_get_token(self, repo):
        user_id = ID()
        token = IDGenerator.generate()

        await repo.add(user_id=user_id, token=token)

        result = await repo.get(token)

        assert result is not None
        assert result.value == user_id.value

    async def test_get_expired_token_returns_none(self, repo):
        token = IDGenerator.generate()
        user_id = ID()

        await repo.add(token, user_id, ttl_seconds=1)

        import asyncio

        await asyncio.sleep(1.1)

        result = await repo.get(token)

        assert result is None

    async def test_get_nonexistent_token_returns_none(self, repo):
        result = await repo.get("nonexistent_token")
        assert result is None

    async def test_delete_token(self, repo):
        token = IDGenerator.generate()
        user_id = ID()

        await repo.add(token, user_id)
        await repo.delete(token)

        result = await repo.get(token)
        assert result is None
