from src.modules.card.domain.entities.card import CardEntity
from src.modules.card.domain.value_objects.id import ID
from src.modules.card.domain.value_objects.title import Title
from src.modules.card.domain.value_objects.description import Description
from src.modules.card.domain.value_objects.priority import Priority
from src.modules.card.domain.value_objects.datetime import DateTime


class TestCardEntity:
    def test_eq_id(self):
        card = CardEntity(
            id=ID("MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"),
            column_id=ID(),
            created_by_user_id=ID(),
            title=Title("ExampleTitle"),
            description=Description("Desc"),
            priority=Priority("urgent"),
            due_date=DateTime("2028-09-07"),
            created_at=DateTime(),
        )
        card2 = CardEntity(
            id=ID("MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"),
            column_id=ID(),
            created_by_user_id=ID(),
            title=Title("ExampleTitle"),
            description=Description("Desc"),
            priority=Priority("urgent"),
            due_date=DateTime("2028-09-07"),
            created_at=DateTime(),
        )
        card3 = CardEntity(
            id=ID("MyDifferentIDDDDDDDDDDDDDDDDDDDDDDDD"),
            column_id=ID(),
            created_by_user_id=ID(),
            title=Title("ExampleTitle"),
            description=Description("Desc"),
            priority=Priority("urgent"),
            due_date=DateTime("2028-09-07"),
            created_at=DateTime(),
        )

        assert card == card2
        assert card != card3 and card2 != card3
