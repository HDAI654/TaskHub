from abc import ABC, abstractmethod
from src.modules.auth.domain.ports.user_repo_interface import (
    IUserRepository,
)
from src.modules.org.domain.ports.org_repo_interface import (
    IOrgRepository,
)
from src.modules.org.domain.ports.project_repo_interface import (
    IProjectRepository,
)


class IUnitOfWork(ABC):
    users: IUserRepository
    orgs: IOrgRepository
    projects: IProjectRepository

    @abstractmethod
    async def commit(self) -> None:
        pass

    @abstractmethod
    async def rollback(self) -> None:
        pass
