import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from src.modules.auth.application.invite import (
    InviteService,
)
from src.modules.auth.presentation.api.v1.dependencies import (
    get_invite_service,
)
from src.modules.core.exceptions import (
    UserNotFoundError,
    InvalidToken,
    InvalidEmailError,
    DatabaseError,
    CacheError,
)
from src.modules.core.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()

RATE_LIMIT_MAX_REQUESTS = 3


class InviteRequest(BaseModel):
    access_token: str
    email: str


class InviteResponse(BaseModel):
    message: str


@router.post("/invite", status_code=200, response_model=InviteResponse)
@rate_limit(max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="invite")
async def invite_new_user(
    request: Request,
    invite_data: InviteRequest,
    service: InviteService = Depends(get_invite_service),
):
    logger.info("Invite endpoint started")
    try:
        await service.execute(
            access_token=invite_data.access_token, email=invite_data.email
        )
    except (InvalidToken, UserNotFoundError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except InvalidEmailError:
        raise HTTPException(status_code=400, detail="Invite email is invalid")
    except DatabaseError:
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )
    except CacheError:
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )
    except Exception as e:
        logger.exception("Unexpected error during invite endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("Invite finished successfully")
    return InviteResponse(message="User invited successfully")
