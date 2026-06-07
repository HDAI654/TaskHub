from src.modules.auth.domain.ports.token_repo_interface import ITokenRepository
from src.modules.auth.domain.ports.unit_of_work_interface import IUnitOfWork
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.auth.infrastructure.security.jwt_encoder import JWTEncoder
from src.modules.auth.domain.value_objects.id import ID
from src.modules.auth.exceptions import (
    UserNotFoundError,
    InvalidToken
)
import logging

logger = logging.getLogger(__name__)

class TokenRotationService:
    def __init__(
        self,
        uow: IUnitOfWork,
        token_repo: ITokenRepository,
        jwt_decoder: JWTDecoder,
        jwt_encoder: JWTEncoder,
    ):
        self.uow = uow
        self.token_repo = token_repo
        self.jwt_decoder = jwt_decoder
        self.jwt_encoder = jwt_encoder

    async def execute(self, refresh_token: str):
        # Decode and validate access token
        payload = self.jwt_decoder.decode_and_validate(refresh_token, "refresh")
        exp = payload["exp"]

        # Retrieve user and session entities
        try:
            user = await self.uow.users.get_by_id(ID(payload["sub"]))
        except UserNotFoundError:
            logger.warning(
                "Valid token signature for non-existent user_id=%s. Possible token theft.",
                payload["sub"],
            )
            raise

        # check version of token
        current_version = await self.token_repo.get_user_version(user_id=user.id)
        if payload["ver"] != current_version:
            raise InvalidToken("Token is expired")

        # Generate new access token
        new_access = self.jwt_encoder.create_access_token(user.id, current_version)

        # Check if refresh token rotation is needed
        need = self.jwt_encoder.should_rotate_refresh_token(exp)
        if need:
            # Generate new refresh token
            new_refresh = self.jwt_encoder.create_refresh_token(user.id, current_version)
            return new_access, new_refresh

        return new_access, None
