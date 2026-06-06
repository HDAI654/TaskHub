from src.modules.core.exceptions import InfrastructureError

# ===== JWT Exceptions =====
class TokenCreationError(InfrastructureError):

    pass


# ===== Hasher Exceptions =====
class PasswordHasherError(InfrastructureError):

    pass