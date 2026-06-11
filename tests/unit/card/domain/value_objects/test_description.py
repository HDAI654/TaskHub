import pytest
from src.modules.card.domain.value_objects.description import Description
from src.modules.core.exceptions import InvalidDescriptionError


class TestDescription:
    def test_not_str_description(self):
        with pytest.raises(InvalidDescriptionError):
            Description(25)
            Description(None)

    def test_empty_str_description(self):
        with pytest.raises(InvalidDescriptionError):
            Description("")
            Description(" ")
            Description("  ")

    def test_description_strip(self):
        str_description = "        description  "
        description = Description(str_description)

        assert description.value == str_description.strip()
