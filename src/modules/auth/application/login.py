import logging
from src.modules.auth.domain.ports.unit_of_work_interface import IUnitOfWork
from src.modules.auth.domain.value_objects.email import Email
from src.modules.auth.infrastructure.security.jwt_encoder import JWTEncoder
from src.modules.auth.infrastructure.security.password_hasher import PasswordHasher
from src.modules.auth.exceptions import InvalidEmailOrPassword

logger = logging.getLogger(__name__)


class LoginService:
    def __init__(
        self,
        uow: IUnitOfWork,
        jwt_encoder: JWTEncoder,
        password_hasher: PasswordHasher,
    ):
        self.uow = uow
        self.jwt_encoder = jwt_encoder
        self.password_hasher = password_hasher

    async def execute(self, email: str, password: str) -> tuple[str, str]:
        logger.info("Logging in user: email=%s", email)
        # Retrieve user by email
        user = await self.uow.users.get_by_email(email=Email(email))

        # Verify password
        if not self.password_hasher.verify(password, user.hashed_password.value):
            raise InvalidEmailOrPassword()

        # Generate access and refresh tokens
        access_token = self.jwt_encoder.create_access_token(user.id)
        refresh_token = self.jwt_encoder.create_refresh_token(user.id)

        logger.info("User logged in successfully: email=%s", email)

        return access_token, refresh_token
