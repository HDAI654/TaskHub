import pytest
from src.modules.card.domain.value_objects.priority import Priority
from src.modules.core.exceptions import InvalidPriorityError


class TestPriority:
    def test_not_str_priority(self):
        with pytest.raises(InvalidPriorityError):
            Priority(25)
            Priority(None)

    def test_empty_str_priority(self):
        with pytest.raises(InvalidPriorityError):
            Priority("")
            Priority(" ")
            Priority("  ")

    def test_priority_strip(self):
        str_priority = "        high  "
        priority = Priority(str_priority)

        assert priority.value == str_priority.strip()

    def test_invalid_priority(self):
        with pytest.raises(InvalidPriorityError):
            Priority("UnacceptablePriority")
