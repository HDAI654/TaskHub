import pytest
from src.modules.org.domain.value_objects.role import Role
from src.modules.org.exceptions import InvalidRoleError


class TestRole:
    def test_not_str_role(self):
        with pytest.raises(InvalidRoleError):
            Role(25)
            Role(None)

    def test_empty_str_role(self):
        with pytest.raises(InvalidRoleError):
            Role("")
            Role(" ")
            Role("  ")

    def test_role_strip(self):
        str_role = "        viewer  "
        role = Role(str_role)

        assert role.value == str_role.strip()

    def test_invalid_role(self):
        with pytest.raises(InvalidRoleError):
            Role("UnacceptableRole")
