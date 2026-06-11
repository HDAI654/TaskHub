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
from src.modules.auth.domain.factories.user_factory import UserFactory
from src.modules.core.exceptions import (
    InvalidToken,
    ColumnNotFoundError,
    PermissionDenied,
)
from src.modules.org.application.create_org import CreateOrgService
from src.modules.org.application.create_project import CreateProjectService
from src.modules.org.application.create_board import CreateBoardService
from src.modules.org.application.create_column import CreateColumnService
from src.modules.org.application.get_column import GetColumnService
from src.modules.org.domain.value_objects.role import Role


class TestGetColumn:
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
    async def owner_user(self, uow, user_hashed_password):
        user = UserFactory.create(
            email="owner@example.com",
            hashed_password=user_hashed_password,
        )
        await uow.users.add(user)
        await uow.commit()
        return user

    @pytest.fixture
    async def member_user(self, uow, user_hashed_password):
        user = UserFactory.create(
            email="member@example.com",
            hashed_password=user_hashed_password,
        )
        await uow.users.add(user)
        await uow.commit()
        return user

    @pytest.fixture
    async def non_member_user(self, uow, user_hashed_password):
        user = UserFactory.create(
            email="nonmember@example.com",
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
    async def create_org_service(self, uow, token_repo, decoder):
        return CreateOrgService(uow, token_repo, decoder)

    @pytest.fixture
    async def test_org(self, owner_user, member_user, create_org_service, encoder):
        owner_token = encoder.create_access_token(user_id=owner_user.id)
        org = await create_org_service.execute(owner_token, "Test Org")
        await create_org_service.uow.orgs.add_member(
            org.id, member_user.id, Role("member")
        )
        await create_org_service.uow.commit()
        return org

    @pytest.fixture
    async def create_project_service(self, uow, token_repo, decoder):
        return CreateProjectService(uow, token_repo, decoder)

    @pytest.fixture
    async def test_project(self, owner_user, test_org, create_project_service, encoder):
        access_token = encoder.create_access_token(user_id=owner_user.id)
        project = await create_project_service.execute(
            access_token, test_org.id.value, "Test Project", "Desc"
        )
        return project

    @pytest.fixture
    async def create_board_service(self, uow, token_repo, decoder):
        return CreateBoardService(uow, token_repo, decoder)

    @pytest.fixture
    async def test_board(self, owner_user, test_project, create_board_service, encoder):
        access_token = encoder.create_access_token(user_id=owner_user.id)
        board = await create_board_service.execute(
            access_token, test_project.id.value, "Test Board", "Desc"
        )
        return board

    @pytest.fixture
    async def create_column_service(self, uow, token_repo, decoder):
        return CreateColumnService(uow, token_repo, decoder)

    @pytest.fixture
    async def get_column_service(self, uow, token_repo, decoder):
        return GetColumnService(uow, token_repo, decoder)

    @pytest.fixture
    async def sample_column(
        self, owner_user, test_board, create_column_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=owner_user.id)
        column = await create_column_service.execute(
            access_token, test_board.id.value, "Test Column", 1
        )
        return column

    async def test_get_column_success_by_owner(
        self, owner_user, sample_column, get_column_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=owner_user.id)
        column = await get_column_service.execute(access_token, sample_column.id.value)
        assert column.id.value == sample_column.id.value

    async def test_get_column_success_by_member(
        self, member_user, sample_column, get_column_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=member_user.id)
        column = await get_column_service.execute(access_token, sample_column.id.value)
        assert column.id.value == sample_column.id.value

    async def test_get_column_permission_denied_for_non_member(
        self, non_member_user, sample_column, get_column_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=non_member_user.id)
        with pytest.raises(PermissionDenied):
            await get_column_service.execute(access_token, sample_column.id.value)

    async def test_get_column_not_found(self, owner_user, get_column_service, encoder):
        access_token = encoder.create_access_token(user_id=owner_user.id)
        with pytest.raises(ColumnNotFoundError):
            await get_column_service.execute(access_token, "non-existent-id")

    async def test_get_column_invalid_token(self, get_column_service, sample_column):
        with pytest.raises(InvalidToken):
            await get_column_service.execute("invalid_token", sample_column.id.value)
