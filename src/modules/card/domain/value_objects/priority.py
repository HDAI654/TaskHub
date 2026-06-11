from src.modules.core.base_vo import BaseVO
from src.modules.core.exceptions import InvalidPriorityError

ACCEPTABLE_PRIORITY = {"low", "medium", "high", "urgent"}


class Priority(BaseVO[str]):
    def __init__(self, value: str):
        if not isinstance(value, str):
            raise InvalidPriorityError(
                f"Priority must be string, got {type(value).__name__}"
            )
        value = value.strip()
        if not value:
            raise InvalidPriorityError(f"Priority must be a non-empty string")

        if value not in ACCEPTABLE_PRIORITY:
            raise InvalidPriorityError(
                f"Invalid priority '{value}'. Must be one of: {', '.join(ACCEPTABLE_PRIORITY)}"
            )

        super().__init__(value)
