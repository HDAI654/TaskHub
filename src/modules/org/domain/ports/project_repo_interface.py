from abc import ABC, abstractmethod
from typing import List
from src.modules.org.domain.entities.project import PrjEntity
from src.modules.org.domain.value_objects.id import ID


class IProjectRepository(ABC):
    """Repository interface for project entities."""

    @abstractmethod
    async def add(self, project: PrjEntity) -> None:
        """Create a new project in the database."""
        pass

    @abstractmethod
    async def update(
        self,
        project_id: ID,
        new_name: str | None = None,
        new_description: str | None = None,
    ) -> None:
        """Update an existing project in the database."""
        pass

    @abstractmethod
    async def delete(self, project_id: ID) -> None:
        """Delete a project by ID."""
        pass

    @abstractmethod
    async def get_by_id(self, project_id: ID) -> PrjEntity:
        """Get a project by ID."""
        pass

    @abstractmethod
    async def get_by_org_id(self, org_id: ID) -> List[PrjEntity]:
        """Get all projects of an organization."""
        pass
