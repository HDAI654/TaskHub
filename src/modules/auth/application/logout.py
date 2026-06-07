import logging
from src.modules.auth.domain.ports.unit_of_work_interface import IUnitOfWork
from src.modules.auth.domain.ports.token_repo_interface import ITokenRepository
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.auth.domain.value_objects.id import ID
from src.modules.auth.exceptions import InvalidToken, UserNotFoundError

logger = logging.getLogger(__name__)


class LogoutService:
    def __init__(
        self,
        uow: IUnitOfWork,
        token_repo: ITokenRepository,
        jwt_decoder: JWTDecoder,
    ):
        self.uow = uow
        self.token_repo = token_repo
        self.jwt_decoder = jwt_decoder

    async def execute(self, access_token: str, refresh_token: str):
        logger.info("Logging out user")
        # Decode and validate access token and refresh token
        try:
            access_payload = self.jwt_decoder.decode_and_validate(
                access_token, "access"
            )
        except InvalidToken as e:
            logger.warning("access_token was invalid: %s", str(e))
            raise
        try:
            refresh_payload = self.jwt_decoder.decode_and_validate(
                refresh_token, "refresh"
            )
        except InvalidToken as e:
            logger.warning("refresh_token was invalid: %s", str(e))
            raise

        if access_payload["sub"] != refresh_payload["sub"]:
            logger.warning(
                "Token user mismatch detected: access_token refers to user_id=%s, refresh_token refers to user_id=%s",
                access_payload["sub"],
                refresh_payload["sub"],
            )
            raise InvalidToken(
                "Access token and Refresh token are invalid or has wrong data"
            )

        # check user does exist
        try:
            await self.uow.users.get_by_id(ID(access_payload["sub"]))
        except UserNotFoundError:
            logger.warning(
                "Logout failed: user_id=%s not found in database", access_payload["sub"]
            )
            raise

        # Add tokens to blacklist
        await self.token_repo.block_token(
            token_id=ID(access_payload["jti"]), expires_at=access_payload["exp"]
        )
        await self.token_repo.block_token(
            token_id=ID(refresh_payload["jti"]), expires_at=refresh_payload["exp"]
        )
        logger.info("User logged out successfully")
