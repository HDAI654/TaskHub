import pytest
from src.modules.card.domain.value_objects.is_checked import IsChecked
from src.modules.core.exceptions import InvalidIsCheckedError


class TestIsChecked:
    def test_is_checked_with_none(self):
        vo = IsChecked(None)
        assert vo.value is False

    def test_not_bool_is_checked(self):
        with pytest.raises(InvalidIsCheckedError):
            IsChecked(25)
            IsChecked("ABC")
