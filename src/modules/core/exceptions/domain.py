class DomainError(Exception):
    """Base domain error"""

    pass


# ===== VO Exceptions =====
class InvalidIDError(DomainError):
    pass


class InvalidHashedPasswordError(DomainError):
    pass


class InvalidEmailError(DomainError):
    pass


class InvalidDatetimeError(DomainError):
    pass


class InvalidNameError(DomainError):
    pass


class InvalidRoleError(DomainError):
    pass


class InvalidDescriptionError(DomainError):
    pass


# ===== Password Checker Exceptions =====
class WeakPasswordError(DomainError):
    """Raised when password doesn't meet strength requirements"""

    pass
