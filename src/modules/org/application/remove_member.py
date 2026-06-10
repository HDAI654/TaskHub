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

logger = logging.getLogger(__name__)


class RemoveMemberService:
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
        self, access_token: str, org_id: str, user_to_remove_id: str
    ) -> None:
        logger.info(
            "Removing member from organization: org_id=%s, user_id=%s",
            org_id,
            user_to_remove_id,
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

        # Check if current user has permission (owner or admin)
        current_role = await self.uow.orgs.get_user_role(org_id_vo, current_user.id)
        if current_role is None or current_role.value not in {"owner", "admin"}:
            logger.debug(
                "User lacks permission to remove members: user_id=%s, org_id=%s",
                current_user.id.value,
                org_id,
            )
            raise PermissionDenied("Only owner or admin can remove members")

        # Remove member
        try:
            await self.uow.orgs.remove_member(org_id_vo, ID(user_to_remove_id))
            await self.uow.commit()
        except InvalidIDError as e:
            logger.debug("Member has invalid ID: %s", str(e))
            raise MemberNotFoundError()
        except MemberNotFoundError as e:
            logger.debug("Member not found: %s", str(e))
            raise

        logger.info(
            "Member removed successfully: org_id=%s, user_id=%s",
            org_id,
            user_to_remove_id,
        )
