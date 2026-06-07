from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from fastapi import Depends
from src.modules.core.database import get_async_session
from src.modules.core.redis_client import get_redis_client
from src.modules.auth.domain.ports.user_repo_interface import IUserRepository
from src.modules.auth.domain.ports.session_repo_interface import ISessionRepository
from src.modules.auth.infrastructure.persistence.sqlal_user_repo import (
    SQLAL_UserRepository,
)
from src.modules.auth.infrastructure.cache.redis_session_repo import (
    RedisSessionRepository,
)
from src.modules.auth.infrastructure.security.jwt_encoder import JWTEncoder
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.auth.infrastructure.security.password_hasher import PasswordHasher
from src.modules.auth.domain.ports.oauth_provider_interface import IOAuthProvider
from src.modules.auth.infrastructure.oauth.github_oauth_provider import (
    GitHubOAuthProvider,
)
from functools import lru_cache


def get_user_repo(db: AsyncSession = Depends(get_async_session)) -> IUserRepository:
    return SQLAL_UserRepository(db)


def get_session_repo(client: Redis = Depends(get_redis_client)) -> ISessionRepository:
    return RedisSessionRepository(client)


@lru_cache(maxsize=1)
def get_jwt_encoder() -> JWTEncoder:
    return JWTEncoder()


@lru_cache(maxsize=1)
def get_jwt_decoder() -> JWTDecoder:
    return JWTDecoder()


@lru_cache(maxsize=1)
def get_password_hasher() -> PasswordHasher:
    return PasswordHasher()


def get_oauth_provider() -> IOAuthProvider:
    return GitHubOAuthProvider()
