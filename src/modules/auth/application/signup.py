import logging
from src.modules.auth.domain.ports.unit_of_work_interface import IUnitOfWork
from src.modules.auth.domain.factories.user_factory import UserFactory
from src.modules.auth.infrastructure.security.jwt_encoder import JWTEncoder
from src.modules.auth.infrastructure.security.password_hasher import PasswordHasher
from src.modules.auth.domain.password_strength_checker import (
    PasswordStrengthChecker,
)

logger = logging.getLogger(__name__)

class SignupService:
    def __init__(
        self,
        uow: IUnitOfWork,
        jwt_encoder: JWTEncoder,
        password_hasher: PasswordHasher,
    ):
        self.uow = uow
        self.jwt_encoder = jwt_encoder
        self.password_hasher = password_hasher

    async def execute(self, email: str, password: str):
        logger.info("Signing up user: email=%s", email)
        # Validate new password strength
        PasswordStrengthChecker.validate(password=password)

        # Hash the password
        hashed_password = self.password_hasher.hash(str(password))

        # Create new user
        user = UserFactory.create(email=email, hashed_password=hashed_password)
        try:
            await self.uow.users.add(user)
        except Exception:
            await self.uow.rollback()
            logger.error("Adding user to DB failed: email=%s", email)
            raise    
        await self.uow.commit()

        # Generate access and refresh tokens
        access_token = self.jwt_encoder.create_access_token(user.id)
        refresh_token = self.jwt_encoder.create_refresh_token(user.id)

        logger.info("User signed up successfully: email=%s", email)

        return access_token, refresh_token
