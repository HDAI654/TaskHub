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
    MemberDuplicateError,
)
from src.modules.org.application.create_org import CreateOrgService
from src.modules.org.application.add_member import AddMemberService
from src.modules.org.domain.value_objects.role import Role


class TestAddMember:
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
    async def admin(self, uow, user_hashed_password):
        user = UserFactory.create(
            email="admin@example.com",
            hashed_password=user_hashed_password,
        )
        await uow.users.add(user)
        await uow.commit()
        return user

    @pytest.fixture
    async def member_to_add(self, uow, user_hashed_password):
        user = UserFactory.create(
            email="newmember@example.com",
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
    async def org(self, owner, create_service, encoder):
        access_token = encoder.create_access_token(user_id=owner.id)
        org = await create_service.execute(access_token, "Test Org")
        return org

    @pytest.fixture
    async def org_with_admin(self, admin, create_service, encoder):
        access_token = encoder.create_access_token(user_id=admin.id)
        org = await create_service.execute(access_token, "Test Org 2")
        return org

    async def test_add_member_success_by_owner(
        self, owner, member_to_add, add_member_service, encoder, org
    ):
        access_token = encoder.create_access_token(user_id=owner.id)
        await add_member_service.execute(
            access_token, org.id.value, member_to_add.id.value, "member"
        )
        role = await add_member_service.uow.orgs.get_user_role(org.id, member_to_add.id)
        assert role is not None
        assert role.value == "member"

    async def test_add_member_success_by_admin(
        self, admin, member_to_add, add_member_service, encoder, org_with_admin
    ):
        access_token = encoder.create_access_token(user_id=admin.id)
        await add_member_service.execute(
            access_token, org_with_admin.id.value, member_to_add.id.value, "member"
        )
        role = await add_member_service.uow.orgs.get_user_role(
            org_with_admin.id, member_to_add.id
        )
        assert role is not None
        assert role.value == "member"

    async def test_add_member_insufficient_permission(
        self, regular_user, member_to_add, add_member_service, encoder, org
    ):
        access_token = encoder.create_access_token(user_id=regular_user.id)
        with pytest.raises(PermissionDenied):
            await add_member_service.execute(
                access_token, org.id.value, member_to_add.id.value, "member"
            )

    async def test_add_member_user_not_found(
        self, owner, add_member_service, encoder, org
    ):
        access_token = encoder.create_access_token(user_id=owner.id)
        with pytest.raises(MemberNotFoundError):
            await add_member_service.execute(
                access_token, org.id.value, ID().value, "member"
            )

    async def test_add_member_already_exists(
        self, owner, member_to_add, add_member_service, encoder, org
    ):
        access_token = encoder.create_access_token(user_id=owner.id)
        await add_member_service.execute(
            access_token, org.id.value, member_to_add.id.value, "member"
        )
        with pytest.raises(MemberDuplicateError):
            await add_member_service.execute(
                access_token, org.id.value, member_to_add.id.value, "member"
            )

    async def test_add_member_org_not_found(
        self, owner, member_to_add, add_member_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=owner.id)
        with pytest.raises(OrgNotFoundError):
            await add_member_service.execute(
                access_token, ID().value, member_to_add.id.value, "member"
            )
