import bcrypt
from src.modules.auth.exceptions import PasswordHasherError


class PasswordHasher:
    def hash(self, password: str) -> str:
        """Hash a password using bcrypt with automatic salt generation"""
        if not isinstance(password, str):
            raise TypeError(
                f"PasswordHasher.hash() argument 'password' must be string, got {type(password).__name__}"
            )
        if not password:
            raise ValueError("Password cannot be empty")

        try:

            password_bytes = password.encode("utf-8")
            hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())

            return hashed.decode("utf-8")
        except Exception as e:
            raise PasswordHasherError(
                f"Unexpected error occurred during hashing password:\n{str(e)}"
            ) from e

    def verify(self, plain: str, hashed: str) -> bool:
        """Verify a plain password against a bcrypt hash"""
        if not isinstance(plain, str):
            raise TypeError(
                f"PasswordHasher.verify() argument 'plain' must be string, got {type(plain).__name__}"
            )
        if not isinstance(hashed, str):
            raise TypeError(
                f"PasswordHasher.verify() argument 'hashed' must be string, got {type(hashed).__name__}"
            )

        try:
            plain_bytes = plain.encode("utf-8")
            hashed_bytes = hashed.encode("utf-8")
            return bcrypt.checkpw(plain_bytes, hashed_bytes)
        except Exception as e:
            raise PasswordHasherError(
                f"Unexpected error occurred during verifying password:\n{str(e)}"
            ) from e
