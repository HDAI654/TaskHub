from src.modules.card.domain.entities.checklist import CheckListEntity
from src.modules.card.domain.value_objects.id import ID
from src.modules.card.domain.value_objects.title import Title
from src.modules.card.domain.value_objects.is_checked import IsChecked


class TestCheckListEntity:
    def test_eq_id(self):
        checklist = CheckListEntity(
            id=ID("MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"),
            card_id=ID(),
            title=Title("ExampleTitle"),
            is_checked=IsChecked(False),
        )
        checklist2 = CheckListEntity(
            id=ID("MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"),
            card_id=ID(),
            title=Title("ExampleTitle"),
            is_checked=IsChecked(False),
        )
        checklist3 = CheckListEntity(
            id=ID("MyDifferentIDDDDDDDDDDDDDDDDDDDDDDDD"),
            card_id=ID(),
            title=Title("ExampleTitle"),
            is_checked=IsChecked(False),
        )

        assert checklist == checklist2
        assert checklist != checklist3 and checklist2 != checklist3
