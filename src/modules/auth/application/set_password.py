from src.modules.auth.exceptions import (
    InvalidToken,
    InvalidOldPassword,
    WeakPasswordError,
    UserNotFoundError,
)
from src.modules.auth.domain.ports.token_repo_interface import ITokenRepository
from src.modules.auth.domain.ports.unit_of_work_interface import IUnitOfWork
from src.modules.auth.domain.value_objects.id import ID
from src.modules.auth.domain.value_objects.password import HashedPassword
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.auth.infrastructure.security.jwt_encoder import JWTEncoder
from src.modules.auth.infrastructure.security.password_hasher import PasswordHasher
from src.modules.auth.domain.password_strength_checker import (
    PasswordStrengthChecker,
)
import logging

logger = logging.getLogger(__name__)


class SetPassService:
    def __init__(
        self,
        uow: IUnitOfWork,
        token_repo: ITokenRepository,
        jwt_decoder: JWTDecoder,
        jwt_encoder: JWTEncoder,
        password_hasher: PasswordHasher,
    ):
        self.uow = uow
        self.token_repo = token_repo
        self.jwt_decoder = jwt_decoder
        self.jwt_encoder = jwt_encoder
        self.password_hasher = password_hasher

    async def execute(self, access_token: str, old_password: str, new_password: str):
        logging.info("Changing user password")

        # Decode and validate access token
        try:
            payload = self.jwt_decoder.decode_and_validate(access_token, "access")
        except InvalidToken as e:
            logger.warning("access_token was invalid: %s", str(e))
            raise

        # Retrieve user and session entities
        try:
            user = await self.uow.users.get_by_id(ID(payload["sub"]))
        except UserNotFoundError:
            logger.warning(
                "Valid token signature for non-existent user_id=%s. Possible token theft.",
                payload["sub"],
            )
            raise
        if (
            self.password_hasher.verify(
                plain=old_password, hashed=user.hashed_password.value
            )
            is False
        ):
            logger.debug("User entered an incorrect password")
            raise InvalidOldPassword()

        # Validate new password strength
        try:
            PasswordStrengthChecker.validate(new_password)
        except WeakPasswordError:
            logger.debug("The new-password was weak")
            raise

        # Hash the new password
        hashed_password = self.password_hasher.hash(new_password)
        new_password_vo = HashedPassword(hashed_password)

        # Update user password
        try:
            await self.uow.users.update(id=user.id, new_password=new_password_vo)
        except Exception:
            await self.uow.rollback()
            logger.error("Updating user failed: public_id=%s", user.id.value)
            raise

        await self.uow.commit()

        # Increment user version to force re-authentication on other devices
        await self.token_repo.increment_user_version(user_id=user.id)

        # Generate access and refresh tokens
        new_access_token = self.jwt_encoder.create_access_token(user.id)
        new_refresh_token = self.jwt_encoder.create_refresh_token(user.id)

        logger.info("User password changed successfully: public_id=%s", user.id)

        return new_access_token, new_refresh_token
