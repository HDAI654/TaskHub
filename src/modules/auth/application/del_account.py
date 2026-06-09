import logging
from src.modules.auth.domain.ports.unit_of_work_interface import IUnitOfWork
from src.modules.auth.domain.ports.token_repo_interface import ITokenRepository
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.auth.domain.value_objects.id import ID
from src.modules.auth.exceptions import InvalidToken, UserNotFoundError

logger = logging.getLogger(__name__)


class DelAccountService:
    def __init__(
        self,
        uow: IUnitOfWork,
        token_repo: ITokenRepository,
        jwt_decoder: JWTDecoder,
    ):
        self.uow = uow
        self.token_repo = token_repo
        self.jwt_decoder = jwt_decoder

    async def execute(self, access_token: str):
        logger.info("Deleting user account")
        # Decode and validate refresh token
        access_payload = self.jwt_decoder.decode_and_validate(access_token, "access")

        # check user does exist
        try:
            user = await self.uow.users.get_by_id(ID(access_payload["sub"]))
        except UserNotFoundError:
            logger.warning(
                "Delete account failed: user_id=%s not found in database",
                access_payload["sub"],
            )
            raise

        # check version of token
        current_version = await self.token_repo.get_user_version(user_id=user.id)
        is_token_blocked = await self.token_repo.is_token_blocked(
            ID(access_payload["jti"])
        )
        if access_payload["ver"] != current_version or is_token_blocked:
            raise InvalidToken("Access token is expired")

        # Delete user account
        try:
            await self.uow.users.delete(user.id)
        except Exception:
            await self.uow.rollback()
            logger.error("Delete account failed: user_id=%s", user.id.value)
            raise
        await self.uow.commit()

        # Invalidate all user's tokens
        await self.token_repo.increment_user_version(user.id)

        logger.info("User account deleted successfully")
