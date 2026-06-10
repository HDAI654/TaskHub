from src.modules.org.domain.entities.project import PrjEntity
from src.modules.org.domain.value_objects.id import ID
from src.modules.org.domain.value_objects.name import Name
from src.modules.org.domain.value_objects.description import Description
from src.modules.org.domain.value_objects.datetime import DateTime


class PrjFactory:
    @staticmethod
    def create(
        *,
        name: str,
        org_id: str,
        description: str,
        created_at: float | int | None = None,
        id: str | None = None,
    ) -> PrjEntity:
        """
        Create a new PrjEntity.
        """

        return PrjEntity(
            id=ID(id),
            org_id=ID(org_id),
            name=Name(name),
            description=Description(description),
            created_at=DateTime(created_at),
        )
