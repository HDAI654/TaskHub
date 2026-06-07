from src.modules.core.exceptions import DomainError


class InvalidHashedPasswordError(DomainError):
    pass


class InvalidEmailError(DomainError):
    pass


# ===== Password Checker Exceptions =====
class WeakPasswordError(DomainError):
    """Raised when password doesn't meet strength requirements"""

    pass
