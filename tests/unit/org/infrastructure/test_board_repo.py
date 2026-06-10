import pytest
from sqlalchemy import select, exists
from src.modules.core.database import get_async_session, engine, Base
from src.modules.org.infrastructure.persistence.models import (
    OrgModel,
    ProjectModel,
    BoardModel,
)
from src.modules.org.infrastructure.persistence.sqlal_board_repo import (
    SQLAL_BoardRepository,
)
from src.modules.org.domain.factories.board_factory import BoardFactory
from src.modules.org.domain.value_objects.id import ID
from src.modules.org.domain.value_objects.name import Name
from src.modules.org.domain.value_objects.description import Description
from src.modules.core.exceptions import BoardNotFoundError, NoChangesError


class TestBoardRepo:
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
        return SQLAL_BoardRepository(db_session)

    @pytest.fixture
    async def org_seed(self, db_session):
        org = OrgModel(
            public_id=ID().value,
            name="Test Organization",
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
            description="Project Description",
        )
        db_session.add(project)
        await db_session.flush()
        return project

    @pytest.fixture
    async def board_entity(self, project_seed):
        return BoardFactory.create(
            id=None,
            name="Test Board",
            description="Board Description",
            created_at=None,
            prj_id=project_seed.public_id,
        )

    @pytest.fixture
    async def board_seed(self, db_session, project_seed):
        board = BoardModel(
            public_id=ID().value,
            project_id=project_seed.public_id,
            name="Seed Board",
            description="Seed Description",
        )
        db_session.add(board)
        await db_session.flush()
        return board

    @pytest.fixture
    async def second_board_seed(self, db_session, project_seed):
        board = BoardModel(
            public_id=ID().value,
            project_id=project_seed.public_id,
            name="Second Board",
            description="Second Description",
        )
        db_session.add(board)
        await db_session.flush()
        return board

    @pytest.fixture
    async def non_existent_board_id(self):
        return ID()

    async def test_add_successfully(self, repo, db_session, board_entity):
        await repo.add(board_entity)

        result = await db_session.execute(
            select(BoardModel).where(BoardModel.public_id == board_entity.id.value)
        )
        saved = result.scalar_one()
        assert saved.public_id == board_entity.id.value
        assert saved.name == board_entity.name.value
        assert saved.description == board_entity.description.value
        assert saved.project_id == board_entity.prj_id.value

    async def test_get_by_id_successfully(self, repo, board_seed):
        board_id = ID(board_seed.public_id)
        result = await repo.get_by_id(board_id)
        assert result.id.value == board_seed.public_id
        assert result.name.value == board_seed.name
        assert result.description.value == board_seed.description
        assert result.prj_id.value == board_seed.project_id

    async def test_get_by_id_not_found(self, repo, non_existent_board_id):
        with pytest.raises(BoardNotFoundError):
            await repo.get_by_id(non_existent_board_id)

    async def test_get_by_prj_id_successfully(
        self, repo, db_session, project_seed, board_seed, second_board_seed
    ):
        boards = await repo.get_by_prj_id(ID(project_seed.public_id))
        assert len(boards) == 2
        ids = {b.id.value for b in boards}
        assert board_seed.public_id in ids
        assert second_board_seed.public_id in ids

    async def test_get_by_prj_id_empty(self, repo, project_seed):
        boards = await repo.get_by_prj_id(ID(project_seed.public_id))
        assert boards == []

    async def test_update_name_successfully(self, repo, board_seed):
        board_id = ID(board_seed.public_id)
        new_name = Name("Updated Board Name")
        await repo.update(board_id, new_name=new_name)

        result = await repo.get_by_id(board_id)
        assert result.name.value == new_name.value
        assert result.description.value == board_seed.description

    async def test_update_description_successfully(self, repo, board_seed):
        board_id = ID(board_seed.public_id)
        new_desc = Description("Updated Board Description")
        await repo.update(board_id, new_description=new_desc)

        result = await repo.get_by_id(board_id)
        assert result.name.value == board_seed.name
        assert result.description.value == new_desc.value

    async def test_update_both_successfully(self, repo, board_seed):
        board_id = ID(board_seed.public_id)
        new_name = Name("New Board Name")
        new_desc = Description("New Board Description")
        await repo.update(board_id, new_name=new_name, new_description=new_desc)

        result = await repo.get_by_id(board_id)
        assert result.name.value == new_name.value
        assert result.description.value == new_desc.value

    async def test_update_raises_when_no_fields_provided(self, repo, board_seed):
        board_id = ID(board_seed.public_id)
        with pytest.raises(NoChangesError):
            await repo.update(board_id)

    async def test_update_raises_when_board_not_found(
        self, repo, non_existent_board_id
    ):
        with pytest.raises(BoardNotFoundError):
            await repo.update(non_existent_board_id, new_name=Name("Anything"))

    async def test_delete_successfully(self, repo, db_session, board_seed):
        board_id = ID(board_seed.public_id)
        await repo.delete(board_id)

        result = await db_session.execute(
            select(exists().where(BoardModel.public_id == board_id.value))
        )
        assert result.scalar() is False

    async def test_delete_raises_when_board_not_found(
        self, repo, non_existent_board_id
    ):
        with pytest.raises(BoardNotFoundError):
            await repo.delete(non_existent_board_id)
