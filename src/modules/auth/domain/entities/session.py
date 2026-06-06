from src.modules.core.entity import Entity
from src.modules.auth.domain.value_objects.id import ID
from src.modules.auth.domain.value_objects.date import Date


class SessionEntity(Entity):
    def __init__(
        self,
        id: ID,
        user_id: ID,
        created_at: Date,
    ):
        self.id = id
        self.user_id = user_id
        self.created_at = created_at

        super().__init__()
