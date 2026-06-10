from src.modules.org.domain.entities.board import BoardEntity
from src.modules.org.domain.value_objects.id import ID
from src.modules.org.domain.value_objects.name import Name
from src.modules.org.domain.value_objects.description import Description
from src.modules.org.domain.value_objects.datetime import DateTime


class BoardFactory:
    @staticmethod
    def create(
        *,
        name: str,
        prj_id: str,
        description: str,
        created_at: float | int | None = None,
        id: str | None = None,
    ) -> BoardEntity:
        """
        Create a new BoardEntity.
        """

        return BoardEntity(
            id=ID(id),
            prj_id=ID(prj_id),
            name=Name(name),
            description=Description(description),
            created_at=DateTime(created_at),
        )
