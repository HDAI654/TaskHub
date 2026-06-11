from src.modules.core.base_vo import BaseVO
from src.modules.core.exceptions import InvalidIsCheckedError


class IsChecked(BaseVO[bool]):
    def __init__(self, value: bool | None = False):
        if value is None:
            value = False
        if not isinstance(value, bool):
            raise InvalidIsCheckedError(
                f"IsChecked must be boolean, got {type(value).__name__}"
            )

        super().__init__(value)
