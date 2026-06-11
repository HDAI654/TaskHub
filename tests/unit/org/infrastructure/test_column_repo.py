import pytest
from sqlalchemy import select, exists
from src.modules.core.database import get_async_session, engine, Base
from src.modules.org.infrastructure.persistence.models import (
    OrgModel,
    ProjectModel,
    BoardModel,
    ColumnModel,
)
from src.modules.org.infrastructure.persistence.sqlal_column_repo import (
    SQLAL_ColumnRepository,
)
from src.modules.org.domain.factories.column_factory import ColumnFactory
from src.modules.org.domain.value_objects.id import ID
from src.modules.org.domain.value_objects.name import Name
from src.modules.org.domain.value_objects.order import Order
from src.modules.core.exceptions import ColumnNotFoundError, NoChangesError


class TestColumnRepo:
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
        return SQLAL_ColumnRepository(db_session)

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
    async def board_seed(self, db_session, project_seed):
        board = BoardModel(
            public_id=ID().value,
            project_id=project_seed.public_id,
            name="Test Board",
            description="Board Description",
        )
        db_session.add(board)
        await db_session.flush()
        return board

    @pytest.fixture
    async def column_entity(self, board_seed):
        return ColumnFactory.create(
            id=None,
            board_id=board_seed.public_id,
            name="Test Column",
            order=1,
        )

    @pytest.fixture
    async def column_seed(self, db_session, board_seed):
        column = ColumnModel(
            public_id=ID().value,
            board_id=board_seed.public_id,
            name="Seed Column",
            order=1,
        )
        db_session.add(column)
        await db_session.flush()
        return column

    @pytest.fixture
    async def second_column_seed(self, db_session, board_seed):
        column = ColumnModel(
            public_id=ID().value,
            board_id=board_seed.public_id,
            name="Second Column",
            order=2,
        )
        db_session.add(column)
        await db_session.flush()
        return column

    @pytest.fixture
    async def non_existent_column_id(self):
        return ID()

    async def test_add_successfully(self, repo, db_session, column_entity):
        await repo.add(column_entity)

        result = await db_session.execute(
            select(ColumnModel).where(ColumnModel.public_id == column_entity.id.value)
        )
        saved = result.scalar_one()
        assert saved.public_id == column_entity.id.value
        assert saved.name == column_entity.name.value
        assert saved.order == column_entity.order.value
        assert saved.board_id == column_entity.board_id.value

    async def test_get_by_id_successfully(self, repo, column_seed):
        column_id = ID(column_seed.public_id)
        result = await repo.get_by_id(column_id)
        assert result.id.value == column_seed.public_id
        assert result.name.value == column_seed.name
        assert result.order.value == column_seed.order
        assert result.board_id.value == column_seed.board_id

    async def test_get_by_id_not_found(self, repo, non_existent_column_id):
        with pytest.raises(ColumnNotFoundError):
            await repo.get_by_id(non_existent_column_id)

    async def test_get_by_board_id_successfully(
        self, repo, board_seed, column_seed, second_column_seed
    ):
        columns = await repo.get_by_board_id(ID(board_seed.public_id))
        assert len(columns) == 2
        ids = {c.id.value for c in columns}
        assert column_seed.public_id in ids
        assert second_column_seed.public_id in ids
        # Order should be preserved (order 1 then 2)
        assert columns[0].order.value == 1
        assert columns[1].order.value == 2

    async def test_get_by_board_id_empty(self, repo, board_seed):
        columns = await repo.get_by_board_id(ID(board_seed.public_id))
        assert columns == []

    async def test_update_name_successfully(self, repo, column_seed):
        column_id = ID(column_seed.public_id)
        new_name = Name("Updated Column Name")
        await repo.update(column_id, new_name=new_name)

        result = await repo.get_by_id(column_id)
        assert result.name.value == new_name.value
        assert result.order.value == column_seed.order

    async def test_update_order_successfully(self, repo, column_seed):
        column_id = ID(column_seed.public_id)
        new_order = Order(5)
        await repo.update(column_id, new_order=new_order)

        result = await repo.get_by_id(column_id)
        assert result.name.value == column_seed.name
        assert result.order.value == new_order.value

    async def test_update_both_successfully(self, repo, column_seed):
        column_id = ID(column_seed.public_id)
        new_name = Name("New Column Name")
        new_order = Order(10)
        await repo.update(column_id, new_name=new_name, new_order=new_order)

        result = await repo.get_by_id(column_id)
        assert result.name.value == new_name.value
        assert result.order.value == new_order.value

    async def test_update_raises_when_no_fields_provided(self, repo, column_seed):
        column_id = ID(column_seed.public_id)
        with pytest.raises(NoChangesError):
            await repo.update(column_id)

    async def test_update_raises_when_column_not_found(
        self, repo, non_existent_column_id
    ):
        with pytest.raises(ColumnNotFoundError):
            await repo.update(non_existent_column_id, new_name=Name("Anything"))

    async def test_delete_successfully(self, repo, db_session, column_seed):
        column_id = ID(column_seed.public_id)
        await repo.delete(column_id)

        result = await db_session.execute(
            select(exists().where(ColumnModel.public_id == column_id.value))
        )
        assert result.scalar() is False

    async def test_delete_raises_when_column_not_found(
        self, repo, non_existent_column_id
    ):
        with pytest.raises(ColumnNotFoundError):
            await repo.delete(non_existent_column_id)
