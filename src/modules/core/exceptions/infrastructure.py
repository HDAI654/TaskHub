class InfrastructureError(Exception):
    """Base infrastructure error"""

    pass


# ===== DB Exceptions =====
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


# User Exceptions
class UserException(InfrastructureError):
    """Base User error"""

    pass


class UserNotFoundError(UserException):
    """User not found in database"""

    pass


class UserDuplicateError(UserException):
    """User with same unique field exists"""

    pass


# Org Exceptions
class OrgException(InfrastructureError):
    """Base Organization error"""

    pass


class OrgNotFoundError(OrgException):
    """Organization not found in database"""

    pass


class MemberNotFoundError(OrgException):
    """Member not found in database"""

    pass


class MemberDuplicateError(OrgException):
    """Member with same unique field exists"""

    pass


# ===== Cache Exceptions =====
class CacheError(Exception):
    """Base exception for all cache infrastructure failures"""

    pass


class CacheConnectionError(CacheError):
    """Raised when cannot connect to cache"""

    pass


class CacheTimeoutError(CacheError):
    """Raised when cache operation times out"""

    pass


class CacheOperationError(CacheError):
    """Raised when cache operation fails"""

    pass


# ===== JWT Exceptions =====
class TokenCreationError(InfrastructureError):

    pass


class InvalidToken(InfrastructureError):

    pass


# ===== Hasher Exceptions =====
class PasswordHasherError(InfrastructureError):

    pass
