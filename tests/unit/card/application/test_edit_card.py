import pytest
import fakeredis
from datetime import datetime, timezone
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
    InvalidToken,
    CardNotFoundError,
    ColumnNotFoundError,
    PermissionDenied,
    NoChangesError,
)
from src.modules.org.domain.factories.organization_factory import OrgFactory
from src.modules.org.domain.factories.project_factory import PrjFactory
from src.modules.org.domain.factories.board_factory import BoardFactory
from src.modules.org.domain.factories.column_factory import ColumnFactory
from src.modules.card.application.edit_card import EditCardService
from src.modules.card.application.create_card import CreateCardService
from src.modules.card.domain.factories.card_factory import CardFactory
from src.modules.org.domain.value_objects.role import Role
from src.modules.card.domain.value_objects.id import ID


class TestEditCard:
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
    async def test_org(self, owner_user, admin_user, member_user, uow):
        org = OrgFactory.create(name="TestOrg")
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
    async def second_column(self, uow, test_board):
        column = ColumnFactory.create(
            board_id=test_board.id.value, name="Second Column", order=2
        )
        await uow.columns.add(column)
        await uow.commit()
        return column

    @pytest.fixture
    async def create_card_service(self, uow, token_repo, decoder):
        return CreateCardService(uow, token_repo, decoder)

    @pytest.fixture
    async def edit_card_service(self, uow, token_repo, decoder):
        return EditCardService(uow, token_repo, decoder)

    @pytest.fixture
    async def sample_card(self, owner_user, test_column, create_card_service, encoder):
        access_token = encoder.create_access_token(user_id=owner_user.id)
        card = await create_card_service.execute(
            access_token,
            test_column.id.value,
            "Original Card",
            "Original Description",
            "high",
            "2025-12-31T23:59:59+00:00",
        )
        return card

    async def test_edit_card_title_success_by_owner(
        self, owner_user, sample_card, edit_card_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=owner_user.id)
        new_title = "Updated Card Title"

        await edit_card_service.execute(
            access_token, sample_card.id.value, new_title=new_title
        )

        updated = await edit_card_service.uow.cards.get_by_id(sample_card.id)
        assert updated.title.value == new_title
        assert updated.description.value == "Original Description"
        assert updated.priority.value == "high"

    async def test_edit_card_description_success_by_admin(
        self, admin_user, sample_card, edit_card_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=admin_user.id)
        new_description = "Admin Updated Description"

        await edit_card_service.execute(
            access_token, sample_card.id.value, new_description=new_description
        )

        updated = await edit_card_service.uow.cards.get_by_id(sample_card.id)
        assert updated.description.value == new_description
        assert updated.title.value == "Original Card"

    async def test_edit_card_priority_success_by_owner(
        self, owner_user, sample_card, edit_card_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=owner_user.id)
        new_priority = "urgent"

        await edit_card_service.execute(
            access_token, sample_card.id.value, new_priority=new_priority
        )

        updated = await edit_card_service.uow.cards.get_by_id(sample_card.id)
        assert updated.priority.value == new_priority

    async def test_edit_card_due_date_success_by_admin(
        self, admin_user, sample_card, edit_card_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=admin_user.id)
        new_due_date = "2027-12-31"

        await edit_card_service.execute(
            access_token, sample_card.id.value, new_due_date=new_due_date
        )

        updated = await edit_card_service.uow.cards.get_by_id(sample_card.id)
        assert updated.due_date.value.split("T")[0] == new_due_date

    async def test_edit_card_column_success_by_owner(
        self, owner_user, sample_card, second_column, edit_card_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=owner_user.id)

        await edit_card_service.execute(
            access_token, sample_card.id.value, new_column_id=second_column.id.value
        )

        updated = await edit_card_service.uow.cards.get_by_id(sample_card.id)
        assert updated.column_id.value == second_column.id.value

    async def test_edit_card_all_fields_success_by_owner(
        self, owner_user, sample_card, second_column, edit_card_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=owner_user.id)
        new_title = "Completely Updated"
        new_description = "Completely New Description"
        new_priority = "medium"
        new_due_date = "2027-12-31"

        await edit_card_service.execute(
            access_token,
            sample_card.id.value,
            new_column_id=second_column.id.value,
            new_title=new_title,
            new_description=new_description,
            new_priority=new_priority,
            new_due_date=new_due_date,
        )

        updated = await edit_card_service.uow.cards.get_by_id(sample_card.id)
        assert updated.title.value == new_title
        assert updated.description.value == new_description
        assert updated.priority.value == new_priority
        assert updated.due_date.value.split("T")[0] == new_due_date
        assert updated.column_id.value == second_column.id.value

    async def test_edit_card_permission_denied_for_member(
        self, member_user, sample_card, edit_card_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=member_user.id)

        with pytest.raises(PermissionDenied) as exc_info:
            await edit_card_service.execute(
                access_token, sample_card.id.value, new_title="Hacked Title"
            )
        assert "Only owner or admin" in str(exc_info.value)

    async def test_edit_card_no_changes_provided(
        self, owner_user, sample_card, edit_card_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=owner_user.id)

        with pytest.raises(NoChangesError):
            await edit_card_service.execute(access_token, sample_card.id.value)

    async def test_edit_card_not_found(self, owner_user, edit_card_service, encoder):
        access_token = encoder.create_access_token(user_id=owner_user.id)

        with pytest.raises(CardNotFoundError):
            await edit_card_service.execute(
                access_token, "non-existent-id", new_title="New Title"
            )

    async def test_edit_card_target_column_not_found(
        self, owner_user, sample_card, edit_card_service, encoder
    ):
        access_token = encoder.create_access_token(user_id=owner_user.id)

        with pytest.raises(ColumnNotFoundError):
            await edit_card_service.execute(
                access_token, sample_card.id.value, new_column_id=ID().value
            )

    async def test_edit_card_invalid_token(self, sample_card, edit_card_service):
        with pytest.raises(InvalidToken):
            await edit_card_service.execute(
                "invalid_token", sample_card.id.value, new_title="New Title"
            )

    async def test_edit_card_token_version_mismatch(
        self, owner_user, sample_card, edit_card_service, encoder, token_repo
    ):
        access_token = encoder.create_access_token(user_id=owner_user.id)
        # Increment user version to make token version outdated
        await token_repo.increment_user_version(owner_user.id)

        with pytest.raises(InvalidToken):
            await edit_card_service.execute(
                access_token, sample_card.id.value, new_title="New Title"
            )
