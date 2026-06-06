from src.modules.auth.domain.value_objects.id import ID


class TestID:
    def test_none_id(self):
        id = ID(None)
        assert id.value is not None and isinstance(id.value, str)
