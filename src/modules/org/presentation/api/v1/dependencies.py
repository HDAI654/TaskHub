from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from src.modules.core.database import get_async_session
from src.modules.core.redis_client import get_redis_client
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.auth.infrastructure.cache.redis_token_repo import RedisTokenRepository
from src.modules.org.infrastructure.persistence.sqlal_unit_of_work import (
    SQLAL_UnitOfWork,
)
from src.modules.org.application.create_org import CreateOrgService
from src.modules.org.application.get_org import GetOrgService
from src.modules.org.application.update_org import UpdateOrgService
from src.modules.org.application.delete_org import DeleteOrgService
from src.modules.org.application.add_member import AddMemberService
from src.modules.org.application.remove_member import RemoveMemberService
from src.modules.org.application.change_user_role import ChangeUserRoleService
from src.modules.org.application.get_user_orgs import GetUserOrgsService
from src.modules.org.application.get_org_members import GetOrgMembersService


async def get_uow(db: AsyncSession = Depends(get_async_session)) -> SQLAL_UnitOfWork:
    return SQLAL_UnitOfWork(db)


async def get_token_repo(
    redis: Redis = Depends(get_redis_client),
) -> RedisTokenRepository:
    return RedisTokenRepository(redis)


async def get_jwt_decoder() -> JWTDecoder:
    return JWTDecoder()


async def get_create_org_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> CreateOrgService:
    return CreateOrgService(uow, token_repo, jwt_decoder)


async def get_get_org_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> GetOrgService:
    return GetOrgService(uow, token_repo, jwt_decoder)


async def get_update_org_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> UpdateOrgService:
    return UpdateOrgService(uow, token_repo, jwt_decoder)


async def get_delete_org_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> DeleteOrgService:
    return DeleteOrgService(uow, token_repo, jwt_decoder)


async def get_add_member_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> AddMemberService:
    return AddMemberService(uow, token_repo, jwt_decoder)


async def get_remove_member_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> RemoveMemberService:
    return RemoveMemberService(uow, token_repo, jwt_decoder)


async def get_change_user_role_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> ChangeUserRoleService:
    return ChangeUserRoleService(uow, token_repo, jwt_decoder)


async def get_get_user_orgs_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> GetUserOrgsService:
    return GetUserOrgsService(uow, token_repo, jwt_decoder)


async def get_get_org_members_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> GetOrgMembersService:
    return GetOrgMembersService(uow, token_repo, jwt_decoder)
