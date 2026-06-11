from abc import ABC, abstractmethod
from src.modules.auth.domain.ports.user_repo_interface import (
    IUserRepository,
)
from src.modules.org.domain.ports.column_repo_interface import (
    IColumnRepository,
)
from src.modules.card.domain.ports.card_repo_interface import (
    ICardRepository,
)


class IUnitOfWork(ABC):
    users: IUserRepository
    columns: IColumnRepository
    cards: ICardRepository

    @abstractmethod
    async def commit(self) -> None:
        pass

    @abstractmethod
    async def rollback(self) -> None:
        pass
