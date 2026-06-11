import pytest
from sqlalchemy import select, exists
from src.modules.core.database import get_async_session, engine, Base
from datetime import datetime
from src.modules.auth.infrastructure.persistence.models import UserModel
from src.modules.org.infrastructure.persistence.models import (
    OrgModel,
    ProjectModel,
    BoardModel,
    ColumnModel,
)
from src.modules.card.infrastructure.persistence.models import (
    CardModel,
    CardAssigneesModel,
    LabelsModel,
    CardLabels,
    CheckListsModel,
)
from src.modules.card.infrastructure.persistence.sqlal_card_repo import (
    SQLAL_CardRepository,
)
from src.modules.card.domain.factories.card_factory import CardFactory
from src.modules.card.domain.factories.label_factory import LabelFactory
from src.modules.card.domain.factories.checklist_factory import CheckListFactory
from src.modules.auth.domain.factories.user_factory import UserFactory
from src.modules.card.domain.value_objects.id import ID
from src.modules.card.domain.value_objects.title import Title
from src.modules.card.domain.value_objects.description import Description
from src.modules.card.domain.value_objects.priority import Priority
from src.modules.card.domain.value_objects.datetime import DateTime
from src.modules.card.domain.value_objects.is_checked import IsChecked
from src.modules.core.exceptions import (
    CardNotFoundError,
    LabelNotFoundError,
    CheckListNotFoundError,
    NoChangesError,
)


