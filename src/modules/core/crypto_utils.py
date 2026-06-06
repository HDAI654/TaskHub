import uuid
import base64


class IDGenerationError(Exception):
    """Raised when the IDGenerator.generate() had error"""

    pass


class IDGenerator:
    @staticmethod
    def generate() -> str:
        try:
            u = uuid.uuid4()
            ubytes = u.bytes
            id = base64.urlsafe_b64encode(ubytes).decode("utf-8").rstrip("=")
            return id

        except Exception as e:
            raise IDGenerationError(
                f"Unexpected error occurred during ID generation:\n{str(e)}"
            ) from e
