from src.modules.org.domain.entities.organization import OrgEntity
from src.modules.org.domain.value_objects.id import ID
from src.modules.org.domain.value_objects.name import Name
from src.modules.org.domain.value_objects.datetime import DateTime


class OrgFactory:
    @staticmethod
    def create(
        *,
        name: str,
        created_at: float | int | None = None,
        id: str | None = None,
    ) -> OrgEntity:
        """
        Create a new OrgEntity.
        """

        return OrgEntity(
            id=ID(id),
            name=Name(name),
            created_at=DateTime(created_at),
        )
