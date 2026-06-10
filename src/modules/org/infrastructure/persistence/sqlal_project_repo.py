import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select, delete
from sqlalchemy.exc import (
    IntegrityError,
    OperationalError,
    TimeoutError,
    SQLAlchemyError,
)
from src.modules.org.domain.ports.project_repo_interface import IProjectRepository
from src.modules.org.domain.entities.project import PrjEntity
from src.modules.org.domain.value_objects.id import ID
from src.modules.org.infrastructure.persistence.models import ProjectModel
from src.modules.org.domain.factories.project_factory import PrjFactory
from src.modules.core.exceptions import (
    ProjectNotFoundError,
    NoChangesError,
    DatabaseOperationError,
    DatabaseConnectionError,
    DatabaseTimeoutError,
)

logger = logging.getLogger(__name__)


class SQLAL_ProjectRepository(IProjectRepository):
    """SQLAlchemy Repository for Project entities."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, project: PrjEntity) -> None:
        logger.info(
            "Adding project: public_id=%s, name=%s, org_id=%s",
            project.id.value,
            project.name.value,
            project.org_id.value,
        )

        project_model = ProjectModel(
            public_id=project.id.value,
            organization_id=project.org_id.value,
            name=project.name.value,
            description=project.description.value,
        )

        self._session.add(project_model)
        await self._execute_db_operation("add_project", self._session.flush)

        logger.info("Project added successfully: public_id=%s", project.id.value)

    async def update(
        self,
        project_id: ID,
        new_name: str | None = None,
        new_description: str | None = None,
    ) -> None:
        logger.info(
            "Updating project: public_id=%s, new_name=%s, new_description=%s",
            project_id.value,
            new_name,
            new_description,
        )

        update_data = {}
        if new_name is not None:
            update_data["name"] = new_name
        if new_description is not None:
            update_data["description"] = new_description

        if not update_data:
            logger.debug("No changes provided")
            raise NoChangesError("No non-null changes provided.")

        result = await self._execute_db_operation(
            "update_project",
            self._session.execute,
            update(ProjectModel)
            .where(ProjectModel.public_id == project_id.value)
            .values(**update_data)
            .returning(ProjectModel.public_id),
        )

        updated_id = result.scalar_one_or_none()
        if updated_id is None:
            logger.debug("Project not found: public_id=%s", project_id.value)
            raise ProjectNotFoundError(
                f"Project with id {project_id.value!r} not found"
            )

        await self._execute_db_operation("update_project", self._session.flush)

        logger.info("Project updated successfully: public_id=%s", project_id.value)

    async def delete(self, project_id: ID) -> None:
        logger.info("Deleting project: public_id=%s", project_id.value)

        result = await self._execute_db_operation(
            "delete_project",
            self._session.execute,
            delete(ProjectModel).where(ProjectModel.public_id == project_id.value),
        )

        if result.rowcount == 0:
            logger.debug("Project not found: public_id=%s", project_id.value)
            raise ProjectNotFoundError(
                f"Project with id {project_id.value!r} not found"
            )

        await self._execute_db_operation("delete_project", self._session.flush)

        logger.info("Project deleted successfully: public_id=%s", project_id.value)

    async def get_by_id(self, project_id: ID) -> PrjEntity:
        logger.info("Getting project by id: public_id=%s", project_id.value)

        result = await self._execute_db_operation(
            "get_project_by_id",
            self._session.execute,
            select(ProjectModel).where(ProjectModel.public_id == project_id.value),
        )
        project_row = result.scalar_one_or_none()

        if project_row:
            logger.info("Project found: public_id=%s", project_id.value)
            return self._to_entity(project_row)

        logger.debug("Project not found: public_id=%s", project_id.value)
        raise ProjectNotFoundError(f"Project with id {project_id.value!r} not found")

    async def get_by_org_id(self, org_id: ID) -> List[PrjEntity]:
        logger.info("Getting projects for organization: org_id=%s", org_id.value)

        result = await self._execute_db_operation(
            "get_projects_by_org_id",
            self._session.execute,
            select(ProjectModel).where(ProjectModel.organization_id == org_id.value),
        )

        projects = []
        for row in result.scalars():
            projects.append(self._to_entity(row))

        logger.info(
            "Found %d projects for organization: org_id=%s", len(projects), org_id.value
        )
        return projects

    def _to_entity(self, project_model: ProjectModel) -> PrjEntity:
        return PrjFactory.create(
            id=project_model.public_id,
            org_id=project_model.organization_id,
            name=project_model.name,
            description=project_model.description,
            created_at=project_model.created_at.isoformat(),
        )

    async def _execute_db_operation(self, operation: str, coro, *args, **kwargs):
        try:
            return await coro(*args, **kwargs)
        except IntegrityError as e:
            logger.exception(f"Database integrity error during {operation}")
            raise DatabaseOperationError(f"Database integrity error: {e}") from e
        except OperationalError as e:
            logger.exception(f"Database connection error during {operation}")
            raise DatabaseConnectionError(f"Failed to connect to database: {e}") from e
        except TimeoutError as e:
            logger.exception(f"Database timeout during {operation}")
            raise DatabaseTimeoutError(f"Database operation timed out: {e}") from e
        except SQLAlchemyError as e:
            logger.exception(f"Database error during {operation}")
            raise DatabaseOperationError(f"Database operation failed: {e}") from e
