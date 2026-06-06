from src.modules.core.entity import Entity
from src.modules.auth.domain.value_objects.id import ID
from src.modules.auth.domain.value_objects.email import Email
from src.modules.auth.domain.value_objects.password import HashedPassword


class UserEntity(Entity):
    def __init__(
        self,
        id: ID,
        email: Email,
        password: HashedPassword,
    ):
        self.id = id
        self.email = email
        self.password = password

        super().__init__()
