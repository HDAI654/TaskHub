import logging
from src.modules.card.domain.ports.unit_of_work_interface import IUnitOfWork
from src.modules.auth.domain.ports.token_repo_interface import ITokenRepository
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.card.domain.value_objects.id import ID
from src.modules.core.exceptions import (
    InvalidToken,
    InvalidIDError,
    ColumnNotFoundError,
    PermissionDenied,
)
from src.modules.card.domain.factories.card_factory import CardFactory
from src.modules.card.domain.entities.card import CardEntity

logger = logging.getLogger(__name__)


class CreateCardService:
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
        column_id: str,
        title: str,
        description: str,
        priority: str,
        due_date: str,
    ) -> CardEntity:
        logger.info("Creating card: column_id=%s, title=%s", column_id, title)

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

        # Check column exists
        try:
            column_id_vo = ID(column_id)
        except InvalidIDError:
            raise ColumnNotFoundError(f"Column not found: column_id={column_id}")
        try:
            await self.uow.columns.get_by_id(column_id_vo)
        except ColumnNotFoundError:
            logger.warning("Column not found: column_id=%s", column_id)
            raise

        # Get organization ID from column
        org_id = await self.uow.columns.get_org_id(column_id_vo)

        # Check user role in organization (admin/owner required)
        role = await self.uow.orgs.get_user_role(org_id, user_id)
        if role is None or role.value not in {"owner", "admin"}:
            logger.debug(
                "User lacks permission to create card: user_id=%s, org_id=%s, role=%s",
                user_id.value,
                org_id.value,
                role.value if role else None,
            )
            raise PermissionDenied("Only owner or admin can create cards")

        # Create card entity
        card = CardFactory.create(
            column_id=column_id,
            created_by_user_id=user_id.value,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
        )

        await self.uow.cards.add(card)
        await self.uow.commit()

        logger.info("Card created successfully: card_id=%s", card.id.value)
        return card
