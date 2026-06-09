from src.modules.core.base_vo import BaseVO
from src.modules.org.exceptions import InvalidRoleError

ACCEPTABLE_ROLES = {"owner", "admin", "member", "viewer"}


class Role(BaseVO[str]):
    def __init__(self, value: str):
        if not isinstance(value, str):
            raise InvalidRoleError(f"Role must be string, got {type(value).__name__}")
        value = value.strip()
        if not value:
            raise InvalidRoleError(f"Role must be a non-empty string")

        if value not in ACCEPTABLE_ROLES:
            raise InvalidRoleError(
                f"Invalid role '{value}'. Must be one of: {', '.join(ACCEPTABLE_ROLES)}"
            )

        super().__init__(value)
