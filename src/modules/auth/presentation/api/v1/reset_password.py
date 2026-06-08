import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from src.modules.auth.application.reset_password import ResetPassService
from src.modules.auth.presentation.api.v1.dependencies import get_reset_password_service
from src.modules.auth.exceptions import (
    UserNotFoundError,
    InvalidToken,
    PermissionDenied,
    WeakPasswordError,
    DatabaseError,
    CacheError,
)
from src.modules.core.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()

RATE_LIMIT_MAX_REQUESTS = 5

class ResetPasswordRequest(BaseModel):
    access_token: str
    token: str
    new_password: str


class ResetPasswordResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None


@router.post("/reset-password", response_model=ResetPasswordResponse)
@rate_limit(max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="reset_pass")
async def reset_password(
    request: Request,
    res_pass_data: ResetPasswordRequest,
    service: ResetPassService = Depends(get_reset_password_service),
):
    logger.info("ResetPassword endpoint started")
    try:
        access_token, refresh_token = await service.execute(
            access_token=res_pass_data.access_token,
            token=res_pass_data.token,
            new_password=res_pass_data.new_password,
        )
    except (InvalidToken, UserNotFoundError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except PermissionDenied:
        raise HTTPException(
            status_code=404, detail="This reset-password-token is expired"
        )
    except WeakPasswordError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError:
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )
    except CacheError:
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )
    except Exception as e:
        logger.exception("Unexpected error during reset-pass endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("ResetPassword finished successfully")
    return ResetPasswordResponse(access_token=access_token, refresh_token=refresh_token)
