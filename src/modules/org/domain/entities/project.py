from src.modules.core.entity import Entity
from src.modules.org.domain.value_objects.id import ID
from src.modules.org.domain.value_objects.name import Name
from src.modules.org.domain.value_objects.description import Description
from src.modules.org.domain.value_objects.datetime import DateTime


class PrjEntity(Entity):
    def __init__(
        self,
        id: ID,
        name: Name,
        description: Description,
        created_at: DateTime,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.created_at = created_at

        super().__init__()
