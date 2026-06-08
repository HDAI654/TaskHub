import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from src.modules.auth.application.reset_pass_token_publisher import (
    ResetPassTokenPublishService,
)
from src.modules.auth.presentation.api.v1.dependencies import (
    get_reset_password_publish_service,
)
from src.modules.auth.exceptions import (
    UserNotFoundError,
    InvalidToken,
    DatabaseError,
    CacheError,
)
from src.modules.core.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()

RATE_LIMIT_MAX_REQUESTS = 3


class ForgetPasswordRequest(BaseModel):
    access_token: str


class ForgetPasswordResponse(BaseModel):
    message: str


@router.post("/forget-password", response_model=ForgetPasswordResponse)
@rate_limit(
    max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="forget_pass"
)
async def publish_reset_token(
    request: Request,
    forget_pass_data: ForgetPasswordRequest,
    service: ResetPassTokenPublishService = Depends(get_reset_password_publish_service),
):
    logger.info("ForgetPassword endpoint started")
    try:
        await service.execute(access_token=forget_pass_data.access_token)
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
        logger.exception("Unexpected error during forget-pass endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("ForgetPassword finished successfully")
    return ForgetPasswordResponse(message="Password reset token sent to email")
