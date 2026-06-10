import pytest
import fakeredis
from src.modules.core.database import Base, engine, get_async_session
from src.modules.org.infrastructure.persistence.sqlal_unit_of_work import (
    SQLAL_UnitOfWork,
)
from src.modules.auth.infrastructure.security.jwt_encoder import JWTEncoder
from src.modules.auth.infrastructure.security.password_hasher import PasswordHasher
from src.modules.auth.infrastructure.cache.redis_token_repo import RedisTokenRepository
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.org.domain.value_objects.id import ID
from src.modules.auth.domain.factories.user_factory import UserFactory
from src.modules.core.exceptions import InvalidToken, UserNotFoundError
from src.modules.org.application.create_org import CreateOrgService
from src.modules.org.application.get_user_orgs import GetUserOrgsService
from src.modules.org.domain.value_objects.role import Role


class TestGetUserOrgs:
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
    async def uow(self, db_session):
        return SQLAL_UnitOfWork(db_session)

    @pytest.fixture
    async def user_raw_password(self):
        return "Super1@nSecretPassword"

    @pytest.fixture
    async def hasher(self):
        return PasswordHasher()

    @pytest.fixture
    async def user_hashed_password(self, user_raw_password, hasher):
        return hasher.hash(user_raw_password)

    @pytest.fixture
    async def user(self, uow, user_hashed_password):
        user = UserFactory.create(
            email="user@example.com",
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
    async def token_repo(self, redis_client):
        return RedisTokenRepository(redis_client)

    @pytest.fixture
    async def encoder(self):
        return JWTEncoder()

    @pytest.fixture
    async def decoder(self):
        return JWTDecoder()

    @pytest.fixture
    async def create_service(self, uow, token_repo, decoder):
        return CreateOrgService(uow, token_repo, decoder)

    @pytest.fixture
    async def get_user_orgs_service(self, uow, token_repo, decoder):
        return GetUserOrgsService(uow, token_repo, decoder)

    async def test_get_user_orgs_success(
        self, user, create_service, get_user_orgs_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=user.id)
        org1 = await create_service.execute(access_token, "Org 1")
        org2 = await create_service.execute(access_token, "Org 2")

        orgs = await get_user_orgs_service.execute(access_token)

        assert len(orgs) == 2
        org_ids = [org["organization_id"] for org in orgs]
        assert org1.id.value in org_ids
        assert org2.id.value in org_ids

    async def test_get_user_orgs_empty(self, user, get_user_orgs_service, encoder):
        access_token = encoder.create_access_token(user_id=user.id)
        orgs = await get_user_orgs_service.execute(access_token)
        assert orgs == []

    async def test_get_user_orgs_user_not_found(self, get_user_orgs_service, encoder):
        access_token = encoder.create_access_token(user_id=ID())
        with pytest.raises(UserNotFoundError):
            await get_user_orgs_service.execute(access_token)

    async def test_get_user_orgs_invalid_token(self, user, get_user_orgs_service):
        with pytest.raises(InvalidToken):
            await get_user_orgs_service.execute("invalid_token")

    async def test_get_user_orgs_invalid_version(
        self, user, get_user_orgs_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=user.id, version=100)
        with pytest.raises(InvalidToken):
            await get_user_orgs_service.execute(access_token)