class TestCardRepo:
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
    async def repo(self, db_session):
        return SQLAL_CardRepository(db_session)

    @pytest.fixture
    async def org_seed(self, db_session):
        org = OrgModel(
            public_id=ID().value,
            name="Test Org",
        )
        db_session.add(org)
        await db_session.flush()
        return org

    @pytest.fixture
    async def project_seed(self, db_session, org_seed):
        project = ProjectModel(
            public_id=ID().value,
            organization_id=org_seed.public_id,
            name="Test Project",
            description="Project Desc",
        )
        db_session.add(project)
        await db_session.flush()
        return project

    @pytest.fixture
    async def board_seed(self, db_session, project_seed):
        board = BoardModel(
            public_id=ID().value,
            project_id=project_seed.public_id,
            name="Test Board",
            description="Board Desc",
        )
        db_session.add(board)
        await db_session.flush()
        return board

    @pytest.fixture
    async def column_seed(self, db_session, board_seed):
        column = ColumnModel(
            public_id=ID().value,
            board_id=board_seed.public_id,
            name="Test Column",
            order=1,
        )
        db_session.add(column)
        await db_session.flush()
        return column

    @pytest.fixture
    async def user_seed(self, db_session):
        user = UserModel(
            public_id=ID().value,
            email="creator@example.com",
            password="hashed",
        )
        db_session.add(user)
        await db_session.flush()
        return user

    @pytest.fixture
    async def assignee_user_seed(self, db_session):
        user = UserModel(
            public_id=ID().value,
            email="assignee@example.com",
            password="hashed",
        )
        db_session.add(user)
        await db_session.flush()
        return user

    @pytest.fixture
    async def card_entity(self, column_seed, user_seed):
        return CardFactory.create(
            column_id=column_seed.public_id,
            created_by_user_id=user_seed.public_id,
            title="Test Card",
            description="Card Description",
            priority="high",
            due_date="2025-12-31T23:59:59+00:00",
        )

    @pytest.fixture
    async def card_seed(self, db_session, column_seed, user_seed):
        card = CardModel(
            public_id=ID().value,
            column_id=column_seed.public_id,
            title="Seed Card",
            description="Seed Desc",
            priority="medium",
            due_date=datetime.fromisoformat("2025-12-31T23:59:59+00:00"),
            created_by_user_id=user_seed.public_id,
        )
        db_session.add(card)
        await db_session.flush()
        return card

    @pytest.fixture
    async def label_entity(self):
        return LabelFactory.create(name="bug")

    @pytest.fixture
    async def checklist_entity(self, card_seed):
        return CheckListFactory.create(
            card_id=card_seed.public_id,
            title="Check item",
            is_checked=False,
        )

    @pytest.fixture
    async def non_existent_card_id(self):
        return ID()

    # ========== Card tests ==========

    async def test_add_successfully(self, repo, db_session, card_entity):
        await repo.add(card_entity)

        result = await db_session.execute(
            select(CardModel).where(CardModel.public_id == card_entity.id.value)
        )
        saved = result.scalar_one()
        assert saved.public_id == card_entity.id.value
        assert saved.title == card_entity.title.value
        assert saved.column_id == card_entity.column_id.value

    async def test_get_by_id_successfully(self, repo, card_seed):
        card_id = ID(card_seed.public_id)
        result = await repo.get_by_id(card_id)
        assert result.id.value == card_seed.public_id
        assert result.title.value == card_seed.title

    async def test_get_by_id_not_found(self, repo, non_existent_card_id):
        with pytest.raises(CardNotFoundError):
            await repo.get_by_id(non_existent_card_id)

    async def test_get_by_column_id_successfully(
        self, repo, db_session, column_seed, card_seed
    ):
        # Create second card in same column
        card2 = CardModel(
            public_id=ID().value,
            column_id=column_seed.public_id,
            title="Second Card",
            description="Desc2",
            priority="low",
            due_date=datetime.fromisoformat("2025-12-31T23:59:59+00:00"),
            created_by_user_id=card_seed.created_by_user_id,
        )
        db_session.add(card2)
        await db_session.flush()

        cards = await repo.get_by_column_id(ID(column_seed.public_id))
        assert len(cards) == 2
        ids = {c.id.value for c in cards}
        assert card_seed.public_id in ids
        assert card2.public_id in ids

    async def test_update_card_successfully(self, repo, card_seed):
        card_id = ID(card_seed.public_id)
        new_title = Title("Updated Title")
        new_priority = Priority("urgent")
        await repo.update(card_id, new_title=new_title, new_priority=new_priority)

        updated = await repo.get_by_id(card_id)
        assert updated.title.value == new_title.value
        assert updated.priority.value == new_priority.value
        # Other fields unchanged
        assert updated.description.value == card_seed.description

    async def test_update_raises_when_no_changes(self, repo, card_seed):
        card_id = ID(card_seed.public_id)
        with pytest.raises(NoChangesError):
            await repo.update(card_id)

    async def test_update_raises_when_card_not_found(self, repo, non_existent_card_id):
        with pytest.raises(CardNotFoundError):
            await repo.update(non_existent_card_id, new_title=Title("New"))

    async def test_delete_successfully(self, repo, db_session, card_seed):
        card_id = ID(card_seed.public_id)
        await repo.delete(card_id)

        result = await db_session.execute(
            select(exists().where(CardModel.public_id == card_id.value))
        )
        assert result.scalar() is False

    async def test_delete_raises_when_card_not_found(self, repo, non_existent_card_id):
        with pytest.raises(CardNotFoundError):
            await repo.delete(non_existent_card_id)

    # ========== Assignee tests ==========

    async def test_add_assignee_successfully(self, repo, card_seed, assignee_user_seed):
        card_id = ID(card_seed.public_id)
        assignee = UserFactory.create(
            id=assignee_user_seed.public_id,
            email=assignee_user_seed.email,
            hashed_password=assignee_user_seed.password,
        )
        await repo.add_assignee(card_id, assignee)

        assignees = await repo.get_card_assignee_IDs(card_id)
        assert len(assignees) == 1
        assert assignees[0].value == assignee_user_seed.public_id

    async def test_add_assignee_duplicate(self, repo, card_seed, assignee_user_seed):
        card_id = ID(card_seed.public_id)
        assignee = UserFactory.create(
            id=assignee_user_seed.public_id,
            email=assignee_user_seed.email,
            hashed_password=assignee_user_seed.password,
        )
        await repo.add_assignee(card_id, assignee)
        # Adding again should not raise error (should just log and return)
        await repo.add_assignee(card_id, assignee)
        assignees = await repo.get_card_assignee_IDs(card_id)
        assert len(assignees) == 1

    async def test_del_assignee_successfully(self, repo, card_seed, assignee_user_seed):
        card_id = ID(card_seed.public_id)
        assignee = UserFactory.create(
            id=assignee_user_seed.public_id,
            email=assignee_user_seed.email,
            hashed_password=assignee_user_seed.password,
        )
        await repo.add_assignee(card_id, assignee)
        await repo.del_assignee(card_id, ID(assignee_user_seed.public_id))
        assignees = await repo.get_card_assignee_IDs(card_id)
        assert len(assignees) == 0

    async def test_get_card_assignee_IDs_empty(self, repo, card_seed):
        assignees = await repo.get_card_assignee_IDs(ID(card_seed.public_id))
        assert assignees == []

    # ========== Label tests ==========

    async def test_add_label_new_label(self, repo, card_seed):
        card_id = ID(card_seed.public_id)
        label = LabelFactory.create(name="critical")
        await repo.add_label(card_id, label)

        # Verify label created in labels table
        label_row = await repo._get_label_by_name("critical")
        assert label_row is not None
        assert label_row.name == "critical"

        # Verify association
        card_labels = await repo.get_card_labels(card_id)
        assert len(card_labels) == 1
        assert card_labels[0].name.value == "critical"

    async def test_add_label_existing_label(self, repo, card_seed):
        card_id = ID(card_seed.public_id)
        # Pre-create label
        label_model = LabelsModel(public_id=ID().value, name="bug")
        repo._session.add(label_model)
        await repo._session.flush()

        label = LabelFactory.create(name="bug")
        await repo.add_label(card_id, label)

        card_labels = await repo.get_card_labels(card_id)
        assert len(card_labels) == 1
        assert card_labels[0].name.value == "bug"

    async def test_add_label_card_not_found(self, repo):
        label = LabelFactory.create(name="label")
        with pytest.raises(CardNotFoundError):
            await repo.add_label(ID(), label)

    async def test_del_label_successfully(self, repo, card_seed):
        card_id = ID(card_seed.public_id)
        label = LabelFactory.create(name="feature")
        await repo.add_label(card_id, label)
        await repo.del_label(card_id, label)

        card_labels = await repo.get_card_labels(card_id)
        assert len(card_labels) == 0

    async def test_del_label_not_attached(self, repo, card_seed):
        card_id = ID(card_seed.public_id)
        label = LabelFactory.create(name="nonexistent")
        with pytest.raises(LabelNotFoundError):
            await repo.del_label(card_id, label)

    async def test_get_card_labels_empty(self, repo, card_seed):
        labels = await repo.get_card_labels(ID(card_seed.public_id))
        assert labels == []

    # ========== Checklist tests ==========

    async def test_add_checklist_successfully(self, repo, card_seed):
        card_id = ID(card_seed.public_id)
        checklist = CheckListFactory.create(
            card_id=card_id.value,
            title="Task 1",
            is_checked=False,
        )
        await repo.add_checklist(card_id, checklist)

        result = await repo.get_card_checklists(card_id)
        assert len(result) == 1
        assert result[0].title.value == "Task 1"
        assert result[0].is_checked.value is False

    async def test_update_checklist_successfully(self, repo, card_seed):
        card_id = ID(card_seed.public_id)
        checklist = CheckListFactory.create(
            card_id=card_id.value,
            title="Original",
            is_checked=False,
        )
        await repo.add_checklist(card_id, checklist)

        new_title = Title("Updated")
        new_checked = IsChecked(True)
        await repo.update_checklist(checklist.id, new_title, new_checked)

        updated = await repo.get_checklist_by_id(checklist.id)
        assert updated.title.value == "Updated"
        assert updated.is_checked.value is True

    async def test_update_checklist_not_found(self, repo):
        with pytest.raises(CheckListNotFoundError):
            await repo.update_checklist(ID(), new_title=Title("New"))

    async def test_del_checklist_successfully(self, repo, card_seed):
        card_id = ID(card_seed.public_id)
        checklist = CheckListFactory.create(
            card_id=card_id.value,
            title="To delete",
            is_checked=False,
        )
        await repo.add_checklist(card_id, checklist)
        await repo.del_checklist(checklist.id)

        checklists = await repo.get_card_checklists(card_id)
        assert len(checklists) == 0

    async def test_get_checklist_by_id_successfully(self, repo, card_seed):
        card_id = ID(card_seed.public_id)
        checklist = CheckListFactory.create(
            card_id=card_id.value,
            title="Find me",
            is_checked=False,
        )
        await repo.add_checklist(card_id, checklist)

        found = await repo.get_checklist_by_id(checklist.id)
        assert found.id.value == checklist.id.value
        assert found.title.value == "Find me"

    async def test_get_checklist_by_id_not_found(self, repo):
        with pytest.raises(CheckListNotFoundError):
            await repo.get_checklist_by_id(ID())

    async def test_get_card_checklists_multiple(self, repo, card_seed):
        card_id = ID(card_seed.public_id)
        cl1 = CheckListFactory.create(
            card_id=card_id.value, title="Item 1", is_checked=False
        )
        cl2 = CheckListFactory.create(
            card_id=card_id.value, title="Item 2", is_checked=True
        )
        await repo.add_checklist(card_id, cl1)
        await repo.add_checklist(card_id, cl2)

        checklists = await repo.get_card_checklists(card_id)
        assert len(checklists) == 2
        titles = {c.title.value for c in checklists}
        assert "Item 1" in titles
        assert "Item 2" in titles
