from src.modules.auth.domain.entities.user import UserEntity
from src.modules.auth.domain.value_objects.id import ID
from src.modules.auth.domain.value_objects.email import Email
from src.modules.auth.domain.value_objects.password import HashedPassword


class UserFactory:
    @staticmethod
    def create(
        *,
        email: str,
        hashed_password: str,
        id: str | None = None,
    ) -> UserEntity:
        """
        Create a new UserEntity.
        """

        return UserEntity(
            id=ID(id),
            email=Email(email),
            hashed_password=HashedPassword(hashed_password),
        )
