from src.modules.card.domain.entities.label import LabelEntity
from src.modules.card.domain.value_objects.id import ID
from src.modules.card.domain.value_objects.name import Name


class TestLabelEntity:
    def test_eq_id(self):
        label = LabelEntity(
            id=ID("MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"),
            name=Name("The Name"),
        )
        label2 = LabelEntity(
            id=ID("MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"),
            name=Name("The Name"),
        )
        label3 = LabelEntity(
            id=ID("MyDifferentIDDDDDDDDDDDDDDDDDDDDDDDD"),
            name=Name("The Name"),
        )

        assert label == label2
        assert label != label3 and label2 != label3
