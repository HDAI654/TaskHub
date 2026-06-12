import logging
from src.modules.card.domain.ports.unit_of_work_interface import IUnitOfWork
from src.modules.auth.domain.ports.token_repo_interface import ITokenRepository
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.card.domain.value_objects.id import ID
from src.modules.card.domain.value_objects.title import Title
from src.modules.card.domain.value_objects.description import Description
from src.modules.card.domain.value_objects.priority import Priority
from src.modules.card.domain.value_objects.datetime import DateTime
from src.modules.core.exceptions import (
    InvalidToken,
    InvalidIDError,
    CardNotFoundError,
    ColumnNotFoundError,
    PermissionDenied,
)

logger = logging.getLogger(__name__)


class EditCardService:
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
        card_id: str,
        new_column_id: str | None = None,
        new_title: str | None = None,
        new_description: str | None = None,
        new_priority: str | None = None,
        new_due_date: str | None = None,
    ) -> None:
        logger.info("Editing card: card_id=%s", card_id)

        # Decode and validate access token
        payload = self.jwt_decoder.decode_and_validate(access_token, "access")

        # Check token version and block list
        try:
            user_id = ID(payload["sub"])
            current_version = await self.token_repo.get_user_version(user_id)
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

        # Get organization ID from card's column
        org_id = await self.uow.columns.get_org_id(card.column_id)

        # Check user role (admin/owner required)
        role = await self.uow.orgs.get_user_role(org_id, user_id)
        if role is None or role.value not in {"owner", "admin"}:
            logger.debug(
                "User lacks permission to edit card: user_id=%s, org_id=%s, role=%s",
                user_id.value,
                org_id.value,
                role.value if role else None,
            )
            raise PermissionDenied("Only owner or admin can edit cards")

        # Convert optional parameters to value objects
        column_id_vo = ID(new_column_id) if new_column_id is not None else None
        title_vo = Title(new_title) if new_title is not None else None
        description_vo = (
            Description(new_description) if new_description is not None else None
        )
        priority_vo = Priority(new_priority) if new_priority is not None else None
        due_date_vo = DateTime(new_due_date) if new_due_date is not None else None

        # If column_id is provided, ensure column exists
        if column_id_vo:
            try:
                await self.uow.columns.get_by_id(column_id_vo)
            except ColumnNotFoundError:
                logger.warning("Target column not found: column_id=%s", new_column_id)
                raise

        await self.uow.cards.update(
            card_id=card_id_vo,
            new_column_id=column_id_vo,
            new_title=title_vo,
            new_description=description_vo,
            new_priority=priority_vo,
            new_due_date=due_date_vo,
        )
        await self.uow.commit()

        logger.info("Card updated successfully: card_id=%s", card_id)
