import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from src.modules.auth.application.token_rotation import TokenRotationService
from src.modules.auth.presentation.api.v1.dependencies import get_token_rotation_service
from src.modules.auth.exceptions import (
    UserNotFoundError,
    InvalidToken,
    DatabaseError,
    CacheError
)

logger = logging.getLogger(__name__)

router = APIRouter()


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    service: TokenRotationService = Depends(get_token_rotation_service),
):
    logger.info("RefreshToken endpoint started")
    try:
        access_token, refresh_token = await service.execute(
            refresh_token=request.refresh_token,
        )
    except (InvalidToken, UserNotFoundError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except DatabaseError:
        raise HTTPException(status_code=500, detail="Something went wrong. Please try again later.")
    except CacheError:
        raise HTTPException(status_code=500, detail="Something went wrong. Please try again later.")
    except Exception as e:
        logger.exception("Unexpected error during refresh-token endpoint")
        raise HTTPException(status_code=500, detail="Something went wrong. Please try again later.")
    
    logger.info("RefreshToken finished successfully")
    return RefreshTokenResponse(access_token=access_token, refresh_token=refresh_token)