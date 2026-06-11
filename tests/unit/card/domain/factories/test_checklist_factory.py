from src.modules.card.domain.factories.checklist_factory import CheckListFactory


class TestCheckListFactory:
    def test_create_success(self):
        checklist = CheckListFactory.create(
            id="MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD",
            card_id="MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD",
            title="MyTitle",
        )

        assert checklist.id.value == "MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
        assert checklist.card_id.value == "MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
        assert checklist.title.value == "MyTitle"
        assert checklist.is_checked.value == False
