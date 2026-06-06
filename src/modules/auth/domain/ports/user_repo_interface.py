from abc import ABC, abstractmethod
from src.modules.auth.domain.entities.user import UserEntity
from src.modules.core.id_vo import ID
from src.modules.auth.domain.value_objects.password import HashedPassword
from src.modules.auth.domain.value_objects.email import Email


class IUserRepository(ABC):
    """Repository interface for User entities."""

    @abstractmethod
    async def add(self, user: UserEntity) -> None:
        """Create a new user in the database."""
        pass

    @abstractmethod
    async def update(
        self, id: ID, new_password: HashedPassword = None, new_email: Email = None
    ) -> None:
        """Update an existing user in the database."""
        pass

    @abstractmethod
    async def delete(self, id: ID) -> None:
        """Delete a user by ID."""
        pass

    @abstractmethod
    async def get_by_id(self, id: ID) -> UserEntity:
        """Get a user by ID."""
        pass

    @abstractmethod
    async def get_by_email(self, email: Email) -> UserEntity:
        """Get a user by email."""
        pass

    @abstractmethod
    async def exists_by_id(self, id: ID) -> bool:
        """Check if a user exists by ID."""
        pass

    @abstractmethod
    async def exists_by_email(self, email: Email) -> bool:
        """Check if a user exists by email."""
        pass
