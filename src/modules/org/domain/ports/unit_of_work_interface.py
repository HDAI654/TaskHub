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
from src.modules.org.domain.ports.board_repo_interface import (
    IBoardRepository,
)
from src.modules.org.domain.ports.column_repo_interface import (
    IColumnRepository,
)


class IUnitOfWork(ABC):
    users: IUserRepository
    orgs: IOrgRepository
    projects: IProjectRepository
    boards: IBoardRepository
    columns: IColumnRepository

    @abstractmethod
    async def commit(self) -> None:
        pass

    @abstractmethod
    async def rollback(self) -> None:
        pass
