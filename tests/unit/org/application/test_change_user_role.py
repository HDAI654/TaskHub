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
from src.modules.core.exceptions import (
    OrgNotFoundError,
    PermissionDenied,
    MemberNotFoundError,
)
from src.modules.org.application.create_org import CreateOrgService
from src.modules.org.application.add_member import AddMemberService
from src.modules.org.application.change_user_role import ChangeUserRoleService


class TestChangeUserRole:
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
    async def owner(self, uow, user_hashed_password):
        user = UserFactory.create(
            email="owner@example.com",
            hashed_password=user_hashed_password,
        )
        await uow.users.add(user)
        await uow.commit()
        return user

    @pytest.fixture
    async def member(self, uow, user_hashed_password):
        user = UserFactory.create(
            email="member@example.com",
            hashed_password=user_hashed_password,
        )
        await uow.users.add(user)
        await uow.commit()
        return user

    @pytest.fixture
    async def regular_user(self, uow, user_hashed_password):
        user = UserFactory.create(
            email="regular@example.com",
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
    async def change_role_service(self, uow, token_repo, decoder):
        return ChangeUserRoleService(uow, token_repo, decoder)

    @pytest.fixture
    async def org(self, owner, create_service, encoder):
        access_token = encoder.create_access_token(user_id=owner.id)
        org = await create_service.execute(access_token, "Test Org")
        return org

    async def test_change_role_success(
        self, owner, member, change_role_service, add_member_service, encoder, org
    ):
        access_token = encoder.create_access_token(user_id=owner.id)
        await add_member_service.execute(
            access_token, org.id.value, member.id.value, "member"
        )
        await change_role_service.execute(
            access_token, org.id.value, member.id.value, "admin"
        )
        role = await change_role_service.uow.orgs.get_user_role(org.id, member.id)
        assert role is not None
        assert role.value == "admin"

    async def test_change_role_not_owner(
        self, owner, regular_user, change_role_service, add_member_service, encoder, org
    ):
        owner_token = encoder.create_access_token(user_id=owner.id)
        member_token = encoder.create_access_token(user_id=regular_user.id)
        await add_member_service.execute(
            owner_token, org.id.value, regular_user.id.value, "member"
        )
        with pytest.raises(PermissionDenied):
            await change_role_service.execute(
                member_token, org.id.value, regular_user.id.value, "admin"
            )

    async def test_change_role_member_not_found(
        self, owner, change_role_service, encoder, org
    ):
        access_token = encoder.create_access_token(user_id=owner.id)
        with pytest.raises(MemberNotFoundError):
            await change_role_service.execute(
                access_token, org.id.value, ID().value, "admin"
            )

    async def test_change_role_org_not_found(
        self, owner, member, change_role_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=owner.id)
        with pytest.raises(OrgNotFoundError):
            await change_role_service.execute(
                access_token, ID().value, member.id.value, "admin"
            )
