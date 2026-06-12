from fastapi import Depends
from redis.asyncio import Redis
from src.modules.card.domain.ports.unit_of_work_interface import IUnitOfWork
from src.modules.auth.domain.ports.token_repo_interface import ITokenRepository
from src.modules.card.infrastructure.persistence.sqlal_unit_of_work import (
    SQLAL_UnitOfWork,
)
from src.modules.auth.infrastructure.cache.redis_token_repo import RedisTokenRepository
from src.modules.core.jwt_decoder import JWTDecoder
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.core.database import get_async_session
from src.modules.core.redis_client import get_redis_client
from src.modules.card.application.create_card import CreateCardService
from src.modules.card.application.edit_card import EditCardService
from src.modules.card.application.delete_card import DeleteCardService
from src.modules.card.application.get_card_by_id import GetCardByIdService
from src.modules.card.application.get_column_cards import GetColumnCardsService
from src.modules.card.application.add_assignee import AddAssigneeService
from src.modules.card.application.remove_assignee import RemoveAssigneeService
from src.modules.card.application.get_card_assignees import GetCardAssigneesService
from src.modules.card.application.add_label_to_card import AddLabelToCardService
from src.modules.card.application.remove_label_from_card import (
    RemoveLabelFromCardService,
)
from src.modules.card.application.get_card_labels import GetCardLabelsService
from src.modules.card.application.add_checklist import AddChecklistService
from src.modules.card.application.update_checklist import UpdateChecklistService
from src.modules.card.application.delete_checklist import DeleteChecklistService
from src.modules.card.application.get_checklist_by_id import GetChecklistByIdService
from src.modules.card.application.get_card_checklists import GetCardChecklistsService


async def get_uow(db: AsyncSession = Depends(get_async_session)) -> IUnitOfWork:
    return SQLAL_UnitOfWork(db)


async def get_token_repo(
    redis: Redis = Depends(get_redis_client),
) -> ITokenRepository:
    return RedisTokenRepository(redis)


async def get_jwt_decoder():
    return JWTDecoder()


async def get_create_card_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
):
    return CreateCardService(uow, token_repo, jwt_decoder)


async def get_edit_card_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
):
    return EditCardService(uow, token_repo, jwt_decoder)


async def get_delete_card_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
):
    return DeleteCardService(uow, token_repo, jwt_decoder)


async def get_get_card_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
):
    return GetCardByIdService(uow, token_repo, jwt_decoder)


async def get_get_column_cards_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
):
    return GetColumnCardsService(uow, token_repo, jwt_decoder)


async def get_add_assignee_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
):
    return AddAssigneeService(uow, token_repo, jwt_decoder)


async def get_remove_assignee_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
):
    return RemoveAssigneeService(uow, token_repo, jwt_decoder)


async def get_get_assignees_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
):
    return GetCardAssigneesService(uow, token_repo, jwt_decoder)


async def get_add_label_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
):
    return AddLabelToCardService(uow, token_repo, jwt_decoder)


async def get_remove_label_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
):
    return RemoveLabelFromCardService(uow, token_repo, jwt_decoder)


async def get_get_labels_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
):
    return GetCardLabelsService(uow, token_repo, jwt_decoder)


async def get_add_checklist_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
):
    return AddChecklistService(uow, token_repo, jwt_decoder)


async def get_update_checklist_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
):
    return UpdateChecklistService(uow, token_repo, jwt_decoder)


async def get_delete_checklist_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
):
    return DeleteChecklistService(uow, token_repo, jwt_decoder)


async def get_get_checklist_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
):
    return GetChecklistByIdService(uow, token_repo, jwt_decoder)


async def get_get_card_checklists_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
):
    return GetCardChecklistsService(uow, token_repo, jwt_decoder)
