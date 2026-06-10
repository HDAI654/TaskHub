from src.modules.org.domain.factories.board_factory import BoardFactory


class TestBoardFactory:
    def test_create_success(self):
        prj = BoardFactory.create(
            id="MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD",
            prj_id="MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD",
            name="OrgName",
            description="ExampleDescription",
        )

        assert prj.id.value == "MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
        assert prj.prj_id.value == "MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
        assert prj.name.value == "OrgName"
        assert prj.description.value == "ExampleDescription"
