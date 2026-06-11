from src.modules.core.entity import Entity
from src.modules.card.domain.value_objects.id import ID
from src.modules.card.domain.value_objects.name import Name


class LabelEntity(Entity):
    def __init__(
        self,
        id: ID,
        name: Name,
    ):
        self.id = id
        self.name = name

        super().__init__()
