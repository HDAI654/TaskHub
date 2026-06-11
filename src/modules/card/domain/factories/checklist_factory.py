from src.modules.card.domain.entities.checklist import CheckListEntity
from src.modules.card.domain.value_objects.id import ID
from src.modules.card.domain.value_objects.title import Title
from src.modules.card.domain.value_objects.is_checked import IsChecked


class CheckListFactory:
    @staticmethod
    def create(
        *,
        card_id: str,
        title: str,
        is_checked: bool | None = None,
        id: str | None = None,
    ) -> CheckListEntity:
        """
        Create a new CheckListEntity.
        """

        return CheckListEntity(
            id=ID(id),
            card_id=ID(card_id),
            title=Title(title),
            is_checked=IsChecked(is_checked),
        )
