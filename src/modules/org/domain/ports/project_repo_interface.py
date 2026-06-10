from abc import ABC, abstractmethod
from typing import List
from src.modules.org.domain.entities.project import PrjEntity
from src.modules.org.domain.value_objects.id import ID


class IProjectRepository(ABC):
    @abstractmethod
    async def add(self, project: PrjEntity) -> None:
        pass

    @abstractmethod
    async def update(
        self,
        project_id: ID,
        new_name: str | None = None,
        new_description: str | None = None,
    ) -> None:
        pass

    @abstractmethod
    async def delete(self, project_id: ID) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, project_id: ID) -> PrjEntity:
        pass

    @abstractmethod
    async def get_by_org_id(self, org_id: ID) -> List[PrjEntity]:
        pass
