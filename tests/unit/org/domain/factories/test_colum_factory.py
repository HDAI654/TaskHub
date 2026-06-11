from src.modules.org.domain.factories.column_factory import ColumnFactory


class TestColumnFactory:
    def test_create_success(self):
        prj = ColumnFactory.create(
            id="MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD",
            board_id="MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD",
            name="OrgName",
            order=3,
        )

        assert prj.id.value == "MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
        assert prj.board_id.value == "MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
        assert prj.name.value == "OrgName"
        assert prj.order.value == 3
