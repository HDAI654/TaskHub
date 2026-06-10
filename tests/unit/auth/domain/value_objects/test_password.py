import pytest
from src.modules.auth.domain.value_objects.password import HashedPassword
from src.modules.core.exceptions import InvalidHashedPasswordError


class TestHashedPassword:
    def test_not_str_hashed_password(self):
        with pytest.raises(InvalidHashedPasswordError):
            HashedPassword(25)
            HashedPassword(None)

    def test_empty_str_hashed_password(self):
        with pytest.raises(InvalidHashedPasswordError):
            HashedPassword("")
            HashedPassword(" ")
            HashedPassword("  ")

    def test_hashed_password_strip(self):
        psw = HashedPassword("      TheHashedValueOfPassword    ")

        assert psw.value == "TheHashedValueOfPassword"

    def test_eq_hashed_password(self):
        password = HashedPassword("MyPassword")
        password2 = HashedPassword("MyPassword")

        assert password == password2
