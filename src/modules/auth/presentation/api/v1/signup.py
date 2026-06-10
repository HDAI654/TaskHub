import logging
from fastapi import APIRouter, Depends, status, HTTPException, Request
from pydantic import BaseModel
from src.modules.auth.application.signup import SignupService
from src.modules.auth.presentation.api.v1.dependencies import get_signup_service
from src.modules.core.exceptions import (
    WeakPasswordError,
    InvalidEmailError,
    UserDuplicateError,
    DatabaseError,
)
from src.modules.core.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()

RATE_LIMIT_MAX_REQUESTS = 5


class RegisterRequest(BaseModel):
    email: str
    password: str


class RegisterResponse(BaseModel):
    access_token: str
    refresh_token: str


@router.post(
    "/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED
)
@rate_limit(max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="register")
async def register(
    request: Request,
    register_data: RegisterRequest,
    service: SignupService = Depends(get_signup_service),
):
    logger.info("Register endpoint started")
    try:
        access_token, refresh_token = await service.execute(
            email=register_data.email,
            password=register_data.password,
        )
    except WeakPasswordError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidEmailError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except UserDuplicateError as e:
        raise HTTPException(
            status_code=400, detail="Another user already uses this email."
        )
    except DatabaseError:
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )
    except Exception as e:
        logger.exception("Unexpected error during register endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("Register finished successfully: email=%s", register_data.email)
    return RegisterResponse(access_token=access_token, refresh_token=refresh_token)
