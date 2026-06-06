import jwt
from jwt import ExpiredSignatureError, InvalidTokenError, DecodeError
from src.modules.core.exceptions import InvalidToken
from src.modules.core.conf import Config


class JWTDecoder:
    def __init__(self, public_key: str = None):
        self.public_key = public_key or Config.JWT_PUBLIC_KEY
        self.algorithm = Config.JWT_ALGORITHM

    def decode_token(self, token: str) -> dict:
        """
        Decode and verify JWT token using public key
        """
        try:
            return jwt.decode(token, self.public_key, algorithms=[self.algorithm])
        except ExpiredSignatureError:
            raise InvalidToken("Token has expired")
        except (InvalidTokenError, DecodeError):
            raise InvalidToken("Token is malformed or signature is invalid")

    def decode_and_validate(self, token: str, expected_type: str = None) -> dict:
        """Decode and validate claims"""
        payload = self.decode_token(token)

        # Check claims
        required_claims = ["sub", "jti", "ver", "exp", "type", "iat"]
        for claim in required_claims:
            if claim not in payload:
                raise InvalidToken(f"Missing required claim: {claim}")

        # Validate types
        if not isinstance(payload["sub"], str):
            raise InvalidToken(f"Token has invalid 'sub' claim: must be string, got {type(payload["sub"]).__name__}")
        
        if not isinstance(payload["jti"], str):
            raise InvalidToken(f"Token has invalid 'jti' claim: must be string, got {type(payload["jti"]).__name__}")
        
        if not isinstance(payload["ver"], int):
            raise InvalidToken(f"Token has invalid 'ver' claim: must be integer, got {type(payload["ver"]).__name__}")
        
        if not isinstance(payload["exp"], (int, float)):
            raise InvalidToken(f"Token has invalid 'exp' claim: must be numeric, got {type(payload["exp"]).__name__}")
        
        if not isinstance(payload["type"], str):
            raise InvalidToken(f"Token has invalid 'type' claim: must be string, got {type(payload["type"]).__name__}")
        
        if not isinstance(payload["iat"], (int, float)):
            raise InvalidToken(f"Token has invalid 'iat' claim: must be numeric, got {type(payload["iat"]).__name__}")

        # Check token type
        if expected_type and payload["type"] != expected_type:
            raise InvalidToken(f"Invalid token type: expected {expected_type}")

        return payload
