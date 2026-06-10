class ApplicationError(Exception):
    """Base application error"""

    pass

class InvalidEmailOrPassword(ApplicationError):
    """Raised when email/password combination is invalid"""

    pass


class InvalidOldPassword(ApplicationError):
    """Raised when old-password is invalid"""

    pass


class PermissionDenied(ApplicationError):
    """Raised when user lacks permission to perform the requested action"""

    pass
