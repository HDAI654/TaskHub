import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from src.modules.auth.application.login import LoginService
from src.modules.auth.presentation.api.v1.dependencies import get_login_service
from src.modules.auth.exceptions import (
    UserNotFoundError,
    InvalidEmailOrPassword,
    DatabaseError,
    CacheError,
)
from src.modules.core.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()

RATE_LIMIT_MAX_REQUESTS = 10

class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str


@router.post("/login", response_model=LoginResponse)
@rate_limit(max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="login")
async def login(
    request: Request,
    login_data: LoginRequest,
    service: LoginService = Depends(get_login_service),
):
    logger.info("Login endpoint started")
    try:
        access_token, refresh_token = await service.execute(
            email=login_data.email,
            password=login_data.password,
        )
    except (UserNotFoundError, InvalidEmailOrPassword):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    except DatabaseError:
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )
    except CacheError:
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )
    except Exception as e:
        logger.exception("Unexpected error during login endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )
    logger.info("Login finished successfully: email=%s", login_data.email)
    return LoginResponse(access_token=access_token, refresh_token=refresh_token)
