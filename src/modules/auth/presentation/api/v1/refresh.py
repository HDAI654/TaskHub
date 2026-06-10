import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from src.modules.auth.application.token_rotation import TokenRotationService
from src.modules.auth.presentation.api.v1.dependencies import get_token_rotation_service
from src.modules.core.exceptions import (
    UserNotFoundError,
    InvalidToken,
    DatabaseError,
    CacheError,
)
from src.modules.core.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()

RATE_LIMIT_MAX_REQUESTS = 20


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None


@router.post("/refresh", response_model=RefreshTokenResponse)
@rate_limit(max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="refresh")
async def refresh_token(
    request: Request,
    refresh_data: RefreshTokenRequest,
    service: TokenRotationService = Depends(get_token_rotation_service),
):
    logger.info("RefreshToken endpoint started")
    try:
        access_token, refresh_token = await service.execute(
            refresh_token=refresh_data.refresh_token,
        )
    except (InvalidToken, UserNotFoundError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except DatabaseError:
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )
    except CacheError:
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )
    except Exception as e:
        logger.exception("Unexpected error during refresh-token endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("RefreshToken finished successfully")
    return RefreshTokenResponse(access_token=access_token, refresh_token=refresh_token)
