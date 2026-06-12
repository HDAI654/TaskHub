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
from src.modules.auth.infrastructure.security.password_hasher import PasswordHasher
from src.modules.auth.infrastructure.cache.redis_token_repo import RedisTokenRepository
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.auth.domain.factories.user_factory import UserFactory
from src.modules.core.exceptions import (
    CardNotFoundError,
    PermissionDenied,
)
from src.modules.org.domain.factories.organization_factory import OrgFactory
from src.modules.org.domain.factories.project_factory import PrjFactory
from src.modules.org.domain.factories.board_factory import BoardFactory
from src.modules.org.domain.factories.column_factory import ColumnFactory
from src.modules.card.application.get_card_assignees import GetCardAssigneesService
from src.modules.card.application.add_assignee import AddAssigneeService
from src.modules.card.application.create_card import CreateCardService
from src.modules.org.domain.value_objects.role import Role
from src.modules.card.domain.value_objects.id import ID


class TestGetCardAssignees:
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
    async def assignee_user1(self, uow, user_hashed_password):
        user = UserFactory.create(
            email="assignee1@example.com",
            hashed_password=user_hashed_password,
        )
        await uow.users.add(user)
        await uow.commit()
        return user

    @pytest.fixture
    async def assignee_user2(self, uow, user_hashed_password):
        user = UserFactory.create(
            email="assignee2@example.com",
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
    async def test_org(self, owner_user, admin_user, member_user, uow):
        org = OrgFactory.create(name="Test Org")
        await uow.orgs.add(org)
        await uow.orgs.add_member(org.id, owner_user.id, Role("owner"))
        await uow.orgs.add_member(org.id, admin_user.id, Role("admin"))
        await uow.orgs.add_member(org.id, member_user.id, Role("member"))
        await uow.commit()
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
    async def test_column(self, uow, test_board):
        column = ColumnFactory.create(
            board_id=test_board.id.value, name="Test Column", order=1
        )
        await uow.columns.add(column)
        await uow.commit()
        return column

    @pytest.fixture
    async def create_card_service(self, uow, token_repo, decoder):
        return CreateCardService(uow, token_repo, decoder)

    @pytest.fixture
    async def add_assignee_service(self, uow, token_repo, decoder):
        return AddAssigneeService(uow, token_repo, decoder)

    @pytest.fixture
    async def get_card_assignees_service(self, uow, token_repo, decoder):
        return GetCardAssigneesService(uow, token_repo, decoder)

    @pytest.fixture
    async def sample_card(self, owner_user, test_column, create_card_service, encoder):
        access_token = encoder.create_access_token(user_id=owner_user.id)
        card = await create_card_service.execute(
            access_token,
            test_column.id.value,
            "Test Card",
            "Test Description",
            "high",
            "2025-12-31T23:59:59+00:00",
        )
        return card

    @pytest.fixture
    async def card_with_assignees(
        self,
        owner_user,
        assignee_user1,
        assignee_user2,
        sample_card,
        add_assignee_service,
        encoder,
    ):
        access_token = encoder.create_access_token(user_id=owner_user.id)
        await add_assignee_service.execute(
            access_token, sample_card.id.value, assignee_user1.id.value
        )
        await add_assignee_service.execute(
            access_token, sample_card.id.value, assignee_user2.id.value
        )
        return sample_card

    async def test_get_card_assignees_success_by_owner(
        self,
        owner_user,
        card_with_assignees,
        assignee_user1,
        assignee_user2,
        get_card_assignees_service,
        encoder,
    ):
        access_token = encoder.create_access_token(user_id=owner_user.id)
        assignees = await get_card_assignees_service.execute(
            access_token, card_with_assignees.id.value
        )

        assert len(assignees) == 2
        assignee_ids = {a.id.value for a in assignees}
        assert assignee_user1.id.value in assignee_ids
        assert assignee_user2.id.value in assignee_ids

    async def test_get_card_assignees_success_by_admin(
        self,
        admin_user,
        card_with_assignees,
        assignee_user1,
        assignee_user2,
        get_card_assignees_service,
        encoder,
    ):
        access_token = encoder.create_access_token(user_id=admin_user.id)
        assignees = await get_card_assignees_service.execute(
            access_token, card_with_assignees.id.value
        )

        assert len(assignees) == 2

    async def test_get_card_assignees_permission_denied_for_member(
        self, member_user, card_with_assignees, get_card_assignees_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=member_user.id)
        with pytest.raises(PermissionDenied) as exc_info:
            await get_card_assignees_service.execute(
                access_token, card_with_assignees.id.value
            )
        assert "Only owner or admin can view assignees" in str(exc_info.value)

    async def test_get_card_assignees_permission_denied_for_non_member(
        self, non_member_user, card_with_assignees, get_card_assignees_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=non_member_user.id)
        with pytest.raises(PermissionDenied) as exc_info:
            await get_card_assignees_service.execute(
                access_token, card_with_assignees.id.value
            )
        assert "Only owner or admin can view assignees" in str(exc_info.value)

    async def test_get_card_assignees_empty(
        self, owner_user, sample_card, get_card_assignees_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=owner_user.id)
        assignees = await get_card_assignees_service.execute(
            access_token, sample_card.id.value
        )
        assert assignees == []

    async def test_get_card_assignees_card_not_found(
        self, owner_user, get_card_assignees_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=owner_user.id)
        with pytest.raises(CardNotFoundError):
            await get_card_assignees_service.execute(access_token, ID().value)

    async def test_get_card_assignees_skips_deleted_users(
        self,
        owner_user,
        assignee_user1,
        sample_card,
        add_assignee_service,
        get_card_assignees_service,
        encoder,
        uow,
    ):
        # Add two assignees
        access_token = encoder.create_access_token(user_id=owner_user.id)
        await add_assignee_service.execute(
            access_token, sample_card.id.value, assignee_user1.id.value
        )
        # Add a second assignee that will be deleted
        temp_user = UserFactory.create(
            email="temp@example.com", hashed_password="hashed"
        )
        await uow.users.add(temp_user)
        await uow.commit()
        await add_assignee_service.execute(
            access_token, sample_card.id.value, temp_user.id.value
        )

        # Delete the temp user (simulate user being removed)
        await uow.users.delete(temp_user.id)
        await uow.commit()

        # Get assignees – should only return assignee_user1, skipping the deleted user
        assignees = await get_card_assignees_service.execute(
            access_token, sample_card.id.value
        )
        assert len(assignees) == 1
        assert assignees[0].id.value == assignee_user1.id.value
