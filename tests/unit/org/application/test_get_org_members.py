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
from src.modules.core.exceptions import OrgNotFoundError
from src.modules.org.application.create_org import CreateOrgService
from src.modules.org.application.add_member import AddMemberService
from src.modules.org.application.get_org_members import GetOrgMembersService
from src.modules.org.domain.value_objects.role import Role


class TestGetOrgMembers:
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
    async def second_user(self, uow, user_hashed_password):
        user = UserFactory.create(
            email="member2@example.com",
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
    async def add_member_service(self, uow, token_repo, decoder):
        return AddMemberService(uow, token_repo, decoder)

    @pytest.fixture
    async def get_members_service(self, uow, token_repo, decoder):
        return GetOrgMembersService(uow, token_repo, decoder)

    @pytest.fixture
    async def org(self, user, create_service, encoder):
        access_token = encoder.create_access_token(user_id=user.id)
        org = await create_service.execute(access_token, "Test Org")
        return org

    async def test_get_members_success(
        self, user, second_user, get_members_service, add_member_service, encoder, org
    ):
        access_token = encoder.create_access_token(user_id=user.id)
        await add_member_service.execute(
            access_token, org.id.value, second_user.id.value, "member"
        )

        members = await get_members_service.execute(access_token, org.id.value)

        assert len(members) == 2
        member_roles = {m["user_id"]: m["role"] for m in members}
        assert member_roles[user.id.value] == "owner"
        assert member_roles[second_user.id.value] == "member"

    async def test_get_members_with_role_filter(
        self, user, second_user, get_members_service, add_member_service, encoder, org
    ):
        access_token = encoder.create_access_token(user_id=user.id)
        await add_member_service.execute(
            access_token, org.id.value, second_user.id.value, "member"
        )

        owners = await get_members_service.execute(
            access_token, org.id.value, role="owner"
        )
        members = await get_members_service.execute(
            access_token, org.id.value, role="member"
        )

        assert len(owners) == 1
        assert owners[0]["user_id"] == user.id.value
        assert len(members) == 1
        assert members[0]["user_id"] == second_user.id.value

    async def test_get_members_org_not_found(self, user, get_members_service, encoder):
        access_token = encoder.create_access_token(user_id=user.id)
        with pytest.raises(OrgNotFoundError):
            await get_members_service.execute(access_token, ID().value)
