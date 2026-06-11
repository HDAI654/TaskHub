from src.modules.card.domain.factories.card_factory import CardFactory


class TestCardFactory:
    def test_create_success(self):
        card = CardFactory.create(
            id="MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD",
            description="ExampleDescription",
            column_id="MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD",
            created_by_user_id="MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD",
            title="ExampleTitle",
            priority="high",
            due_date="1990-08-07",
        )

        assert card.id.value == "MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
        assert card.description.value == "ExampleDescription"
        assert card.column_id.value == "MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
        assert card.created_by_user_id.value == "MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
        assert card.title.value == "ExampleTitle"
        assert card.description.value == "ExampleDescription"
        assert card.priority.value == "high"
        assert card.due_date.value == "1990-08-07T00:00:00"
