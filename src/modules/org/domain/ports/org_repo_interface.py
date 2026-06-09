from abc import ABC, abstractmethod
from src.modules.org.domain.entities.organization import OrgEntity
from src.modules.org.domain.value_objects.id import ID
from src.modules.org.domain.value_objects.name import Name
from src.modules.org.domain.value_objects.role import Role


class IOrgRepository(ABC):
    """Repository interface for organization entities."""
    
    @abstractmethod
    async def add(self, org: OrgEntity) -> None:
        """Create a new organization in the database."""
        pass

    @abstractmethod
    async def update(self, org_id: ID, new_name: Name | None = None) -> None:
        """Update an existing organization in the database."""
        pass

    @abstractmethod
    async def delete(self, org_id: ID) -> None:
        """Delete a organization by ID."""
        pass

    @abstractmethod
    async def get_by_id(self, org_id: ID) -> OrgEntity:
        """Get a organization by ID."""
        pass

    @abstractmethod
    async def exists_by_id(self, org_id: ID) -> bool:
        """Check if a organization exists by ID."""
        pass

    @abstractmethod
    async def get_members(
        self, org_id: ID, role: Role | None = None
    ) -> list[dict[str, str]]:
        """Get all members of an organization."""
        pass

    @abstractmethod
    async def get_orgs_by_user_id(self, user_id: ID) -> list[dict[str, str]]:
        """Get all organizations where the user is a member."""
        pass

    @abstractmethod
    async def add_member(self, org_id: ID, user_id: ID, role: Role) -> None:
        """Add a user to organization with specified role."""
        pass

    @abstractmethod
    async def remove_member(self, org_id: ID, user_id: ID) -> None:
        """Remove a user from organization."""
        pass

    @abstractmethod
    async def get_user_role(self, org_id: ID, user_id: ID) -> Role | None:
        """Get user's role in organization. Returns None if user is not a member."""
        pass

    @abstractmethod
    async def change_user_role(self, org_id: ID, user_id: ID, new_role: Role) -> None:
        """Change user's role in organization."""
        pass
