import logging
from src.modules.card.domain.ports.unit_of_work_interface import IUnitOfWork
from src.modules.auth.domain.ports.token_repo_interface import ITokenRepository
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.card.domain.value_objects.id import ID
from src.modules.card.domain.value_objects.title import Title
from src.modules.card.domain.value_objects.is_checked import IsChecked
from src.modules.core.exceptions import (
    InvalidToken,
    UserNotFoundError,
    InvalidIDError,
    PermissionDenied,
    CheckListNotFoundError,
)

logger = logging.getLogger(__name__)


class UpdateChecklistService:
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
        self,
        access_token: str,
        checklist_id: str,
        new_title: str | None = None,
        new_is_checked: bool | None = None,
    ) -> None:
        logger.info("Updating checklist: checklist_id=%s", checklist_id)

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

        # Get checklist to verify ownership via card
        try:
            checklist_id_vo = ID(checklist_id)
        except InvalidIDError:
            raise CheckListNotFoundError(
                f"CheckList not found: checklist_id={checklist_id}"
            )
        checklist = await self.uow.cards.get_checklist_by_id(checklist_id_vo)

        # Get card and organization
        card = await self.uow.cards.get_by_id(checklist.card_id)
        org_id = await self.uow.columns.get_org_id(card.column_id)

        # Check role (admin/owner/member allowed)
        role = await self.uow.orgs.get_user_role(org_id, current_user_id)
        if role is None or role.value not in {"owner", "admin", "member"}:
            logger.debug(
                "User lacks permission to update checklist: user_id=%s, org_id=%s, role=%s",
                current_user_id.value,
                org_id.value,
                role.value if role else None,
            )
            raise PermissionDenied("Only owner, admin, or member can update checklists")

        title_vo = Title(new_title) if new_title is not None else None
        is_checked_vo = (
            IsChecked(new_is_checked) if new_is_checked is not None else None
        )

        await self.uow.cards.update_checklist(
            checklist_id=checklist_id_vo,
            new_title=title_vo,
            new_is_checked=is_checked_vo,
        )
        await self.uow.commit()

        logger.info("Checklist updated: checklist_id=%s", checklist_id)
