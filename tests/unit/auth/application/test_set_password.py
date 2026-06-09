import pytest
import fakeredis
from src.modules.auth.domain.ports.token_repo_interface import ITokenRepository
from src.modules.auth.infrastructure.cache.redis_token_repo import RedisTokenRepository
from src.modules.auth.domain.ports.unit_of_work_interface import IUnitOfWork
from src.modules.auth.infrastructure.persistence.sqlal_unit_of_work import (
    SQLAL_UnitOfWork,
)
from src.modules.core.database import Base
from src.modules.core.database import get_async_session, engine
from src.modules.auth.application.set_password import SetPassService
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.auth.infrastructure.security.jwt_encoder import JWTEncoder
from src.modules.auth.infrastructure.security.password_hasher import PasswordHasher
from src.modules.auth.domain.factories.user_factory import UserFactory
from src.modules.auth.exceptions import InvalidOldPassword, InvalidToken


class TestSetPass:
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
        return "SuperSecretPassword"

    @pytest.fixture
    async def hasher(self):
        return PasswordHasher()

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
    async def decoder(self):
        return JWTDecoder()

    @pytest.fixture
    async def encoder(self):
        return JWTEncoder()

    @pytest.fixture
    async def user_access_token(self, user, encoder):
        return encoder.create_access_token(user_id=user.id)

    @pytest.fixture
    async def service(self, uow, token_repo, decoder, encoder, hasher):
        return SetPassService(
            uow=uow,
            token_repo=token_repo,
            jwt_decoder=decoder,
            jwt_encoder=encoder,
            password_hasher=hasher,
        )

    async def test_set_pass_success(
        self,
        user,
        user_raw_password,
        user_access_token,
        service,
        uow,
        hasher,
        token_repo,
    ):
        new_access_token, new_refresh_token = await service.execute(
            access_token=user_access_token,
            old_password=user_raw_password,
            new_password="NewSuper25@Secret",
        )
        assert isinstance(new_access_token, str) and isinstance(new_refresh_token, str)

        user = await uow.users.get_by_id(user.id)
        assert hasher.verify(
            plain="NewSuper25@Secret", hashed=user.hashed_password.value
        )

        # Password change should change user version
        assert await token_repo.get_user_version(user.id) == 1

    async def test_set_pass_with_invalid_password(self, user_access_token, service):

        with pytest.raises(InvalidOldPassword):
            await service.execute(
                access_token=user_access_token,
                old_password="invalid_old_password:)",
                new_password="NewSuper25@Secret",
            )

    async def test_set_pass_with_invalid_version(
        self, service, user, encoder, user_raw_password
    ):
        access_token = encoder.create_access_token(user_id=user.id, version=100)
        with pytest.raises(InvalidToken):
            await service.execute(
                access_token=access_token,
                old_password=user_raw_password,
                new_password="NewSuper25@Secret",
            )
