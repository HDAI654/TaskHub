import pytest
from datetime import datetime, timezone
from src.modules.org.domain.value_objects.datetime import DateTime
from src.modules.org.exceptions import InvalidDatetimeError


class TestDateTime:
    def test_none_datetime_auto_use_current_time(self):
        dt = DateTime(None)
        assert dt.value != None and isinstance(dt.value, str)

    def test_not_str_datetime(self):
        with pytest.raises(InvalidDatetimeError):
            DateTime(85)
            DateTime(["M", 25])

    def test_empty_str_datetime(self):
        with pytest.raises(InvalidDatetimeError):
            DateTime("")
            DateTime(" ")
            DateTime("  ")

    def test_datetime_strip(self):
        str_datetime = "        1999-05-08  "
        datetime = DateTime(str_datetime)

        assert datetime.value.split("T")[0] == str_datetime.strip()
