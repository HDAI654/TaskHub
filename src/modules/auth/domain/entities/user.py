from src.modules.core.entity import Entity
from src.modules.auth.domain.value_objects.id import ID
from src.modules.auth.domain.value_objects.email import Email
from src.modules.auth.domain.value_objects.password import HashedPassword


class UserEntity(Entity):
    def __init__(
        self,
        id: ID,
        email: Email,
        hashed_password: HashedPassword,
    ):
        self.id = id
        self.email = email
        self.hashed_password = hashed_password

        super().__init__()
