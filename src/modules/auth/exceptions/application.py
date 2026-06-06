from src.modules.core.exceptions import ApplicationError


class InvalidEmailOrPassword(ApplicationError):
    """Raised when email/password combination is invalid"""

    pass


class PermissionDenied(ApplicationError):
    """Raised when user lacks permission to perform the requested action"""

    pass
