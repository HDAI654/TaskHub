from src.modules.auth.domain.ports.unit_of_work_interface import IUnitOfWork
from src.modules.auth.domain.ports.token_repo_interface import ITokenRepository
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.auth.domain.value_objects.id import ID
from src.modules.auth.exceptions import InvalidToken


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
        # Decode and validate access token and refresh token
        access_payload = self.jwt_decoder.decode_and_validate(access_token, "access")
        refresh_payload = self.jwt_decoder.decode_and_validate(refresh_token, "refresh")

        if access_payload['sub'] != refresh_payload['sub']:
            raise InvalidToken("Access token and Refresh token are invalid or has wrong data")
        
        # check user does exist
        await self.uow.users.get_by_id(ID(access_payload['sub']))
        
        # Add tokens to blacklist
        await self.token_repo.block_token(token_id=ID(access_payload['jti']), expires_at=access_payload['exp'])
        await self.token_repo.block_token(token_id=ID(refresh_payload['jti']), expires_at=refresh_payload['exp'])
