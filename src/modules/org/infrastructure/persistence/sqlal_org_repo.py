import logging
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select, exists, delete
from sqlalchemy.exc import (
    IntegrityError,
    OperationalError,
    TimeoutError,
    SQLAlchemyError,
)
from src.modules.org.domain.ports.org_repo_interface import IOrgRepository
from src.modules.org.domain.entities.organization import OrgEntity
from src.modules.org.domain.value_objects.id import ID
from src.modules.org.domain.value_objects.name import Name
from src.modules.org.domain.value_objects.role import Role
from src.modules.org.infrastructure.persistence.models import OrgModel
from src.modules.org.domain.factories.organization_factory import OrgFactory
from src.modules.org.exceptions import (
    OrgNotFoundError,
    NoChangesError,
    DatabaseOperationError,
    DatabaseConnectionError,
    DatabaseTimeoutError,
)
from src.modules.auth.infrastructure.persistence.models import UserModel
from src.modules.org.infrastructure.persistence.models import OrgMemberModel

logger = logging.getLogger(__name__)


class SQLAL_OrgRepository(IOrgRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, org: OrgEntity) -> None:
        logger.info("Adding organization: public_id=%s, name=%s", org.id.value, org.name.value)

        org_model = OrgModel(
            public_id=org.id.value,
            name=org.name.value,
        )

        self._session.add(org_model)
        await self._execute_db_operation("add_organization", self._session.flush)

        logger.info("Organization added successfully: public_id=%s", org.id.value)

    async def update(self, org_id: ID, new_name: Name | None = None) -> None:
        logger.info("Updating organization: public_id=%s, new_name=%s", org_id.value, new_name.value if new_name else None)

        update_data = {}
        if new_name is not None:
            update_data["name"] = new_name.value

        if not update_data:
            logger.debug("No changes provided")
            raise NoChangesError("No non-null changes provided.")

        result = await self._execute_db_operation(
            "update_organization",
            self._session.execute,
            update(OrgModel)
            .where(OrgModel.public_id == org_id.value)
            .values(**update_data)
            .returning(OrgModel.public_id),
        )

        updated_id = result.scalar_one_or_none()
        if updated_id is None:
            logger.debug("Organization not found: public_id=%s", org_id.value)
            raise OrgNotFoundError(f"Organization with id {org_id.value!r} not found")

        await self._execute_db_operation("update_organization", self._session.flush)

        logger.info("Organization updated successfully: public_id=%s", org_id.value)

    async def delete(self, org_id: ID) -> None:
        logger.info("Deleting organization: public_id=%s", org_id.value)

        result = await self._execute_db_operation(
            "delete_organization",
            self._session.execute,
            delete(OrgModel).where(OrgModel.public_id == org_id.value),
        )

        if result.rowcount == 0:
            logger.debug("Organization not found: public_id=%s", org_id.value)
            raise OrgNotFoundError(f"Organization with id {org_id.value!r} not found")

        await self._execute_db_operation("delete_organization", self._session.flush)

        logger.info("Organization deleted successfully: public_id=%s", org_id.value)

    async def get_by_id(self, org_id: ID) -> OrgEntity:
        logger.info("Getting organization by id: public_id=%s", org_id.value)

        result = await self._execute_db_operation(
            "get_organization_by_id",
            self._session.execute,
            select(OrgModel).where(OrgModel.public_id == org_id.value),
        )
        org_row = result.scalar_one_or_none()

        if org_row:
            logger.info("Organization found: public_id=%s", org_id.value)
            return self._to_entity(org_row)

        logger.debug("Organization not found: public_id=%s", org_id.value)
        raise OrgNotFoundError(f"Organization with id {org_id.value!r} not found")

    async def get_by_name(self, name: Name) -> OrgEntity:
        logger.info("Getting organization by name: %s", name.value)

        result = await self._execute_db_operation(
            "get_organization_by_name",
            self._session.execute,
            select(OrgModel).where(OrgModel.name == name.value),
        )
        org_row = result.scalar_one_or_none()

        if org_row:
            logger.info("Organization found: name=%s", name.value)
            return self._to_entity(org_row)

        logger.debug("Organization not found: name=%s", name.value)
        raise OrgNotFoundError(f"Organization with name {name.value!r} not found")

    async def exists_by_id(self, org_id: ID) -> bool:
        result = await self._execute_db_operation(
            "exists_organization_by_id",
            self._session.execute,
            select(exists().where(OrgModel.public_id == org_id.value)),
        )
        return result.scalar()

    async def exists_by_name(self, name: Name) -> bool:
        result = await self._execute_db_operation(
            "exists_organization_by_name",
            self._session.execute,
            select(exists().where(OrgModel.name == name.value)),
        )
        return result.scalar()

    async def get_members(self, org_id: ID, role: Role | None = None) -> list[dict[str, Any]]:
        logger.info("Getting members for organization: public_id=%s, role_filter=%s", org_id.value, role)

        query = (
            select(UserModel.public_id, UserModel.email, OrgMemberModel.role, OrgMemberModel.joined_at)
            .join(OrgMemberModel, UserModel.id == OrgMemberModel.user_id)
            .where(OrgMemberModel.organization_id == org_id.value)
        )

        if role:
            query = query.where(OrgMemberModel.role == role.lower())

        result = await self._execute_db_operation(
            "get_organization_members",
            self._session.execute,
            query,
        )

        members = []
        for row in result:
            members.append({
                "user_id": row.public_id,
                "email": row.email,
                "role": row.role,
                "joined_at": row.joined_at.isoformat() if row.joined_at else None,
            })

        logger.info("Found %d members for organization: public_id=%s", len(members), org_id.value)
        return members

    def _to_entity(self, org_model: OrgModel) -> OrgEntity:
        return OrgFactory.create(
            id=org_model.public_id,
            name=org_model.name,
            created_at=org_model.created_at.isoformat(),
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