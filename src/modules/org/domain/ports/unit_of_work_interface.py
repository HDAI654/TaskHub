from abc import ABC, abstractmethod
from src.modules.org.domain.ports.org_repo_interface import (
    IOrgRepository,
)


class IUnitOfWork(ABC):
    orgs: IOrgRepository

    @abstractmethod
    async def commit(self) -> None:
        pass

    @abstractmethod
    async def rollback(self) -> None:
        pass
