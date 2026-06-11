from src.modules.card.domain.entities.card import CardEntity
from src.modules.card.domain.value_objects.id import ID
from src.modules.card.domain.value_objects.title import Title
from src.modules.card.domain.value_objects.description import Description
from src.modules.card.domain.value_objects.priority import Priority
from src.modules.card.domain.value_objects.datetime import DateTime


class CardFactory:
    @staticmethod
    def create(
        *,
        column_id: str,
        created_by_user_id: str,
        title: str,
        description: str,
        priority: str,
        due_date: str,
        created_at: str | None = None,
        id: str | None = None,
    ) -> CardEntity:
        """
        Create a new CardEntity.
        """

        return CardEntity(
            id=ID(id),
            column_id=ID(column_id),
            created_by_user_id=ID(created_by_user_id),
            title=Title(title),
            description=Description(description),
            priority=Priority(priority),
            due_date=DateTime(due_date),
            created_at=DateTime(created_at),
        )
