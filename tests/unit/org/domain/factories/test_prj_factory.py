from src.modules.org.domain.factories.project_factory import PrjFactory


class TestPrjFactory:
    def test_create_success(self):
        prj = PrjFactory.create(
            id="MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD",
            name="OrgName",
            description="ExampleDescription",
        )

        assert prj.id.value == "MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
        assert prj.name.value == "OrgName"
        assert prj.description.value == "ExampleDescription"
