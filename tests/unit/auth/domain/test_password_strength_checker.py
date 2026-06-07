import pytest
from src.modules.auth.domain.password_strength_checker import PasswordStrengthChecker
from src.modules.auth.exceptions import WeakPasswordError


class TestPasswordStrengthChecker:
    @pytest.mark.parametrize(
        "password,should_pass",
        [
            # Valid passwords
            ("StrongP@ss1", True),
            ("MySecureP@ssw0rd", True),
            ("Test123!@#Aa", True),
            # Invalid: too short
            ("Sh0@rt", False),
            ("A1@b", False),
            # Invalid: too long
            ("A" * PasswordStrengthChecker.PASSWORD_MAX_LENGTH + "1@aA", False),
            # Invalid: no uppercase
            ("weakp@ss1", False),
            # Invalid: no lowercase
            ("WEAKP@SS1", False),
            # Invalid: no number
            ("NoNumber@P", False),
            # Invalid: no special char
            ("NoSpecialA1", False),
            # Invalid: empty
            ("", False),
        ],
    )
    def test_password_validation(self, password, should_pass):
        if should_pass:
            PasswordStrengthChecker.validate(password)
            assert PasswordStrengthChecker.is_strong(password) is True
        else:
            with pytest.raises(WeakPasswordError):
                PasswordStrengthChecker.validate(password)
            assert PasswordStrengthChecker.is_strong(password) is False

    def test_get_error_returns_none_for_valid_password(self):
        error = PasswordStrengthChecker.get_error("ValidP@ss1")
        assert error is None

    def test_get_error_returns_message_for_invalid_password(self):
        error = PasswordStrengthChecker.get_error("weak")
        assert error is not None
        assert "at least" in error
