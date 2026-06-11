from src.modules.core.entity import Entity
from src.modules.org.domain.value_objects.id import ID
from src.modules.org.domain.value_objects.name import Name
from src.modules.org.domain.value_objects.order import Order


class ColumnEntity(Entity):
    def __init__(
        self,
        id: ID,
        board_id: ID,
        name: Name,
        order: Order,
    ):
        self.id = id
        self.board_id = board_id
        self.name = name
        self.order = order

        super().__init__()
