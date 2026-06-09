import pytest
from sqlalchemy.exc import OperationalError
from src.modules.core.database import engine, get_async_session
from src.modules.org.infrastructure.persistence.sqlal_unit_of_work import (
    SQLAL_UnitOfWork,
)
from src.modules.core.database import Base
from src.modules.org.domain.entities.organization import OrgEntity
from src.modules.org.domain.value_objects.id import ID
from src.modules.org.domain.value_objects.name import Name
from src.modules.org.domain.value_objects.datetime import DateTime
from src.modules.org.exceptions import (
    DatabaseConnectionError,
)


class TestUnitOfWork:
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
    async def sample_org(self):
        return OrgEntity(
            id=ID(),
            name=Name("Test Organization"),
            created_at=DateTime(None),
        )

    async def test_commit_successfully(self, uow, sample_org):
        await uow.orgs.add(sample_org)
        await uow.commit()

        saved_org = await uow.orgs.get_by_id(sample_org.id)
        assert saved_org.id.value == sample_org.id.value
        assert saved_org.name.value == sample_org.name.value

    async def test_commit_rollback_on_error(self, uow, sample_org, mocker):
        mocker.patch.object(
            uow._session,
            "flush",
            side_effect=lambda: None,
        )

        # Add an org
        await uow.orgs.add(sample_org)

        mocker.patch.object(
            uow._session,
            "commit",
            side_effect=OperationalError("statement", "params", "orig"),
        )

        # Mock rollback to track call
        mock_rollback = mocker.patch.object(uow._session, "rollback")

        with pytest.raises(DatabaseConnectionError):
            await uow.commit()

        # Rollback should have been called
        uow._session.rollback.assert_called_once()

        # Verify the user wasn't saved
        assert await uow.orgs.exists_by_id(sample_org.id) is False

    async def test_commit_with_no_changes(self, uow):
        await uow.commit()

    async def test_rollback_discards_changes(self, uow, sample_org):
        await uow.orgs.add(sample_org)
        await uow.rollback()

        exists = await uow.orgs.exists_by_id(sample_org.id)
        assert exists is False

    async def test_multiple_operations_in_one_transaction(self, uow):
        org1 = OrgEntity(
            id=ID(),
            name=Name("Org 1"),
            created_at=None,
        )
        org2 = OrgEntity(
            id=ID(),
            name=Name("Org 2"),
            created_at=None,
        )

        await uow.orgs.add(org1)
        await uow.orgs.add(org2)
        await uow.commit()

        assert await uow.orgs.exists_by_id(org1.id) is True
        assert await uow.orgs.exists_by_id(org2.id) is True

    async def test_rollback_after_multiple_operations(self, uow):
        org1 = OrgEntity(
            id=ID(),
            name=Name("Org 1"),
            created_at=None,
        )
        org2 = OrgEntity(
            id=ID(),
            name=Name("Org 2"),
            created_at=None,
        )

        await uow.orgs.add(org1)
        await uow.orgs.add(org2)
        await uow.rollback()

        assert await uow.orgs.exists_by_id(org1.id) is False
        assert await uow.orgs.exists_by_id(org2.id) is False

    async def test_commit_after_rollback(self, uow, sample_org):
        await uow.orgs.add(sample_org)
        await uow.rollback()

        await uow.orgs.add(sample_org)
        await uow.commit()

        assert await uow.orgs.exists_by_id(sample_org.id) is True
