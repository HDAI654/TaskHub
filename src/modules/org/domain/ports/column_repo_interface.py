from abc import ABC, abstractmethod
from typing import List
from src.modules.org.domain.entities.column import ColumnEntity
from src.modules.org.domain.value_objects.id import ID
from src.modules.org.domain.value_objects.name import Name
from src.modules.org.domain.value_objects.order import Order


class IColumnRepository(ABC):
    """Repository interface for column entities."""

    @abstractmethod
    async def add(self, column: ColumnEntity) -> None:
        """Create a new column in the database."""
        pass

    @abstractmethod
    async def update(
        self,
        column_id: ID,
        new_name: Name | None = None,
        new_order: Order | None = None,
    ) -> None:
        """Update an existing column (name and/or order)."""
        pass

    @abstractmethod
    async def delete(self, column_id: ID) -> None:
        """Delete a column by ID."""
        pass

    @abstractmethod
    async def get_by_id(self, column_id: ID) -> ColumnEntity:
        """Get a column by ID."""
        pass

    @abstractmethod
    async def get_by_board_id(self, board_id: ID) -> List[ColumnEntity]:
        """Get all columns belonging to a board, ordered by 'order' field."""
        pass

    @abstractmethod
    async def get_org_id(self, column_id: ID) -> ID:
        """Find the organization id of a column"""
        pass
