from src.modules.org.domain.entities.organization import OrgEntity
from src.modules.org.domain.value_objects.id import ID
from src.modules.org.domain.value_objects.name import Name
from src.modules.org.domain.value_objects.datetime import DateTime


class TestOrgEntity:
    def test_eq_id(self):
        org = OrgEntity(
            id=ID("MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"),
            name=Name("Name"),
            created_at=DateTime()
        )
        org2 = OrgEntity(
            id=ID("MyIDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"),
            name=Name("DifferentName"),
            created_at=DateTime()
        )
        org3 = OrgEntity(
            id=ID("MyDifferentIDDDDDDDDDDDDDDDDDDDDDDDD"),
            name=Name("Name"),
            created_at=DateTime()
        )

        assert org == org2
        assert org != org3 and org2 != org3
