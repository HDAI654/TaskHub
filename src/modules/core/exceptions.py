class DomainError(Exception):
    """Base domain error"""

    pass


class InvalidIDError(DomainError):
    pass


class InfrastructureError(Exception):
    """Base infrastructure error"""

    pass


class ApplicationError(Exception):
    """Base application error"""

    pass


class InvalidToken(Exception):

    pass
