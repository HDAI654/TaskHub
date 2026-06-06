import pytest
from datetime import datetime, timedelta, timezone
from src.modules.core.conf import Config
import jwt
from src.modules.auth.exceptions import TokenCreationError
from src.modules.auth.infrastructure.security.jwt_encoder import JWTEncoder
from src.modules.auth.domain.value_objects.id import ID


class TestJWTEncoder:
    @pytest.fixture
    def encoder(self):
        return JWTEncoder()

    def test_create_access_token_payload(self, encoder: JWTEncoder):
        user_id = ID()
        token = encoder.create_access_token(user_id=user_id)
        payload = jwt.decode(
            token,
            Config.JWT_PUBLIC_KEY,
            algorithms=[Config.JWT_ALGORITHM],
        )

        assert payload["sub"] == user_id.value
        assert isinstance(payload["jti"], str)
        assert payload["type"] == "access"
        assert payload["exp"] > datetime.now(timezone.utc).timestamp()

    def test_create_refresh_token_payload(self, encoder: JWTEncoder):
        user_id = ID()
        token = encoder.create_refresh_token(
            user_id=user_id,
        )
        payload = jwt.decode(
            token,
            Config.JWT_PUBLIC_KEY,
            algorithms=[Config.JWT_ALGORITHM],
        )

        assert payload["sub"] == user_id.value
        assert isinstance(payload["jti"], str)
        assert payload["type"] == "refresh"
        assert payload["exp"] > datetime.now(timezone.utc).timestamp()

    def test_should_rotate_refresh_token_true(self, encoder):
        exp = datetime.now(timezone.utc) + timedelta(
            minutes=Config.ROTATE_THRESHOLD_MINUTES - 10
        )
        assert encoder.should_rotate_refresh_token(exp.timestamp()) is True

    def test_should_rotate_refresh_token_false(self, encoder):
        exp = datetime.now(timezone.utc) + timedelta(
            minutes=Config.ROTATE_THRESHOLD_MINUTES + 3
        )
        assert encoder.should_rotate_refresh_token(exp.timestamp()) is False
