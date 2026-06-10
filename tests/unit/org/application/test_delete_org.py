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
from src.modules.core.exceptions import OrgNotFoundError, PermissionDenied
from src.modules.org.application.create_org import CreateOrgService
from src.modules.org.application.delete_org import DeleteOrgService


class TestDeleteOrg:
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
            email="owner@example.com",
            hashed_password=user_hashed_password,
        )
        await uow.users.add(user)
        await uow.commit()
        return user

    @pytest.fixture
    async def second_user(self, uow, user_hashed_password):
        user = UserFactory.create(
            email="member@example.com",
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
    async def delete_service(self, uow, token_repo, decoder):
        return DeleteOrgService(uow, token_repo, decoder)

    @pytest.fixture
    async def org(self, user, create_service, encoder):
        access_token = encoder.create_access_token(user_id=user.id)
        org = await create_service.execute(access_token, "Test Org")
        return org

    async def test_delete_org_success(self, user, delete_service, encoder, org):
        access_token = encoder.create_access_token(user_id=user.id)
        await delete_service.execute(access_token, org.id.value)
        with pytest.raises(OrgNotFoundError):
            await delete_service.uow.orgs.get_by_id(org.id)

    async def test_delete_org_not_owner(
        self, second_user, delete_service, encoder, org
    ):
        access_token = encoder.create_access_token(user_id=second_user.id)
        with pytest.raises(PermissionDenied):
            await delete_service.execute(access_token, org.id.value)

    async def test_delete_org_not_found(self, user, delete_service, encoder):
        access_token = encoder.create_access_token(user_id=user.id)
        with pytest.raises(OrgNotFoundError):
            await delete_service.execute(access_token, ID().value)
