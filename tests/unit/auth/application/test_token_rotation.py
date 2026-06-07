import pytest
import fakeredis
from uuid import uuid4
from datetime import datetime, timedelta, timezone
import jwt
import fakeredis
from src.modules.auth.domain.ports.token_repo_interface import ITokenRepository
from src.modules.auth.infrastructure.cache.redis_token_repo import RedisTokenRepository
from src.modules.auth.domain.ports.unit_of_work_interface import IUnitOfWork
from src.modules.auth.infrastructure.persistence.sqlal_unit_of_work import (
    SQLAL_UnitOfWork,
)
from src.modules.auth.infrastructure.persistence.models import Base
from src.modules.auth.infrastructure.security.jwt_encoder import JWTEncoder
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.core.database import get_async_session, engine
from src.modules.auth.application.token_rotation import TokenRotationService
from src.modules.auth.domain.factories.user_factory import UserFactory
from src.modules.auth.infrastructure.security.password_hasher import PasswordHasher
from src.modules.core.conf import Config
from src.modules.auth.exceptions import InvalidToken


class TestTokenRotation:
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
    async def encoder(self):
        return JWTEncoder()

    @pytest.fixture
    async def decoder(self):
        return JWTDecoder()

    @pytest.fixture
    async def user_refresh_token(self, encoder, user):
        return encoder.create_refresh_token(user_id=user.id)

    @pytest.fixture
    async def service(self, uow, token_repo, decoder, encoder):
        return TokenRotationService(
            uow=uow, token_repo=token_repo, jwt_decoder=decoder, jwt_encoder=encoder
        )

    async def test_rotation_success(self, service, user_refresh_token):
        new_access_token, new_refresh_token = await service.execute(
            refresh_token=user_refresh_token,
        )
        assert isinstance(new_access_token, str) and new_refresh_token is None

    async def test_rotation_success_with_new_refresh_token(self, service, user):
        exp = datetime.now(timezone.utc) + timedelta(
            minutes=Config.ROTATE_THRESHOLD_MINUTES
        )
        payload = {
            "sub": user.id.value,
            "jti": str(uuid4()),
            "ver": 0,
            "exp": exp,
            "type": "refresh",
            "iat": datetime.now(timezone.utc).timestamp(),
        }
        refresh_token = jwt.encode(
            payload, Config.JWT_PRIVATE_KEY, algorithm=Config.JWT_ALGORITHM
        )
        new_access_token, new_refresh_token = await service.execute(
            refresh_token=refresh_token,
        )
        assert isinstance(new_access_token, str) and isinstance(new_refresh_token, str)

    async def test_rotation_with_invalid_version(self, service, user, encoder):
        refresh_token = encoder.create_refresh_token(user_id=user.id, version=100)
        with pytest.raises(InvalidToken):
            await service.execute(
                refresh_token=refresh_token,
            )
