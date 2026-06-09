import logging
from src.modules.auth.domain.ports.unit_of_work_interface import IUnitOfWork
from src.modules.auth.domain.ports.token_repo_interface import ITokenRepository
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.core.conf import Config
from src.modules.auth.domain.value_objects.id import ID
from src.modules.auth.domain.value_objects.email import Email
from workers.email_tasks import send_invite_email
from src.modules.auth.exceptions import InvalidToken, UserNotFoundError

logger = logging.getLogger(__name__)


class InviteService:
    def __init__(
        self,
        uow: IUnitOfWork,
        token_repo: ITokenRepository,
        jwt_decoder: JWTDecoder,
    ):
        self.uow = uow
        self.token_repo = token_repo
        self.jwt_decoder = jwt_decoder

    async def execute(self, access_token: str, email: str):
        logger.info("Inviting user")

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
                "Invite failed: user_id=%s not found in database", payload["sub"]
            )
            raise

        # check version of token
        current_version = await self.token_repo.get_user_version(user_id=user.id)
        if payload["ver"] != current_version:
            raise InvalidToken("Access token is expired")

        email = Email(email)

        # Send email
        if Config.APP_ENV != "development":
            send_invite_email.delay(to_email=email.value)

        logger.info("User invited successfully : email=%s", email.value)
