import re
from src.modules.core.base_vo import BaseVO
from src.modules.core.exceptions import InvalidEmailError

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

BLOCKLIST = {
    "mailinator.com",
    "temp-mail.org",
    "guerrillamail.com",
    "10minutemail.com",
    "yopmail.com",
    "trashmail.com",
    "throwawaymail.com",
    "emailondeck.com",
    "mail.tm",
    "tempmail.net",
}


class Email(BaseVO[str]):
    def __init__(self, value: str):
        if not isinstance(value, str):
            raise InvalidEmailError(f"Email must be string, got {type(value).__name__}")
        value = value.strip().lower()
        if not value:
            raise InvalidEmailError("Email must be a non-empty string")
        if (
            not EMAIL_REGEX.match(value)
            or len(value) > 254
            or value.split("@")[1] in BLOCKLIST
        ):
            raise InvalidEmailError("Invalid Email !")

        super().__init__(value)
