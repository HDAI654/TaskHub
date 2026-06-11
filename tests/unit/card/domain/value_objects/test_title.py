import pytest
from src.modules.card.domain.value_objects.title import Title
from src.modules.core.exceptions import InvalidTitleError


class TestTitle:
    def test_not_str_title(self):
        with pytest.raises(InvalidTitleError):
            Title(25)
            Title(None)

    def test_empty_str_title(self):
        with pytest.raises(InvalidTitleError):
            Title("")
            Title(" ")
            Title("  ")

    def test_title_strip(self):
        str_title = "        title  "
        title = Title(str_title)

        assert title.value == str_title.strip()

    def test_long_title(self):
        with pytest.raises(InvalidTitleError):
            Title("Mytitle" + "ABC" * 400)
