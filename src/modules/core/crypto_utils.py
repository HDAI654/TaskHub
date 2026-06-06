import uuid
import base64


class IDGenerationError(Exception):
    """Raised when the IDGenerator.generate() had error"""

    pass


class IDGenerator:
    @staticmethod
    def generate() -> str:
        try:
            return str(uuid.uuid4())
        except Exception as e:
            raise IDGenerationError(
                f"Unexpected error occurred during ID generation:\n{str(e)}"
            ) from e
