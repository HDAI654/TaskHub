from src.modules.card.domain.factories.label_factory import LabelFactory


class TestLabelFactory:
    def test_create_success(self):
        label = LabelFactory.create(
            id="MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD",
            name="Slim Shady",
        )

        assert label.id.value == "MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
        assert label.name.value == "Slim Shady"
