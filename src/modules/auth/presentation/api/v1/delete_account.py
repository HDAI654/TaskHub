import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from src.modules.auth.application.del_account import DelAccountService
from src.modules.auth.presentation.api.v1.dependencies import get_del_account_service
from src.modules.auth.exceptions import (
    UserNotFoundError,
    InvalidToken,
    DatabaseError,
    CacheError,
)
from src.modules.core.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()

RATE_LIMIT_MAX_REQUESTS = 30


class DelAccRequest(BaseModel):
    access_token: str


class DelAccResponse(BaseModel):
    message: str


@router.post("/delete-account", status_code=200, response_model=DelAccResponse)
@rate_limit(max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="del_acc")
async def delete_account(
    request: Request,
    del_acc_data: DelAccRequest,
    service: DelAccountService = Depends(get_del_account_service),
):
    logger.info("DeleteAccount endpoint started")
    try:
        await service.execute(
            access_token=del_acc_data.access_token,
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
        logger.exception("Unexpected error during delete account endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("DeleteAccount finished successfully")
    return DelAccResponse(message="Account deleted successfully")
