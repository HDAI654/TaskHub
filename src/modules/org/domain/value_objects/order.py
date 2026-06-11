from src.modules.core.base_vo import BaseVO
from src.modules.core.exceptions import InvalidOrderError


class Order(BaseVO[int]):
    def __init__(self, value: int):
        if not isinstance(value, int):
            raise InvalidOrderError(
                f"Order must be integer, got {type(value).__name__}"
            )

        super().__init__(value)
