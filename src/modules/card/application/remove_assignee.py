import logging
from src.modules.card.domain.ports.unit_of_work_interface import IUnitOfWork
from src.modules.auth.domain.ports.token_repo_interface import ITokenRepository
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.card.domain.value_objects.id import ID
from src.modules.core.exceptions import (
    InvalidToken,
    UserNotFoundError,
    InvalidIDError,
    CardNotFoundError,
    PermissionDenied,
)

logger = logging.getLogger(__name__)


class RemoveAssigneeService:
    def __init__(
        self,
        uow: IUnitOfWork,
        token_repo: ITokenRepository,
        jwt_decoder: JWTDecoder,
    ):
        self.uow = uow
        self.token_repo = token_repo
        self.jwt_decoder = jwt_decoder

    async def execute(self, access_token: str, card_id: str, assignee_id: str) -> None:
        logger.info(
            "Removing assignee from card: card_id=%s, assignee_id=%s",
            card_id,
            assignee_id,
        )

        # Decode and validate access token
        payload = self.jwt_decoder.decode_and_validate(access_token, "access")

        # Check token version and block list
        try:
            current_user_id = ID(payload["sub"])
            current_version = await self.token_repo.get_user_version(current_user_id)
            is_token_blocked = await self.token_repo.is_token_blocked(
                token_id=ID(payload["jti"])
            )
            if payload["ver"] != current_version or is_token_blocked:
                raise InvalidToken("Access token is expired")
        except InvalidIDError:
            raise InvalidToken("Access token is invalid")

        # Get card
        try:
            card_id_vo = ID(card_id)
        except InvalidIDError:
            raise CardNotFoundError(f"Card not found: card_id={card_id}")
        card = await self.uow.cards.get_by_id(card_id_vo)

        # Get organization ID
        org_id = await self.uow.columns.get_org_id(card.column_id)

        # Check role (admin/owner required)
        role = await self.uow.orgs.get_user_role(org_id, current_user_id)
        if role is None or role.value not in {"owner", "admin"}:
            logger.debug(
                "User lacks permission to remove assignees: user_id=%s, org_id=%s, role=%s",
                current_user_id.value,
                org_id.value,
                role.value if role else None,
            )
            raise PermissionDenied("Only owner or admin can remove assignees")

        try:
            assignee_id_vo = ID(assignee_id)
        except InvalidIDError:
            raise UserNotFoundError(f"User not found: assignee_id={assignee_id}")
        await self.uow.cards.del_assignee(card_id_vo, assignee_id_vo)
        await self.uow.commit()

        logger.info(
            "Assignee removed successfully: card_id=%s, assignee_id=%s",
            card_id,
            assignee_id,
        )
