import pytest
from datetime import datetime, timezone
from src.modules.org.domain.value_objects.datetime import DateTime
from src.modules.org.exceptions import InvalidDatetimeError

class TestDateTime:
    def test_none_datetime_auto_use_current_time(self):
        dt = DateTime(None)
        assert dt.value != None and isinstance(dt.value, float)

    def test_not_float_or_int_datetime(self):
        with pytest.raises(InvalidDatetimeError):
            DateTime("25")
            DateTime(["M", 25])

    def test_zero_and_negative_datetime(self):
        with pytest.raises(InvalidDatetimeError):
            DateTime(0)
            DateTime(-1)

    def test_int_datetime_auto_convert_to_float(self):
        dt = DateTime(1236457800.0)
        dt2 = DateTime(1236457800)
        assert dt.value == dt2.value
