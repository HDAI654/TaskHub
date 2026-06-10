import logging
from src.modules.org.domain.ports.unit_of_work_interface import IUnitOfWork
from src.modules.auth.domain.ports.token_repo_interface import ITokenRepository
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.org.domain.value_objects.id import ID
from src.modules.core.exceptions import (
    InvalidToken,
    UserNotFoundError,
    OrgNotFoundError,
    PermissionDenied,
)
from src.modules.org.domain.value_objects.name import Name

logger = logging.getLogger(__name__)


class UpdateOrgService:
    def __init__(
        self,
        uow: IUnitOfWork,
        token_repo: ITokenRepository,
        jwt_decoder: JWTDecoder,
    ):
        self.uow = uow
        self.token_repo = token_repo
        self.jwt_decoder = jwt_decoder

    async def execute(self, access_token: str, org_id: str, new_name: str) -> None:
        logger.info("Updating organization: org_id=%s, new_name=%s", org_id, new_name)

        # Decode and validate access token
        payload = self.jwt_decoder.decode_and_validate(access_token, "access")

        # Check user exists
        try:
            user = await self.uow.users.get_by_id(ID(payload["sub"]))
        except UserNotFoundError:
            logger.warning("User not found: user_id=%s", payload["sub"])
            raise

        # Check token version and check it is blocked
        current_version = await self.token_repo.get_user_version(user_id=user.id)
        is_token_blocked = await self.token_repo.is_token_blocked(
            token_id=ID(payload["jti"])
        )
        if payload["ver"] != current_version or is_token_blocked:
            raise InvalidToken("Access token is expired")

        # Check organization exists
        org_id_vo = ID(org_id)
        if not await self.uow.orgs.exists_by_id(org_id_vo):
            raise OrgNotFoundError(f"Organization with id {org_id} not found")

        # Check if user is owner
        role = await self.uow.orgs.get_user_role(org_id_vo, user.id)
        if role is None or role.value != "owner":
            logger.debug(
                "User is not owner of organization: user_id=%s, org_id=%s",
                user.id.value,
                org_id,
            )
            raise PermissionDenied("Only owner can edit organization")

        # Update organization name
        await self.uow.orgs.update(org_id_vo, new_name=Name(new_name))
        await self.uow.commit()

        logger.info("Organization updated successfully: org_id=%s", org_id)
