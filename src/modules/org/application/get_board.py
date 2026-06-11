import logging
from src.modules.org.domain.ports.unit_of_work_interface import IUnitOfWork
from src.modules.auth.domain.ports.token_repo_interface import ITokenRepository
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.org.domain.value_objects.id import ID
from src.modules.core.exceptions import (
    InvalidToken,
    UserNotFoundError,
    OrgNotFoundError,
    ProjectNotFoundError,
    BoardNotFoundError,
    PermissionDenied,
    InvalidIDError,
)
from src.modules.org.domain.entities.board import BoardEntity

logger = logging.getLogger(__name__)


class GetBoardService:
    def __init__(
        self,
        uow: IUnitOfWork,
        token_repo: ITokenRepository,
        jwt_decoder: JWTDecoder,
    ):
        self.uow = uow
        self.token_repo = token_repo
        self.jwt_decoder = jwt_decoder

    async def execute(self, access_token: str, board_id: str) -> BoardEntity:
        logger.info("Getting board: board_id=%s", board_id)

        # Decode and validate access token
        payload = self.jwt_decoder.decode_and_validate(access_token, "access")

        # Check user exists
        try:
            user = await self.uow.users.get_by_id(ID(payload["sub"]))
        except UserNotFoundError:
            logger.warning("User not found: user_id=%s", payload["sub"])
            raise

        # Check token version and blacklist
        current_version = await self.token_repo.get_user_version(user_id=user.id)
        is_token_blocked = await self.token_repo.is_token_blocked(
            token_id=ID(payload["jti"])
        )
        if payload["ver"] != current_version or is_token_blocked:
            raise InvalidToken("Access token is expired")

        # Get board
        try:
            board_id_vo = ID(board_id)
        except InvalidIDError:
            raise BoardNotFoundError(f"Board not found: board_id={board_id}")
        try:
            board = await self.uow.boards.get_by_id(board_id_vo)
        except BoardNotFoundError:
            logger.debug("Board not found: board_id=%s", board_id)
            raise

        # Get project from board
        try:
            project = await self.uow.projects.get_by_id(board.prj_id)
        except ProjectNotFoundError:
            raise ProjectNotFoundError(
                f"Project with id {board.prj_id.value} not found"
            )

        # Check organization exists
        org_id_vo = project.org_id
        if not await self.uow.orgs.exists_by_id(org_id_vo):
            raise OrgNotFoundError(f"Organization with id {org_id_vo.value} not found")

        # Check user is a member of the organization
        user_role = await self.uow.orgs.get_user_role(org_id_vo, user.id)
        if user_role is None:
            logger.debug(
                "User not a member of organization: user_id=%s, org_id=%s",
                user.id.value,
                org_id_vo.value,
            )
            raise PermissionDenied("You don't have access to this board")

        logger.info("Board retrieved successfully: board_id=%s", board_id)
        return board
