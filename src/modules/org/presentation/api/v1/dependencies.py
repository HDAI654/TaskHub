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

from src.modules.org.application.create_project import CreateProjectService
from src.modules.org.application.update_project import UpdateProjectService
from src.modules.org.application.delete_project import DeleteProjectService
from src.modules.org.application.get_project import GetProjectService
from src.modules.org.application.get_org_projects import GetOrgProjectsService

from src.modules.org.application.create_board import CreateBoardService
from src.modules.org.application.update_board import UpdateBoardService
from src.modules.org.application.delete_board import DeleteBoardService
from src.modules.org.application.get_board import GetBoardService
from src.modules.org.application.get_project_boards import GetProjectBoardsService

from src.modules.org.application.create_column import CreateColumnService
from src.modules.org.application.update_column import UpdateColumnService
from src.modules.org.application.delete_column import DeleteColumnService
from src.modules.org.application.get_column import GetColumnService
from src.modules.org.application.get_board_columns import GetBoardColumnsService


async def get_uow(db: AsyncSession = Depends(get_async_session)) -> SQLAL_UnitOfWork:
    return SQLAL_UnitOfWork(db)


async def get_token_repo(
    redis: Redis = Depends(get_redis_client),
) -> RedisTokenRepository:
    return RedisTokenRepository(redis)


async def get_jwt_decoder() -> JWTDecoder:
    return JWTDecoder()


# ===== org =====
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


# ===== prj =====
async def get_create_project_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> CreateProjectService:
    return CreateProjectService(uow, token_repo, jwt_decoder)


async def get_update_project_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> UpdateProjectService:
    return UpdateProjectService(uow, token_repo, jwt_decoder)


async def get_delete_project_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> DeleteProjectService:
    return DeleteProjectService(uow, token_repo, jwt_decoder)


async def get_get_project_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> GetProjectService:
    return GetProjectService(uow, token_repo, jwt_decoder)


async def get_get_org_projects_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> GetOrgProjectsService:
    return GetOrgProjectsService(uow, token_repo, jwt_decoder)


# ===== board =====
async def get_create_board_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> CreateBoardService:
    return CreateBoardService(uow, token_repo, jwt_decoder)


async def get_update_board_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> UpdateBoardService:
    return UpdateBoardService(uow, token_repo, jwt_decoder)


async def get_delete_board_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> DeleteBoardService:
    return DeleteBoardService(uow, token_repo, jwt_decoder)


async def get_get_board_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> GetBoardService:
    return GetBoardService(uow, token_repo, jwt_decoder)


async def get_get_project_boards_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> GetProjectBoardsService:
    return GetProjectBoardsService(uow, token_repo, jwt_decoder)


# ===== column =====
async def get_create_column_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> CreateColumnService:
    return CreateColumnService(uow, token_repo, jwt_decoder)


async def get_update_column_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> UpdateColumnService:
    return UpdateColumnService(uow, token_repo, jwt_decoder)


async def get_delete_column_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> DeleteColumnService:
    return DeleteColumnService(uow, token_repo, jwt_decoder)


async def get_get_column_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> GetColumnService:
    return GetColumnService(uow, token_repo, jwt_decoder)


async def get_get_board_columns_service(
    uow: SQLAL_UnitOfWork = Depends(get_uow),
    token_repo: RedisTokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> GetBoardColumnsService:
    return GetBoardColumnsService(uow, token_repo, jwt_decoder)
