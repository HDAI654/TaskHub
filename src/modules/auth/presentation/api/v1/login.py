import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.modules.auth.application.login import LoginService
from src.modules.auth.presentation.api.v1.dependencies import get_login_service
from src.modules.auth.exceptions import (
    UserNotFoundError,
    InvalidEmailOrPassword,
    DatabaseError,
    CacheError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    service: LoginService = Depends(get_login_service),
):
    logger.info("Login endpoint started")
    try:
        access_token, refresh_token = await service.execute(
            email=request.email,
            password=request.password,
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
    logger.info("Login finished successfully: email=%s", request.email)
    return LoginResponse(access_token=access_token, refresh_token=refresh_token)
