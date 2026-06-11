from src.modules.card.domain.entities.label import LabelEntity
from src.modules.card.domain.value_objects.id import ID
from src.modules.card.domain.value_objects.name import Name


class LabelFactory:
    @staticmethod
    def create(*, name: str, id: str | None = None) -> LabelEntity:
        """
        Create a new LabelEntity.
        """

        return LabelEntity(
            id=ID(id),
            name=Name(name),
        )
