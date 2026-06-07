import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.modules.auth.application.logout import LogoutService
from src.modules.auth.presentation.api.v1.dependencies import get_logout_service
from src.modules.auth.exceptions import (
    UserNotFoundError,
    InvalidToken,
    DatabaseError,
    CacheError,
)
from src.modules.core.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()


class LogoutRequest(BaseModel):
    access_token: str
    refresh_token: str


class LogoutResponse(BaseModel):
    message: str


@router.post("/logout", response_model=LogoutResponse)
@rate_limit(max_requests=30, window="min", key_prefix="logout")
async def logout(
    request: LogoutRequest,
    service: LogoutService = Depends(get_logout_service),
):
    logger.info("Logout endpoint started")
    try:
        await service.execute(
            access_token=request.access_token,
            refresh_token=request.refresh_token,
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
        logger.exception("Unexpected error during logout endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("Logout finished successfully")
    return LogoutResponse(message="Logged out successfully")
