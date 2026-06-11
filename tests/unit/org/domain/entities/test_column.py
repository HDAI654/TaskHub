from src.modules.org.domain.entities.column import ColumnEntity
from src.modules.org.domain.value_objects.id import ID
from src.modules.org.domain.value_objects.name import Name
from src.modules.org.domain.value_objects.order import Order


class TestColumnEntity:
    def test_eq_id(self):
        column = ColumnEntity(
            id=ID("MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"),
            board_id=ID("MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"),
            name=Name("ExampleName"),
            order=Order(4),
        )
        column2 = ColumnEntity(
            id=ID("MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"),
            board_id=ID("MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"),
            name=Name("ExampleName"),
            order=Order(5),
        )
        column3 = ColumnEntity(
            id=ID("MyDifferentIDDDDDDDDDDDDDDDDDDDDDDDD"),
            board_id=ID("MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"),
            name=Name("ExampleName"),
            order=Order(0),
        )

        assert column == column2
        assert column != column3 and column2 != column3
