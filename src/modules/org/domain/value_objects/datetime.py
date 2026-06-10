from src.modules.core.base_vo import BaseVO
from datetime import datetime, timezone
from src.modules.core.exceptions import InvalidDatetimeError


class DateTime(BaseVO[str]):
    def __init__(self, value: str = None):
        if value is None:
            value = datetime.now(timezone.utc).isoformat()
        else:
            if not isinstance(value, str):
                raise InvalidDatetimeError(
                    f"DateTime must be string, got {type(value).__name__}"
                )
            value = value.strip()
            if not value:
                raise InvalidDatetimeError(f"DateTime must be a non-empty string")
            try:
                value = datetime.fromisoformat(value).isoformat()
            except:
                raise InvalidDatetimeError("DateTime got invalid value")

        super().__init__(value)
