from datetime import datetime, timedelta, timezone
import jwt
from src.modules.core.exceptions import TokenCreationError
from src.modules.auth.domain.value_objects.id import ID
from src.modules.core.conf import Config
import logging

logger = logging.getLogger(__name__)


class JWTEncoder:

    def __init__(self, private_key: str = None):
        self.private_key = private_key or Config.JWT_PRIVATE_KEY
        self.algorithm = Config.JWT_ALGORITHM

    def create_token(self, token_type: str, user_id: ID, version: int = 0):
        logger.info("Creating %s-token", token_type)
        try:
            if token_type == "refresh":
                exp = datetime.now(timezone.utc) + timedelta(
                    minutes=Config.REFRESH_TOKEN_EXPIRE_MINUTES
                )
            else:
                exp = datetime.now(timezone.utc) + timedelta(
                    minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES
                )
            payload = {
                "sub": user_id.value,
                "jti": ID().value,
                "ver": version,
                "exp": exp.timestamp(),
                "type": token_type,
                "iat": datetime.now(timezone.utc).timestamp(),
            }
            logger.info("%s-token created successfully", token_type)
            return jwt.encode(payload, self.private_key, algorithm=self.algorithm)
        except Exception as e:
            logger.exception(
                "Unexpected error occurred during %s-token generation", token_type
            )
            raise TokenCreationError(
                f"Unexpected error occurred during {token_type}-token generation:\n{str(e)}"
            ) from e

    def create_access_token(self, user_id: ID, version: int = 0) -> str:
        """Create access token signed with private key"""
        return self.create_token(token_type="access", user_id=user_id, version=version)

    def create_refresh_token(self, user_id: ID, version: int = 0) -> str:
        """Create refresh token signed with private key"""
        return self.create_token(token_type="refresh", user_id=user_id, version=version)

    def should_rotate_refresh_token(self, token_expire_time: float) -> bool:
        logger.info("Checking refresh-token rotation")
        try:
            rotate_threshold = timedelta(minutes=Config.ROTATE_THRESHOLD_MINUTES)

            exp = datetime.fromtimestamp(token_expire_time, timezone.utc)
            now = datetime.now(timezone.utc)
            need = exp - now <= rotate_threshold
            logger.info("Refresh token rotation checked: rotation need=%s", need)
            return need
        except Exception as e:
            logger.exception(
                "Unexpected error occurred during check refresh-token rotation"
            )
            raise TokenCreationError(
                f"Unexpected error occurred during check refresh-token rotation:\n{str(e)}"
            ) from e
