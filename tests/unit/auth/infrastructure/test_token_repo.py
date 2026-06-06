import pytest
from datetime import datetime, timedelta, timezone
from src.modules.auth.infrastructure.cache.redis_token_repo import RedisTokenRepository
from src.modules.auth.domain.ports.token_repo_interface import ITokenRepository
from src.modules.auth.domain.value_objects.id import ID
import fakeredis.aioredis


class TestTokenRepo:
    @pytest.fixture
    async def redis_client(self):
        client = fakeredis.aioredis.FakeRedis(decode_responses=True)
        yield client
        await client.flushall()
        await client.aclose()

    @pytest.fixture
    async def token_repo(self, redis_client) -> ITokenRepository:
        return RedisTokenRepository(redis_client)

    @pytest.fixture
    def user_id(self):
        return ID()

    @pytest.fixture
    def token_id(self):
        return ID()
    
    @pytest.mark.asyncio
    async def test_block_token_success(self, token_repo: ITokenRepository, token_id: ID):
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()
        
        await token_repo.block_token(token_id, expires_at)
        
        assert await token_repo.is_token_blocked(token_id) is True

    @pytest.mark.asyncio
    async def test_is_token_blocked_returns_false_for_non_blocked(self, token_repo: ITokenRepository, token_id: ID):
        assert await token_repo.is_token_blocked(token_id) is False

    @pytest.mark.asyncio
    async def test_block_token_ttl_is_correct(self, token_repo: RedisTokenRepository, redis_client, token_id: ID):
        expires_at = (datetime.now(timezone.utc) + timedelta(seconds=3600)).timestamp()
        
        await token_repo.block_token(token_id, expires_at)
        
        key = f"blacklist:{token_id.value}"
        ttl = await redis_client.ttl(key)
        assert 3500 <= ttl <= 3600

    @pytest.mark.asyncio
    async def test_block_token_multiple_tokens(self, token_repo: ITokenRepository):
        token_id1 = ID("11111111-1111-1111-1111-111111111111")
        token_id2 = ID("22222222-2222-2222-2222-222222222222")
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()
        
        await token_repo.block_token(token_id1, expires_at)
        await token_repo.block_token(token_id2, expires_at)
        
        assert await token_repo.is_token_blocked(token_id1) is True
        assert await token_repo.is_token_blocked(token_id2) is True
    
    @pytest.mark.asyncio
    async def test_get_user_version_initial_zero(self, token_repo: ITokenRepository, user_id: ID):
        version = await token_repo.get_user_version(user_id)
        assert version == 0

    @pytest.mark.asyncio
    async def test_increment_user_version_first_time(self, token_repo: ITokenRepository, user_id: ID):
        new_version = await token_repo.increment_user_version(user_id)
        
        assert new_version == 1
        assert await token_repo.get_user_version(user_id) == 1

    @pytest.mark.asyncio
    async def test_increment_user_version_multiple_times(self, token_repo: ITokenRepository, user_id: ID):
        version1 = await token_repo.increment_user_version(user_id)
        version2 = await token_repo.increment_user_version(user_id)
        version3 = await token_repo.increment_user_version(user_id)
        
        assert version1 == 1
        assert version2 == 2
        assert version3 == 3
        assert await token_repo.get_user_version(user_id) == 3

    @pytest.mark.asyncio
    async def test_user_version_different_users(self, token_repo: ITokenRepository):
        user1 = ID("11111111-1111-1111-1111-111111111111")
        user2 = ID("22222222-2222-2222-2222-222222222222")
        
        await token_repo.increment_user_version(user1)
        await token_repo.increment_user_version(user1)
        await token_repo.increment_user_version(user2)
        
        assert await token_repo.get_user_version(user1) == 2
        assert await token_repo.get_user_version(user2) == 1