from src.modules.org.domain.entities.board import BoardEntity
from src.modules.org.domain.value_objects.id import ID
from src.modules.org.domain.value_objects.name import Name
from src.modules.org.domain.value_objects.description import Description
from src.modules.org.domain.value_objects.datetime import DateTime


class TestBoardEntity:
    def test_eq_id(self):
        board = BoardEntity(
            id=ID("MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"),
            prj_id=ID("MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"),
            description=Description("ExampleDescription"),
            name=Name("Name"),
            created_at=DateTime(),
        )
        board2 = BoardEntity(
            id=ID("MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"),
            prj_id=ID("MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"),
            description=Description("ExampleDescription"),
            name=Name("DifferentName"),
            created_at=DateTime(),
        )
        board3 = BoardEntity(
            id=ID("MyDifferentIDDDDDDDDDDDDDDDDDDDDDDDD"),
            prj_id=ID("MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"),
            description=Description("ExampleDescription"),
            name=Name("Name"),
            created_at=DateTime(),
        )

        assert board == board2
        assert board != board3 and board2 != board3
