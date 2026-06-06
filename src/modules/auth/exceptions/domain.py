from src.modules.core.exceptions import DomainError


class InvalidHashedPasswordError(DomainError):
    pass


class InvalidEmailError(DomainError):
    pass


class InvalidDateError(DomainError):
    pass
