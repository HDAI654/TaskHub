from src.modules.core.base_vo import BaseVO
from src.modules.core.exceptions import InvalidTitleError


class Title(BaseVO[str]):
    def __init__(self, value: str):
        if not isinstance(value, str):
            raise InvalidTitleError(f"Title must be string, got {type(value).__name__}")
        value = value.strip()
        if not value:
            raise InvalidTitleError(f"Title must be a non-empty string")
        if len(value) > 500:
            raise InvalidTitleError(f"Title is so long !")

        super().__init__(value)
