from src.modules.org.domain.entities.project import PrjEntity
from src.modules.org.domain.value_objects.id import ID
from src.modules.org.domain.value_objects.name import Name
from src.modules.org.domain.value_objects.description import Description
from src.modules.org.domain.value_objects.datetime import DateTime


class TestPrjEntity:
    def test_eq_id(self):
        prj = PrjEntity(
            id=ID("MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"),
            org_id=ID("MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"),
            name=Name("Name"),
            description=Description("ExampleDescription"),
            created_at=DateTime(),
        )
        prj2 = PrjEntity(
            id=ID("MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"),
            org_id=ID("MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"),
            name=Name("DifferentName"),
            description=Description("ExampleDescription"),
            created_at=DateTime(),
        )
        prj3 = PrjEntity(
            id=ID("MyDifferentIDDDDDDDDDDDDDDDDDDDDDDDD"),
            org_id=ID("MyDifferentIDDDDDDDDDDDDDDDDDDDDDDDD"),
            name=Name("Name"),
            description=Description("ExampleDescription"),
            created_at=DateTime(),
        )

        assert prj == prj2
        assert prj != prj3 and prj2 != prj3
