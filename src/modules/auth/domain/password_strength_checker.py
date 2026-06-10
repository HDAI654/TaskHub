import re
from src.modules.core.exceptions import WeakPasswordError


class PasswordStrengthChecker:
    """Password strength validation"""

    PASSWORD_MIN_LENGTH = 8
    PASSWORD_MAX_LENGTH = 50

    @staticmethod
    def validate(password: str) -> None:
        """Validate password strength, raise WeakPasswordError if invalid"""
        error = PasswordStrengthChecker.get_error(password)
        if error is not None:
            raise WeakPasswordError(error)

    @staticmethod
    def is_strong(password: str) -> bool:
        """Return True if password meets strength requirements"""
        return PasswordStrengthChecker.get_error(password) is None

    @staticmethod
    def get_error(password: str) -> str | None:
        """Get validation error"""
        if not password or len(password) < PasswordStrengthChecker.PASSWORD_MIN_LENGTH:
            return f"Password must be at least {PasswordStrengthChecker.PASSWORD_MIN_LENGTH} characters"

        if len(password) > PasswordStrengthChecker.PASSWORD_MAX_LENGTH:
            return f"Password must be less than {PasswordStrengthChecker.PASSWORD_MAX_LENGTH} characters"

        if not re.search(r"[A-Z]", password):
            return "Password must contain at least one uppercase letter"

        if not re.search(r"[a-z]", password):
            return "Password must contain at least one lowercase letter"

        if not re.search(r"[0-9]", password):
            return "Password must contain at least one number"

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return "Password must contain at least one special character"

        return None
