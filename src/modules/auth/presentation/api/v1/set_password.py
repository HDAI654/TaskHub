import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from src.modules.auth.application.set_password import SetPassService
from src.modules.auth.presentation.api.v1.dependencies import get_set_password_service
from src.modules.auth.exceptions import (
    UserNotFoundError,
    InvalidToken,
    InvalidOldPassword,
    WeakPasswordError,
    DatabaseError,
    CacheError,
)
from src.modules.core.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()

RATE_LIMIT_MAX_REQUESTS = 5


class SetPasswordRequest(BaseModel):
    access_token: str
    old_password: str
    new_password: str


class SetPasswordResponse(BaseModel):
    access_token: str
    refresh_token: str


@router.post("/set-password", response_model=SetPasswordResponse)
@rate_limit(
    max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="set_password"
)
async def set_password(
    request: Request,
    set_pass_data: SetPasswordRequest,
    service: SetPassService = Depends(get_set_password_service),
):
    logger.info("SetPassword endpoint started")
    try:
        access_token, refresh_token = await service.execute(
            access_token=set_pass_data.access_token,
            old_password=set_pass_data.old_password,
            new_password=set_pass_data.new_password,
        )
    except (InvalidToken, UserNotFoundError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except InvalidOldPassword:
        raise HTTPException(status_code=400, detail="Invalid password")
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
        logger.exception("Unexpected error during set-pass endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("SetPassword finished successfully")
    return SetPasswordResponse(access_token=access_token, refresh_token=refresh_token)
