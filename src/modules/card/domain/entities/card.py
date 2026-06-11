from src.modules.core.entity import Entity
from src.modules.card.domain.value_objects.id import ID
from src.modules.card.domain.value_objects.title import Title
from src.modules.card.domain.value_objects.description import Description
from src.modules.card.domain.value_objects.priority import Priority
from src.modules.card.domain.value_objects.datetime import DateTime


class CardEntity(Entity):
    def __init__(
        self,
        id: ID,
        column_id: ID,
        created_by_user_id: ID,
        title: Title,
        description: Description,
        priority: Priority,
        due_date: DateTime,
        created_at: DateTime,
    ):
        self.id = id
        self.column_id = column_id
        self.created_by_user_id = created_by_user_id
        self.title = title
        self.description = description
        self.priority = priority
        self.due_date = due_date
        self.created_at = created_at

        super().__init__()
