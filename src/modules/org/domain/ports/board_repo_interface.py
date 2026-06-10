from abc import ABC, abstractmethod
from typing import List
from src.modules.org.domain.entities.board import BoardEntity
from src.modules.org.domain.value_objects.id import ID
from src.modules.org.domain.value_objects.name import Name
from src.modules.org.domain.value_objects.description import Description


class IBoardRepository(ABC):
    """Repository interface for board entities."""

    @abstractmethod
    async def add(self, board: BoardEntity) -> None:
        """Create a new board in the database."""
        pass

    @abstractmethod
    async def update(
        self,
        board_id: ID,
        new_name: Name | None = None,
        new_description: Description | None = None,
    ) -> None:
        """Update an existing board."""
        pass

    @abstractmethod
    async def delete(self, board_id: ID) -> None:
        """Delete a board by ID."""
        pass

    @abstractmethod
    async def get_by_id(self, board_id: ID) -> BoardEntity:
        """Get a board by ID."""
        pass

    @abstractmethod
    async def get_by_prj_id(self, project_id: ID) -> List[BoardEntity]:
        """Get all boards belonging to a project."""
        pass
