import bcrypt
from src.modules.auth.exceptions import PasswordHasherError
import logging

logger = logging.getLogger(__name__)


class PasswordHasher:
    def hash(self, password: str) -> str:
        """Hash a password using bcrypt with automatic salt generation"""
        logger.info("hashing password")
        if not isinstance(password, str):
            logger.warning(
                "PasswordHasher.hash() argument 'password' must be string, got %s",
                type(password).__name__,
            )
            raise TypeError(
                f"PasswordHasher.hash() argument 'password' must be string, got {type(password).__name__}"
            )
        if not password:
            logger.warning("Password cannot be empty")
            raise ValueError("Password cannot be empty")

        try:
            password_bytes = password.encode("utf-8")
            hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
            hashed = hashed.decode("utf-8")
            logger.info("Password hashed sucessfully")
            return hashed
        except Exception as e:
            logger.exception("Unexpected error occurred during hashing password")
            raise PasswordHasherError(
                f"Unexpected error occurred during hashing password:\n{str(e)}"
            ) from e

    def verify(self, plain: str, hashed: str) -> bool:
        """Verify a plain password against a bcrypt hash"""
        logger.info("Verifying password")
        if not isinstance(plain, str):
            logger.warning(
                "PasswordHasher.verify() argument 'plain' must be string, got %s",
                type(plain).__name__,
            )
            raise TypeError(
                f"PasswordHasher.verify() argument 'plain' must be string, got {type(plain).__name__}"
            )
        if not isinstance(hashed, str):
            logger.warning(
                "PasswordHasher.verify() argument 'hashed' must be string, got %s",
                type(hashed).__name__,
            )
            raise TypeError(
                f"PasswordHasher.verify() argument 'hashed' must be string, got {type(hashed).__name__}"
            )

        try:
            plain_bytes = plain.encode("utf-8")
            hashed_bytes = hashed.encode("utf-8")

            result = bcrypt.checkpw(plain_bytes, hashed_bytes)
            logger.info("Password checked successfully: result=%s", result)
            return result
        except Exception as e:
            logger.exception("Unexpected error occurred during verifying password")
            raise PasswordHasherError(
                f"Unexpected error occurred during verifying password:\n{str(e)}"
            ) from e
