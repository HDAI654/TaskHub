from src.modules.org.domain.entities.column import ColumnEntity
from src.modules.org.domain.value_objects.id import ID
from src.modules.org.domain.value_objects.name import Name
from src.modules.org.domain.value_objects.order import Order


class ColumnFactory:
    @staticmethod
    def create(
        *,
        board_id: str,
        name: str,
        order: int,
        id: str | None = None,
    ) -> ColumnEntity:
        """
        Create a new ColumnEntity.
        """

        return ColumnEntity(
            id=ID(id),
            board_id=ID(board_id),
            name=Name(name),
            order=Order(order),
        )
