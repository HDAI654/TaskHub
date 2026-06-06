from src.modules.core.crypto_utils import IDGenerator
from src.modules.core.id_vo import ID


class ID(ID):
    def __init__(self, value: str | None = None):
        if value is None:
            value = IDGenerator.generate()
        super().__init__(value)
