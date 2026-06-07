import pytest
import fakeredis
from src.modules.auth.domain.ports.unit_of_work_interface import IUnitOfWork
from src.modules.auth.infrastructure.persistence.sqlal_unit_of_work import SQLAL_UnitOfWork
from src.modules.auth.application.logout import LogoutService
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.auth.infrastructure.security.jwt_encoder import JWTEncoder
from src.modules.auth.infrastructure.security.password_hasher import PasswordHasher
from src.modules.auth.domain.ports.unit_of_work_interface import IUnitOfWork
from src.modules.auth.domain.ports.token_repo_interface import ITokenRepository
from src.modules.auth.infrastructure.cache.redis_token_repo import RedisTokenRepository
from src.modules.auth.infrastructure.persistence.models import Base
from src.modules.core.database import get_async_session, engine
from src.modules.auth.domain.factories.user_factory import UserFactory
from src.modules.auth.domain.value_objects.id import ID
from src.modules.auth.exceptions import InvalidToken

class TestLogout:
    @pytest.fixture(autouse=True)
    async def setup_db(self):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    @pytest.fixture
    async def db_session(self):
        async for session in get_async_session():
            yield session
            await session.rollback()
            break

    @pytest.fixture
    async def uow(self, db_session) -> IUnitOfWork:
        return SQLAL_UnitOfWork(db_session)

    @pytest.fixture
    async def user_raw_password(self):
        return "Super1@nSecretPassword"

    @pytest.fixture
    async def user_hashed_password(self, user_raw_password, hasher):
        return hasher.hash(user_raw_password)

    @pytest.fixture
    async def user(self, uow, user_hashed_password):
        user = UserFactory.create(
            email="mynewexampleemail@me.he",
            hashed_password=user_hashed_password,
        )
        await uow.users.add(user)
        await uow.commit()
        return user
    
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
    async def encoder(self):
        return JWTEncoder()

    @pytest.fixture
    async def decoder(self):
        return JWTDecoder()

    @pytest.fixture
    async def hasher(self):
        return PasswordHasher()
    
    @pytest.fixture
    async def service(self, uow, decoder, token_repo):
        return LogoutService(
            uow=uow,
            token_repo=token_repo,
            jwt_decoder=decoder,
        )

    async def test_logout_success(
        self, user, service, encoder, token_repo, decoder
        ):
        access_token = encoder.create_access_token(
            user_id=user.id
        )
        refresh_token = encoder.create_refresh_token(
            user_id=user.id
        )
        await service.execute(
            access_token,
            refresh_token,
        )

        access_payload = decoder.decode_token(access_token)
        refresh_payload = decoder.decode_token(refresh_token)

        assert await token_repo.is_token_blocked(ID(access_payload["jti"])) is True
        assert await token_repo.is_token_blocked(ID(refresh_payload["jti"])) is True
    
    async def test_logout_with_invalid_tokens(
        self, user, service, encoder
        ):
        access_token = encoder.create_access_token(
            user_id=user.id
        )
        refresh_token = encoder.create_refresh_token(
            user_id=ID()
        )

        with pytest.raises(InvalidToken):
            await service.execute(
                access_token,
                refresh_token,
            )
