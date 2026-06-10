import logging
from src.modules.auth.domain.ports.token_repo_interface import ITokenRepository
from src.modules.core.id_vo import ID

logger = logging.getLogger(__name__)


class TokenToolsService:
    def __init__(
        self,
        token_repo: ITokenRepository,
    ):
        self.token_repo = token_repo

    async def execute(self, token_id: str, user_id: str):
        logger.info("TokenToolsService started")

        is_token_blocked = await self.token_repo.is_token_blocked(token_id=ID(token_id))
        current_version = self.token_repo.get_user_version(user_id=ID(user_id))

        logger.info("TokenToolsService finished successfully")

        return {
            "is_token_blocked": is_token_blocked,
            "current_version": current_version,
        }
