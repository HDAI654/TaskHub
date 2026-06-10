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
    PermissionDenied,
    InvalidIDError,
)

logger = logging.getLogger(__name__)


class DeleteProjectService:
    def __init__(
        self,
        uow: IUnitOfWork,
        token_repo: ITokenRepository,
        jwt_decoder: JWTDecoder,
    ):
        self.uow = uow
        self.token_repo = token_repo
        self.jwt_decoder = jwt_decoder

    async def execute(self, access_token: str, project_id: str) -> None:
        logger.info("Deleting project: project_id=%s", project_id)

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

        # Get project
        try:
            project_id_vo = ID(project_id)
        except InvalidIDError:
            raise ProjectNotFoundError(f"Project not found: project_id={project_id}")
        try:
            project = await self.uow.projects.get_by_id(project_id_vo)
        except ProjectNotFoundError:
            logger.debug("Project not found: project_id=%s", project_id)
            raise

        # Check organization exists
        org_id_vo = project.org_id
        if not await self.uow.orgs.exists_by_id(org_id_vo):
            raise OrgNotFoundError(f"Organization with id {org_id_vo.value} not found")

        # Check user is owner or admin of this organization
        user_role = await self.uow.orgs.get_user_role(org_id_vo, user.id)
        if user_role is None or user_role.value not in {"owner", "admin"}:
            logger.debug(
                "User not owner or admin of organization: user_id=%s, org_id=%s",
                user.id.value,
                org_id_vo.value,
            )
            raise PermissionDenied("You don't have access to this project")

        # Delete project
        await self.uow.projects.delete(project_id_vo)
        await self.uow.commit()

        logger.info("Project deleted successfully: project_id=%s", project_id)
