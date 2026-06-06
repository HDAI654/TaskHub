import pytest
from datetime import datetime, timedelta, timezone
from src.modules.core.conf import Config
import jwt
from src.modules.core.exceptions import InvalidToken
from src.modules.core.jwt_decoder import JWTDecoder
from src.modules.auth.domain.value_objects.id import ID


class TestJWTDecoder:
    @pytest.fixture
    def decoder(self):
        return JWTDecoder()

    def test_decode_token_returns_payload(self, decoder):
        user_id = ID()
        exp = datetime.now(timezone.utc) + timedelta(
            minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "sub": user_id.value,
            "exp": exp.timestamp(),
            "type": "access",
            "iat": datetime.now(timezone.utc).timestamp(),
        }
        token = jwt.encode(
            payload, Config.JWT_PRIVATE_KEY, algorithm=Config.JWT_ALGORITHM
        )
        decoded_payload = decoder.decode_token(token)

        assert payload == decoded_payload

    def test_decode_token_invalid_token(self, decoder):
        with pytest.raises(InvalidToken):
            decoder.decode_token("this.is.not.a.valid.jwt")

    def test_decode_token_expired_token(self, decoder):
        user_id = ID()
        exp = datetime.now(timezone.utc) - timedelta(minutes=1)
        payload = {
            "sub": user_id.value,
            "exp": exp.timestamp(),
            "type": "access",
            "iat": datetime.now(timezone.utc).timestamp(),
        }
        token = jwt.encode(
            payload, Config.JWT_PRIVATE_KEY, algorithm=Config.JWT_ALGORITHM
        )

        with pytest.raises(InvalidToken):
            decoder.decode_token(token)

    def test_decode_token_invalid_signature(self, decoder):
        user_id = ID()
        exp = datetime.now(timezone.utc) - timedelta(minutes=1)
        payload = {
            "sub": user_id.value,
            "exp": exp.timestamp(),
            "type": "access",
            "iat": datetime.now(timezone.utc).timestamp(),
        }

        valid_token = jwt.encode(
            payload, Config.JWT_PRIVATE_KEY, algorithm=Config.JWT_ALGORITHM
        )

        parts = valid_token.split(".")
        tampered_token = f"{parts[0]}.{parts[1]}.tampered_signature"

        with pytest.raises(InvalidToken):
            decoder.decode_token(tampered_token)

    def test_decode_and_validate_success(self, decoder):
        user_id = ID()
        session_id = ID()
        exp = datetime.now(timezone.utc) + timedelta(
            minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "sid": session_id.value,
            "sub": user_id.value,
            "exp": exp.timestamp(),
            "type": "access",
            "iat": datetime.now(timezone.utc).timestamp(),
        }
        token = jwt.encode(
            payload, Config.JWT_PRIVATE_KEY, algorithm=Config.JWT_ALGORITHM
        )

        result = decoder.decode_and_validate(token)

        assert result["sid"] == session_id.value
        assert result["sub"] == user_id.value
        assert result["type"] == "access"
        assert isinstance(result["exp"], (int, float))
        assert isinstance(result["iat"], (int, float))

    def test_decode_and_validate_missing_required_claim(self, decoder):
        user_id = ID()
        exp = datetime.now(timezone.utc) + timedelta(
            minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "sub": user_id.value,
            "exp": exp.timestamp(),
            "type": "access",
            "iat": datetime.now(timezone.utc).timestamp(),
        }
        token = jwt.encode(
            payload, Config.JWT_PRIVATE_KEY, algorithm=Config.JWT_ALGORITHM
        )

        with pytest.raises(InvalidToken):
            decoder.decode_and_validate(token)

    def test_decode_and_validate_exp_wrong_type(self, decoder):
        user_id = ID()
        session_id = ID()
        payload = {
            "sid": session_id.value,
            "sub": user_id.value,
            "exp": "not-a-number",
            "type": "access",
            "iat": datetime.now(timezone.utc).timestamp(),
        }
        token = jwt.encode(
            payload, Config.JWT_PRIVATE_KEY, algorithm=Config.JWT_ALGORITHM
        )

        with pytest.raises(InvalidToken):
            decoder.decode_and_validate(token)

    def test_decode_and_validate_type_wrong_type(self, decoder):
        user_id = ID()
        session_id = ID()
        exp = datetime.now(timezone.utc) + timedelta(
            minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "sid": session_id.value,
            "sub": user_id.value,
            "exp": exp.timestamp(),
            "type": 12345,
            "iat": datetime.now(timezone.utc).timestamp(),
        }
        token = jwt.encode(
            payload, Config.JWT_PRIVATE_KEY, algorithm=Config.JWT_ALGORITHM
        )

        with pytest.raises(InvalidToken):
            decoder.decode_and_validate(token)

    def test_decode_and_validate_with_expected_type_matches(self, decoder):
        user_id = ID()
        session_id = ID()
        exp = datetime.now(timezone.utc) + timedelta(
            minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "sid": session_id.value,
            "sub": user_id.value,
            "exp": exp.timestamp(),
            "type": "refresh",
            "iat": datetime.now(timezone.utc).timestamp(),
        }
        token = jwt.encode(
            payload, Config.JWT_PRIVATE_KEY, algorithm=Config.JWT_ALGORITHM
        )

        result = decoder.decode_and_validate(token, expected_type="refresh")

        assert result["type"] == "refresh"

    def test_decode_and_validate_with_expected_type_mismatch(self, decoder):
        user_id = ID()
        session_id = ID()
        exp = datetime.now(timezone.utc) + timedelta(
            minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "sid": session_id.value,
            "sub": user_id.value,
            "exp": exp.timestamp(),
            "type": "access",
            "iat": datetime.now(timezone.utc).timestamp(),
        }
        token = jwt.encode(
            payload, Config.JWT_PRIVATE_KEY, algorithm=Config.JWT_ALGORITHM
        )

        with pytest.raises(InvalidToken):
            decoder.decode_and_validate(token, expected_type="refresh")
