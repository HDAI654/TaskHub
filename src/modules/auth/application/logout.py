from src.modules.auth.exceptions import InvalidToken
from src.modules.auth.domain.ports.unit_of_work_interface import IUnitOfWork
from src.modules.auth.domain.ports.token_repo_interface import ITokenRepository
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.auth.domain.value_objects.id import ID


class LogoutService:
    def __init__(
        self,
        uow: IUnitOfWork,
        jwt_decoder: JWTDecoder,
    ):
        self.uow = uow
        self.jwt_decoder = jwt_decoder

    async def execute(self, access_token: str, refresh_token: str):
        # Decode and validate access token
        payload = self.jwt_decoder.decode_and_validate(access_token, "access")
