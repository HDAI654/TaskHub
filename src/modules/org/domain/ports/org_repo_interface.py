from abc import ABC, abstractmethod
from typing import Any
from src.modules.org.domain.entities.organization import OrgEntity
from src.modules.org.domain.value_objects.id import ID
from src.modules.org.domain.value_objects.name import Name
from src.modules.org.domain.value_objects.role import Role


class IOrgRepository(ABC):
    @abstractmethod
    async def add(self, org: OrgEntity) -> None:
        pass

    @abstractmethod
    async def update(self, org_id: ID, new_name: Name | None = None) -> None:
        pass

    @abstractmethod
    async def delete(self, org_id: ID) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, org_id: ID) -> OrgEntity:
        pass

    @abstractmethod
    async def get_by_name(self, name: Name) -> OrgEntity:
        pass

    @abstractmethod
    async def exists_by_id(self, org_id: ID) -> bool:
        pass

    @abstractmethod
    async def exists_by_name(self, name: Name) -> bool:
        pass

    @abstractmethod
    async def get_members(self, org_id: ID, role: Role | None = None) -> list[dict[str, Any]]:
        pass