import pytest
import fakeredis
from src.modules.core.database import Base, engine, get_async_session
from src.modules.org.infrastructure.persistence.sqlal_project_repo import (
    SQLAL_ProjectRepository,
)
from src.modules.org.infrastructure.persistence.sqlal_board_repo import (
    SQLAL_BoardRepository,
)
from src.modules.card.infrastructure.persistence.sqlal_unit_of_work import (
    SQLAL_UnitOfWork,
)
from src.modules.auth.infrastructure.security.jwt_encoder import JWTEncoder
from src.modules.auth.infrastructure.cache.redis_token_repo import RedisTokenRepository
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.auth.domain.factories.user_factory import UserFactory
from src.modules.core.exceptions import (
    InvalidToken,
    ColumnNotFoundError,
    PermissionDenied,
)
from src.modules.org.domain.factories.organization_factory import OrgFactory
from src.modules.org.domain.factories.project_factory import PrjFactory
from src.modules.org.domain.factories.board_factory import BoardFactory
from src.modules.org.domain.factories.column_factory import ColumnFactory
from src.modules.card.application.create_card import CreateCardService
from src.modules.org.domain.value_objects.role import Role
from src.modules.card.domain.value_objects.id import ID


class TestCreateCard:
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
    async def owner_user(self, uow):
        user = UserFactory.create(
            email="owner@example.com", hashed_password="Super1@nSecretPassword"
        )
        await uow.users.add(user)
        await uow.commit()
        return user

    @pytest.fixture
    async def admin_user(self, uow):
        user = UserFactory.create(
            email="admin@example.com", hashed_password="Super1@nSecretPassword"
        )
        await uow.users.add(user)
        await uow.commit()
        return user

    @pytest.fixture
    async def member_user(self, uow):
        user = UserFactory.create(
            email="member@example.com", hashed_password="Super1@nSecretPassword"
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
    async def test_org(self, owner_user, admin_user, member_user, uow):
        org = OrgFactory.create(name="TestOrg")
        await uow.orgs.add(org)
        await uow.orgs.add_member(org.id, owner_user.id, Role("owner"))
        await uow.orgs.add_member(org.id, admin_user.id, Role("admin"))
        await uow.orgs.add_member(org.id, member_user.id, Role("member"))

        return org

    @pytest.fixture
    async def test_project(self, db_session, test_org):
        prj_repo = SQLAL_ProjectRepository(db_session)
        project = PrjFactory.create(
            name="Test Project", org_id=test_org.id.value, description="Project Desc"
        )
        await prj_repo.add(project)

        return project

    @pytest.fixture
    async def test_board(self, db_session, test_project):
        board_repo = SQLAL_BoardRepository(db_session)
        board = BoardFactory.create(
            name="Test Board", description="Board Desc", prj_id=test_project.id.value
        )
        await board_repo.add(board)
        return board

    @pytest.fixture
    async def test_column(self, uow: SQLAL_UnitOfWork, test_board):
        column = ColumnFactory.create(
            board_id=test_board.id.value, name="Test Column", order=1
        )
        await uow.columns.add(column)
        await uow.commit()
        return column

    @pytest.fixture
    async def create_card_service(self, uow, token_repo, decoder):
        return CreateCardService(uow, token_repo, decoder)

    async def test_create_card_success_by_owner(
        self, owner_user, test_column, create_card_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=owner_user.id)
        card = await create_card_service.execute(
            access_token,
            test_column.id.value,
            "Owner Card",
            "Desc",
            "high",
            "2025-12-31T23:59:59+00:00",
        )
        assert card.title.value == "Owner Card"
        assert card.column_id.value == test_column.id.value

    async def test_create_card_success_by_admin(
        self, admin_user, test_column, create_card_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=admin_user.id)
        card = await create_card_service.execute(
            access_token,
            test_column.id.value,
            "Admin Card",
            "Desc",
            "medium",
            "2025-12-31T23:59:59+00:00",
        )
        assert card.title.value == "Admin Card"

    async def test_create_card_permission_denied_for_member(
        self, member_user, test_column, create_card_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=member_user.id)
        with pytest.raises(PermissionDenied):
            await create_card_service.execute(
                access_token,
                test_column.id.value,
                "Member Card",
                "Desc",
                "low",
                "2025-12-31T23:59:59+00:00",
            )

    async def test_create_card_column_not_found(
        self, owner_user, create_card_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=owner_user.id)
        with pytest.raises(ColumnNotFoundError):
            await create_card_service.execute(
                access_token,
                ID().value,
                "Card",
                "Desc",
                "high",
                "2025-12-31T23:59:59+00:00",
            )

    async def test_create_card_invalid_token(self, test_column, create_card_service):
        with pytest.raises(InvalidToken):
            await create_card_service.execute(
                "invalid_token",
                test_column.id.value,
                "Card",
                "Desc",
                "high",
                "2025-12-31T23:59:59+00:00",
            )
