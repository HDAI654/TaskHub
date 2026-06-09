from src.modules.org.domain.factories.organization_factory import OrgFactory


class TestUserFactory:
    def test_create_success(self):
        org = OrgFactory.create(
            id="MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD",
            name="OrgName",
        )

        assert org.id.value == "MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
        assert org.name.value == "OrgName"
