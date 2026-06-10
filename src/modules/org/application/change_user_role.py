# src/modules/org/application/change_user_role.py
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
    MemberNotFoundError,
    InvalidIDError,
)
from src.modules.org.domain.value_objects.role import Role

logger = logging.getLogger(__name__)


class ChangeUserRoleService:
    def __init__(
        self,
        uow: IUnitOfWork,
        token_repo: ITokenRepository,
        jwt_decoder: JWTDecoder,
    ):
        self.uow = uow
        self.token_repo = token_repo
        self.jwt_decoder = jwt_decoder

    async def execute(
        self, access_token: str, org_id: str, target_user_id: str, new_role: str
    ) -> None:
        logger.info(
            "Changing user role in organization: org_id=%s, target_user_id=%s, new_role=%s",
            org_id,
            target_user_id,
            new_role,
        )

        # Decode and validate access token
        payload = self.jwt_decoder.decode_and_validate(access_token, "access")

        # Check current user exists
        try:
            current_user = await self.uow.users.get_by_id(ID(payload["sub"]))
        except UserNotFoundError:
            logger.warning("User not found: user_id=%s", payload["sub"])
            raise

        # Check token version and check it is blocked
        current_version = await self.token_repo.get_user_version(
            user_id=current_user.id
        )
        is_token_blocked = await self.token_repo.is_token_blocked(
            token_id=ID(payload["jti"])
        )
        if payload["ver"] != current_version or is_token_blocked:
            raise InvalidToken("Access token is expired")

        # Check organization exists
        try:
            org_id_vo = ID(org_id)
        except InvalidIDError:
            raise OrgNotFoundError()
        if not await self.uow.orgs.exists_by_id(org_id_vo):
            raise OrgNotFoundError(f"Organization with id {org_id} not found")

        # Check if current user is owner (only owner can change roles)
        current_role = await self.uow.orgs.get_user_role(org_id_vo, current_user.id)
        if current_role is None or current_role.value != "owner":
            logger.debug(
                "User lacks permission to change roles: user_id=%s, org_id=%s",
                current_user.id.value,
                org_id,
            )
            raise PermissionDenied("Only owner can change user roles")

        # Change role
        try:
            await self.uow.orgs.change_user_role(
                org_id_vo, ID(target_user_id), Role(new_role)
            )
            await self.uow.commit()
        except MemberNotFoundError as e:
            logger.debug("Member not found: %s", str(e))
            raise

        logger.info(
            "User role changed successfully: org_id=%s, target_user_id=%s, new_role=%s",
            org_id,
            target_user_id,
            new_role,
        )
