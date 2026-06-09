from src.modules.core.base_vo import BaseVO
from datetime import datetime, timezone
from src.modules.org.exceptions import InvalidDatetimeError


class DateTime(BaseVO[float]):
    def __init__(self, value: float | int = None):
        if value is None:
            value = datetime.now(timezone.utc)
        else:
            value = float(value) if isinstance(value, int) else value
            if not isinstance(value, float):
                raise InvalidDatetimeError(
                    f"DateTime must be float or integer, got {type(value).__name__}"
                )
            if value <= 0:
                raise InvalidDatetimeError("DateTime must be positive")
            try:
                value = datetime.fromtimestamp(value, timezone.utc)
            except:
                raise InvalidDatetimeError("DateTime got invalid value")
        
        super().__init__(value)

    @property
    def value(self) -> float:
        return self._value.timestamp()
