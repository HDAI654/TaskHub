import pytest
from src.modules.org.domain.value_objects.order import Order
from src.modules.core.exceptions import InvalidOrderError


class TestOrder:
    def test_not_int_order(self):
        with pytest.raises(InvalidOrderError):
            Order("ABC")
            Order(None)
