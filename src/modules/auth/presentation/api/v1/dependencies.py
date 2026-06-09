from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from fastapi import Depends
from functools import lru_cache

from src.modules.core.database import get_async_session
from src.modules.core.redis_client import get_redis_client
from src.modules.core.jwt_decoder import JWTDecoder

from src.modules.auth.domain.ports.user_repo_interface import IUserRepository
from src.modules.auth.domain.ports.token_repo_interface import ITokenRepository
from src.modules.auth.domain.ports.password_reset_repo_interface import (
    IPasswordResetRepository,
)
from src.modules.auth.domain.ports.unit_of_work_interface import IUnitOfWork

from src.modules.auth.infrastructure.persistence.sqlal_user_repo import (
    SQLAL_UserRepository,
)
from src.modules.auth.infrastructure.persistence.sqlal_unit_of_work import (
    SQLAL_UnitOfWork,
)
from src.modules.auth.infrastructure.cache.redis_token_repo import RedisTokenRepository
from src.modules.auth.infrastructure.cache.redis_password_reset_repo import (
    RedisPasswordResetRepository,
)
from src.modules.auth.infrastructure.security.jwt_encoder import JWTEncoder
from src.modules.auth.infrastructure.security.password_hasher import PasswordHasher

from src.modules.auth.application.signup import SignupService
from src.modules.auth.application.login import LoginService
from src.modules.auth.application.logout import LogoutService
from src.modules.auth.application.set_password import SetPassService
from src.modules.auth.application.reset_pass_token_publisher import (
    ResetPassTokenPublishService,
)
from src.modules.auth.application.reset_password import ResetPassService
from src.modules.auth.application.token_rotation import TokenRotationService
from src.modules.auth.application.del_account import DelAccountService
from src.modules.auth.application.invite import InviteService

# ========== Base Dependencies ==========


def get_user_repo(db: AsyncSession = Depends(get_async_session)) -> IUserRepository:
    return SQLAL_UserRepository(db)


def get_token_repo(client: Redis = Depends(get_redis_client)) -> ITokenRepository:
    return RedisTokenRepository(client)


def get_password_reset_repo(
    client: Redis = Depends(get_redis_client),
) -> IPasswordResetRepository:
    return RedisPasswordResetRepository(client)


async def get_uow(
    db: AsyncSession = Depends(get_async_session),
) -> IUnitOfWork:
    return SQLAL_UnitOfWork(db)


@lru_cache(maxsize=1)
def get_jwt_encoder() -> JWTEncoder:
    return JWTEncoder()


@lru_cache(maxsize=1)
def get_jwt_decoder() -> JWTDecoder:
    return JWTDecoder()


@lru_cache(maxsize=1)
def get_password_hasher() -> PasswordHasher:
    return PasswordHasher()


# ========== Service Dependencies ==========


async def get_signup_service(
    uow: IUnitOfWork = Depends(get_uow),
    jwt_encoder: JWTEncoder = Depends(get_jwt_encoder),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
) -> SignupService:
    return SignupService(uow, jwt_encoder, password_hasher)


async def get_login_service(
    uow: IUnitOfWork = Depends(get_uow),
    token_repo: ITokenRepository = Depends(get_token_repo),
    jwt_encoder: JWTEncoder = Depends(get_jwt_encoder),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
) -> LoginService:
    return LoginService(uow, token_repo, jwt_encoder, password_hasher)


async def get_logout_service(
    uow: IUnitOfWork = Depends(get_uow),
    token_repo: ITokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> LogoutService:
    return LogoutService(uow, token_repo, jwt_decoder)


async def get_set_password_service(
    uow: IUnitOfWork = Depends(get_uow),
    token_repo: ITokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
    jwt_encoder: JWTEncoder = Depends(get_jwt_encoder),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
) -> SetPassService:
    return SetPassService(uow, token_repo, jwt_decoder, jwt_encoder, password_hasher)


async def get_reset_password_publish_service(
    uow: IUnitOfWork = Depends(get_uow),
    reset_pass_repo: IPasswordResetRepository = Depends(get_password_reset_repo),
    token_repo: ITokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> ResetPassTokenPublishService:
    return ResetPassTokenPublishService(uow, reset_pass_repo, token_repo, jwt_decoder)


async def get_reset_password_service(
    uow: IUnitOfWork = Depends(get_uow),
    reset_pass_repo: IPasswordResetRepository = Depends(get_password_reset_repo),
    token_repo: ITokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
    jwt_encoder: JWTEncoder = Depends(get_jwt_encoder),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
) -> ResetPassService:
    return ResetPassService(
        uow, reset_pass_repo, token_repo, jwt_decoder, jwt_encoder, password_hasher
    )


async def get_token_rotation_service(
    uow: IUnitOfWork = Depends(get_uow),
    token_repo: ITokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
    jwt_encoder: JWTEncoder = Depends(get_jwt_encoder),
) -> TokenRotationService:
    return TokenRotationService(uow, token_repo, jwt_decoder, jwt_encoder)


async def get_del_account_service(
    uow: IUnitOfWork = Depends(get_uow),
    token_repo: ITokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> DelAccountService:
    return DelAccountService(uow, token_repo, jwt_decoder)


async def get_invite_service(
    uow: IUnitOfWork = Depends(get_uow),
    token_repo: ITokenRepository = Depends(get_token_repo),
    jwt_decoder: JWTDecoder = Depends(get_jwt_decoder),
) -> InviteService:
    return InviteService(uow, token_repo, jwt_decoder)
