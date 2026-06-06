from datetime import date
from src.modules.auth.domain.entities.session import SessionEntity
from src.modules.auth.domain.value_objects.id import ID
from src.modules.auth.domain.value_objects.date import Date


class SessionFactory:
    @staticmethod
    def create(
        *,
        user_id: str,
        id: str | None = None,
        created_at: str | date | None = None
    ) -> SessionEntity:
        """
        Create a new SessionEntity.
        """

        return SessionEntity(
            user_id=ID(user_id),
            id=ID(id),
            created_at=Date(created_at),
        )
