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
from src.modules.org.domain.ports.column_repo_interface import IColumnRepository
from src.modules.org.domain.entities.column import ColumnEntity
from src.modules.org.domain.value_objects.id import ID
from src.modules.org.domain.value_objects.name import Name
from src.modules.org.domain.value_objects.order import Order
from src.modules.org.infrastructure.persistence.models import ColumnModel
from src.modules.org.domain.factories.column_factory import ColumnFactory
from src.modules.core.exceptions import (
    ColumnNotFoundError,
    NoChangesError,
    DatabaseOperationError,
    DatabaseConnectionError,
    DatabaseTimeoutError,
)

logger = logging.getLogger(__name__)


class SQLAL_ColumnRepository(IColumnRepository):
    """SQLAlchemy Repository for Column entities."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, column: ColumnEntity) -> None:
        logger.info(
            "Adding column: public_id=%s, name=%s, board_id=%s, order=%d",
            column.id.value,
            column.name.value,
            column.board_id.value,
            column.order.value,
        )

        column_model = ColumnModel(
            public_id=column.id.value,
            board_id=column.board_id.value,
            name=column.name.value,
            order=column.order.value,
        )

        self._session.add(column_model)
        await self._execute_db_operation("add_column", self._session.flush)

        logger.info("Column added successfully: public_id=%s", column.id.value)

    async def update(
        self,
        column_id: ID,
        new_name: Name | None = None,
        new_order: Order | None = None,
    ) -> None:
        logger.info(
            "Updating column: public_id=%s, new_name=%s, new_order=%s",
            column_id.value,
            new_name.value if new_name else None,
            new_order.value if new_order else None,
        )

        update_data = {}
        if new_name is not None:
            update_data["name"] = new_name.value
        if new_order is not None:
            update_data["order"] = new_order.value

        if not update_data:
            logger.debug("No changes provided")
            raise NoChangesError("No non-null changes provided.")

        result = await self._execute_db_operation(
            "update_column",
            self._session.execute,
            update(ColumnModel)
            .where(ColumnModel.public_id == column_id.value)
            .values(**update_data)
            .returning(ColumnModel.public_id),
        )

        updated_id = result.scalar_one_or_none()
        if updated_id is None:
            logger.debug("Column not found: public_id=%s", column_id.value)
            raise ColumnNotFoundError(f"Column with id {column_id.value!r} not found")

        await self._execute_db_operation("update_column", self._session.flush)

        logger.info("Column updated successfully: public_id=%s", column_id.value)

    async def delete(self, column_id: ID) -> None:
        logger.info("Deleting column: public_id=%s", column_id.value)

        result = await self._execute_db_operation(
            "delete_column",
            self._session.execute,
            delete(ColumnModel).where(ColumnModel.public_id == column_id.value),
        )

        if result.rowcount == 0:
            logger.debug("Column not found: public_id=%s", column_id.value)
            raise ColumnNotFoundError(f"Column with id {column_id.value!r} not found")

        await self._execute_db_operation("delete_column", self._session.flush)

        logger.info("Column deleted successfully: public_id=%s", column_id.value)

    async def get_by_id(self, column_id: ID) -> ColumnEntity:
        logger.info("Getting column by id: public_id=%s", column_id.value)

        result = await self._execute_db_operation(
            "get_column_by_id",
            self._session.execute,
            select(ColumnModel).where(ColumnModel.public_id == column_id.value),
        )
        column_row = result.scalar_one_or_none()

        if column_row:
            logger.info("Column found: public_id=%s", column_id.value)
            return self._to_entity(column_row)

        logger.debug("Column not found: public_id=%s", column_id.value)
        raise ColumnNotFoundError(f"Column with id {column_id.value!r} not found")

    async def get_by_board_id(self, board_id: ID) -> List[ColumnEntity]:
        logger.info("Getting columns for board: board_id=%s", board_id.value)

        result = await self._execute_db_operation(
            "get_columns_by_board_id",
            self._session.execute,
            select(ColumnModel)
            .where(ColumnModel.board_id == board_id.value)
            .order_by(ColumnModel.order),
        )

        columns = []
        for row in result.scalars():
            columns.append(self._to_entity(row))

        logger.info(
            "Found %d columns for board: board_id=%s", len(columns), board_id.value
        )
        return columns

    def _to_entity(self, column_model: ColumnModel) -> ColumnEntity:
        return ColumnFactory.create(
            id=column_model.public_id,
            board_id=column_model.board_id,
            name=column_model.name,
            order=column_model.order,
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
