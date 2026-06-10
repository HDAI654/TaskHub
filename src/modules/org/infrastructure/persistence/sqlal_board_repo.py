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
from src.modules.org.domain.ports.board_repo_interface import IBoardRepository
from src.modules.org.domain.entities.board import BoardEntity
from src.modules.org.domain.value_objects.id import ID
from src.modules.org.domain.value_objects.name import Name
from src.modules.org.domain.value_objects.description import Description
from src.modules.org.infrastructure.persistence.models import BoardModel
from src.modules.org.domain.factories.board_factory import BoardFactory
from src.modules.core.exceptions import (
    BoardNotFoundError,
    NoChangesError,
    DatabaseOperationError,
    DatabaseConnectionError,
    DatabaseTimeoutError,
)

logger = logging.getLogger(__name__)


class SQLAL_BoardRepository(IBoardRepository):
    """SQLAlchemy Repository for Board entities."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, board: BoardEntity) -> None:
        logger.info(
            "Adding board: public_id=%s, name=%s, project_id=%s",
            board.id.value,
            board.name.value,
            board.prj_id.value,
        )

        board_model = BoardModel(
            public_id=board.id.value,
            project_id=board.prj_id.value,
            name=board.name.value,
            description=board.description.value,
        )

        self._session.add(board_model)
        await self._execute_db_operation("add_board", self._session.flush)

        logger.info("Board added successfully: public_id=%s", board.id.value)

    async def update(
        self,
        board_id: ID,
        new_name: Name | None = None,
        new_description: Description | None = None,
    ) -> None:
        logger.info(
            "Updating board: public_id=%s, new_name=%s, new_description=%s",
            board_id.value,
            new_name,
            new_description,
        )

        update_data = {}
        if new_name is not None:
            update_data["name"] = new_name.value
        if new_description is not None:
            update_data["description"] = new_description.value

        if not update_data:
            logger.debug("No changes provided")
            raise NoChangesError("No non-null changes provided.")

        result = await self._execute_db_operation(
            "update_board",
            self._session.execute,
            update(BoardModel)
            .where(BoardModel.public_id == board_id.value)
            .values(**update_data)
            .returning(BoardModel.public_id),
        )

        updated_id = result.scalar_one_or_none()
        if updated_id is None:
            logger.debug("Board not found: public_id=%s", board_id.value)
            raise BoardNotFoundError(f"Board with id {board_id.value!r} not found")

        await self._execute_db_operation("update_board", self._session.flush)

        logger.info("Board updated successfully: public_id=%s", board_id.value)

    async def delete(self, board_id: ID) -> None:
        logger.info("Deleting board: public_id=%s", board_id.value)

        result = await self._execute_db_operation(
            "delete_board",
            self._session.execute,
            delete(BoardModel).where(BoardModel.public_id == board_id.value),
        )

        if result.rowcount == 0:
            logger.debug("Board not found: public_id=%s", board_id.value)
            raise BoardNotFoundError(f"Board with id {board_id.value!r} not found")

        await self._execute_db_operation("delete_board", self._session.flush)

        logger.info("Board deleted successfully: public_id=%s", board_id.value)

    async def get_by_id(self, board_id: ID) -> BoardEntity:
        logger.info("Getting board by id: public_id=%s", board_id.value)

        result = await self._execute_db_operation(
            "get_board_by_id",
            self._session.execute,
            select(BoardModel).where(BoardModel.public_id == board_id.value),
        )
        board_row = result.scalar_one_or_none()

        if board_row:
            logger.info("Board found: public_id=%s", board_id.value)
            return self._to_entity(board_row)

        logger.debug("Board not found: public_id=%s", board_id.value)
        raise BoardNotFoundError(f"Board with id {board_id.value!r} not found")

    async def get_by_prj_id(self, project_id: ID) -> List[BoardEntity]:
        logger.info("Getting boards for project: project_id=%s", project_id.value)

        result = await self._execute_db_operation(
            "get_boards_by_project_id",
            self._session.execute,
            select(BoardModel).where(BoardModel.project_id == project_id.value),
        )

        boards = []
        for row in result.scalars():
            boards.append(self._to_entity(row))

        logger.info(
            "Found %d boards for project: project_id=%s", len(boards), project_id.value
        )
        return boards

    def _to_entity(self, board_model: BoardModel) -> BoardEntity:
        return BoardFactory.create(
            id=board_model.public_id,
            prj_id=board_model.project_id,
            name=board_model.name,
            description=board_model.description,
            created_at=board_model.created_at.isoformat(),
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
