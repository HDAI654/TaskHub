from src.modules.core.entity import Entity
from src.modules.card.domain.value_objects.id import ID
from src.modules.card.domain.value_objects.title import Title
from src.modules.card.domain.value_objects.is_checked import IsChecked


class CheckListEntity(Entity):
    def __init__(
        self,
        id: ID,
        card_id: ID,
        title: Title,
        is_checked: IsChecked,
    ):
        self.id = id
        self.card_id = card_id
        self.title = title
        self.is_checked = is_checked

        super().__init__()
