import logging
from fastapi import APIRouter, Depends, HTTPException
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

logger = logging.getLogger(__name__)

router = APIRouter()


class ResetPasswordRequest(BaseModel):
    access_token: str
    token: str
    new_password: str


class ResetPasswordResponse(BaseModel):
    access_token: str
    refresh_token: str


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    request: ResetPasswordRequest,
    service: ResetPassService = Depends(get_reset_password_service),
):
    logger.info("ResetPassword endpoint started")
    try:
        access_token, refresh_token = await service.execute(
            access_token=request.access_token,
            token=request.token,
            new_password=request.new_password,
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
