import logging
from src.modules.auth.domain.ports.unit_of_work_interface import IUnitOfWork
from src.modules.auth.domain.ports.password_reset_repo_interface import (
    IPasswordResetRepository,
)
from src.modules.auth.domain.ports.token_repo_interface import ITokenRepository
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.auth.domain.value_objects.id import ID
from src.modules.core.exceptions import InvalidToken, UserNotFoundError
from src.modules.core.crypto_utils import IDGenerator
from src.modules.core.conf import Config
from workers.email_tasks import send_password_reset_email

logger = logging.getLogger(__name__)


class ResetPassTokenPublishService:
    def __init__(
        self,
        uow: IUnitOfWork,
        res_pass_repo: IPasswordResetRepository,
        token_repo: ITokenRepository,
        jwt_decoder: JWTDecoder,
    ):
        self.uow = uow
        self.res_pass_repo = res_pass_repo
        self.token_repo = token_repo
        self.jwt_decoder = jwt_decoder

    async def execute(self, access_token: str):
        logger.info("Publishing user reset password token")
        try:
            payload = self.jwt_decoder.decode_and_validate(access_token, "access")
        except InvalidToken as e:
            logger.warning("access_token was invalid: %s", str(e))
            raise

        # check user does exist
        try:
            user = await self.uow.users.get_by_id(ID(payload["sub"]))
        except UserNotFoundError:
            logger.warning(
                "Logout failed: user_id=%s not found in database", payload["sub"]
            )
            raise

        # check version of token
        current_version = await self.token_repo.get_user_version(user_id=user.id)
        is_token_blocked = await self.token_repo.is_token_blocked(ID(payload["jti"]))
        if payload["ver"] != current_version or is_token_blocked:
            raise InvalidToken("Access token is expired")

        token = IDGenerator.generate()
        await self.res_pass_repo.add(token, user.id)

        # Send email
        if Config.APP_ENV != "development":
            send_password_reset_email.delay(
                to_email=user.email.value, token=token, expires_in_minutes=15
            )

        logger.info("Token Published successfully: user_public_id=%s", user.id.value)
