import logging
from src.modules.card.domain.ports.unit_of_work_interface import IUnitOfWork
from src.modules.auth.domain.ports.token_repo_interface import ITokenRepository
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.card.domain.value_objects.id import ID
from src.modules.core.exceptions import (
    InvalidToken,
    InvalidIDError,
    CardNotFoundError,
    PermissionDenied,
)
from src.modules.card.domain.entities.card import CardEntity

logger = logging.getLogger(__name__)


class GetCardByIdService:
    def __init__(
        self,
        uow: IUnitOfWork,
        token_repo: ITokenRepository,
        jwt_decoder: JWTDecoder,
    ):
        self.uow = uow
        self.token_repo = token_repo
        self.jwt_decoder = jwt_decoder

    async def execute(self, access_token: str, card_id: str) -> CardEntity:
        logger.info("Getting card by id: card_id=%s", card_id)

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

        # Check if user is a member of the organization (any role)
        org_id = await self.uow.columns.get_org_id(card.column_id)
        role = await self.uow.orgs.get_user_role(org_id, user_id)
        if role is None:
            logger.debug(
                "User is not a member of the organization: user_id=%s, org_id=%s",
                user_id.value,
                org_id.value,
            )
            raise PermissionDenied("You do not have access to this card")

        logger.info("Card retrieved: card_id=%s", card_id)
        return card
