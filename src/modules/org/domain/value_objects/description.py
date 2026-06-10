from src.modules.core.base_vo import BaseVO
from src.modules.core.exceptions import InvalidDescriptionError


class Description(BaseVO[str]):
    def __init__(self, value: str):
        if not isinstance(value, str):
            raise InvalidDescriptionError(
                f"Description must be string, got {type(value).__name__}"
            )
        value = value.strip()
        if not value:
            raise InvalidDescriptionError(f"Description must be a non-empty string")

        super().__init__(value)
