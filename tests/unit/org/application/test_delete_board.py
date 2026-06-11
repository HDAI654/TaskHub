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
    BoardNotFoundError,
    PermissionDenied,
)
from src.modules.org.application.create_org import CreateOrgService
from src.modules.org.application.create_project import CreateProjectService
from src.modules.org.application.create_board import CreateBoardService
from src.modules.org.application.delete_board import DeleteBoardService
from src.modules.org.domain.value_objects.role import Role


class TestDeleteBoard:
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
    async def admin_user(self, uow, user_hashed_password):
        user = UserFactory.create(
            email="admin@example.com",
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
    async def test_org(
        self, owner_user, admin_user, member_user, create_org_service, encoder
    ):
        owner_token = encoder.create_access_token(user_id=owner_user.id)
        org = await create_org_service.execute(owner_token, "Test Org")
        await create_org_service.uow.orgs.add_member(
            org.id, admin_user.id, Role("admin")
        )
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
            access_token, test_org.id.value, "Test Project", "Project Desc"
        )
        return project

    @pytest.fixture
    async def create_board_service(self, uow, token_repo, decoder):
        return CreateBoardService(uow, token_repo, decoder)

    @pytest.fixture
    async def delete_board_service(self, uow, token_repo, decoder):
        return DeleteBoardService(uow, token_repo, decoder)

    @pytest.fixture
    async def sample_board(
        self, owner_user, test_project, create_board_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=owner_user.id)
        board = await create_board_service.execute(
            access_token, test_project.id.value, "To Delete", "Desc"
        )
        return board

    async def test_delete_board_success_by_owner(
        self, owner_user, sample_board, delete_board_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=owner_user.id)
        await delete_board_service.execute(access_token, sample_board.id.value)
        with pytest.raises(BoardNotFoundError):
            await delete_board_service.uow.boards.get_by_id(sample_board.id)

    async def test_delete_board_success_by_admin(
        self, admin_user, sample_board, delete_board_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=admin_user.id)
        await delete_board_service.execute(access_token, sample_board.id.value)
        with pytest.raises(BoardNotFoundError):
            await delete_board_service.uow.boards.get_by_id(sample_board.id)

    async def test_delete_board_permission_denied_for_member(
        self, member_user, sample_board, delete_board_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=member_user.id)
        with pytest.raises(PermissionDenied):
            await delete_board_service.execute(access_token, sample_board.id.value)

    async def test_delete_board_not_found(
        self, owner_user, delete_board_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=owner_user.id)
        with pytest.raises(BoardNotFoundError):
            await delete_board_service.execute(access_token, "non-existent-id")

    async def test_delete_board_invalid_token(self, delete_board_service, sample_board):
        with pytest.raises(InvalidToken):
            await delete_board_service.execute("invalid_token", sample_board.id.value)
