from src.modules.core.exceptions import InfrastructureError


# DB Exceptions
class DatabaseError(InfrastructureError):
    """Base exception for database errors"""

    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when cannot connect to database"""

    pass


class DatabaseTimeoutError(DatabaseError):
    """Raised when database operation times out"""

    pass


class DatabaseOperationError(DatabaseError):
    """Raised when database operation fails"""

    pass


class NoChangesError(InfrastructureError):
    """No changes provided for update"""

    pass


class OrgException(InfrastructureError):
    """Base Organization error"""

    pass


class OrgNotFoundError(OrgException):
    """Organization not found in database"""

    pass
