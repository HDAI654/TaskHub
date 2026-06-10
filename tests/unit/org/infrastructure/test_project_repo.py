import pytest
from sqlalchemy import select, exists
from src.modules.core.database import get_async_session, engine, Base
from src.modules.org.infrastructure.persistence.models import OrgModel, ProjectModel
from src.modules.org.infrastructure.persistence.sqlal_project_repo import (
    SQLAL_ProjectRepository,
)
from src.modules.org.domain.factories.project_factory import PrjFactory
from src.modules.org.domain.value_objects.id import ID
from src.modules.org.domain.value_objects.name import Name
from src.modules.org.domain.value_objects.description import Description
from src.modules.core.exceptions import ProjectNotFoundError, NoChangesError


class TestProjectRepo:
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
        return SQLAL_ProjectRepository(db_session)

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
    async def project_entity(self, org_seed):
        return PrjFactory.create(
            id=None,  # will generate new ID
            name="Test Project",
            description="Test Description",
            created_at=None,
            org_id=org_seed.public_id,
        )

    @pytest.fixture
    async def project_seed(self, db_session, org_seed):
        project = ProjectModel(
            public_id=ID().value,
            organization_id=org_seed.public_id,
            name="Seed Project",
            description="Seed Description",
        )
        db_session.add(project)
        await db_session.flush()
        return project

    @pytest.fixture
    async def non_existent_project_id(self):
        return ID()

    async def test_add_successfully(self, repo, db_session, project_entity):
        await repo.add(project_entity)

        result = await db_session.execute(
            select(ProjectModel).where(
                ProjectModel.public_id == project_entity.id.value
            )
        )
        saved = result.scalar_one()
        assert saved.public_id == project_entity.id.value
        assert saved.name == project_entity.name.value
        assert saved.description == project_entity.description.value
        assert saved.organization_id == project_entity.org_id.value

    async def test_get_by_id_successfully(self, repo, project_seed):
        project_id = ID(project_seed.public_id)
        result = await repo.get_by_id(project_id)
        assert result.id.value == project_seed.public_id
        assert result.name.value == project_seed.name
        assert result.description.value == project_seed.description
        assert result.org_id.value == project_seed.organization_id

    async def test_get_by_id_not_found(self, repo, non_existent_project_id):
        with pytest.raises(ProjectNotFoundError):
            await repo.get_by_id(non_existent_project_id)

    async def test_get_by_org_id_successfully(self, repo, db_session, org_seed):
        # Create two projects for same org
        project1 = ProjectModel(
            public_id=ID().value,
            organization_id=org_seed.public_id,
            name="Proj 1",
            description="Desc 1",
        )
        project2 = ProjectModel(
            public_id=ID().value,
            organization_id=org_seed.public_id,
            name="Proj 2",
            description="Desc 2",
        )
        db_session.add_all([project1, project2])
        await db_session.flush()

        projects = await repo.get_by_org_id(ID(org_seed.public_id))
        assert len(projects) == 2
        ids = {p.id.value for p in projects}
        assert project1.public_id in ids
        assert project2.public_id in ids

    async def test_get_by_org_id_empty(self, repo, org_seed):
        projects = await repo.get_by_org_id(ID(org_seed.public_id))
        assert projects == []

    async def test_update_name_successfully(self, repo, project_seed):
        project_id = ID(project_seed.public_id)
        new_name = "Updated Name"
        await repo.update(project_id, new_name=new_name)

        result = await repo.get_by_id(project_id)
        assert result.name.value == new_name
        assert result.description.value == project_seed.description

    async def test_update_description_successfully(self, repo, project_seed):
        project_id = ID(project_seed.public_id)
        new_desc = "Updated Description"
        await repo.update(project_id, new_description=new_desc)

        result = await repo.get_by_id(project_id)
        assert result.name.value == project_seed.name
        assert result.description.value == new_desc

    async def test_update_both_successfully(self, repo, project_seed):
        project_id = ID(project_seed.public_id)
        new_name = "New Name"
        new_desc = "New Desc"
        await repo.update(project_id, new_name=new_name, new_description=new_desc)

        result = await repo.get_by_id(project_id)
        assert result.name.value == new_name
        assert result.description.value == new_desc

    async def test_update_raises_when_no_fields_provided(self, repo, project_seed):
        project_id = ID(project_seed.public_id)
        with pytest.raises(NoChangesError):
            await repo.update(project_id)

    async def test_update_raises_when_project_not_found(
        self, repo, non_existent_project_id
    ):
        with pytest.raises(ProjectNotFoundError):
            await repo.update(non_existent_project_id, new_name="Anything")

    async def test_delete_successfully(self, repo, db_session, project_seed):
        project_id = ID(project_seed.public_id)
        await repo.delete(project_id)

        result = await db_session.execute(
            select(exists().where(ProjectModel.public_id == project_id.value))
        )
        assert result.scalar() is False

    async def test_delete_raises_when_project_not_found(
        self, repo, non_existent_project_id
    ):
        with pytest.raises(ProjectNotFoundError):
            await repo.delete(non_existent_project_id)
