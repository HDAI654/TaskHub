from src.modules.core.exceptions import InvalidHashedPasswordError


class HashedPassword:
    def __init__(self, hashed_value: str):
        if not isinstance(hashed_value, str):
            raise InvalidHashedPasswordError(
                f"HashedPassword must be string, got {type(hashed_value).__name__}"
            )
        hashed_value = hashed_value.strip()
        if not hashed_value:
            raise InvalidHashedPasswordError(
                "HashedPassword must be a non-empty string"
            )
        self._hashed = hashed_value

    @property
    def value(self):
        return self._hashed

    def __str__(self) -> str:
        return "*" * len(self.value)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__str__()!r})"

    def __eq__(self, other):
        return isinstance(other, HashedPassword) and self.value == other.value

    def __hash__(self) -> int:
        return hash((self.__class__, self.value))
