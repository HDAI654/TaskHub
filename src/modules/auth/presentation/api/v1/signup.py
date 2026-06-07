import logging
from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel
from src.modules.auth.application.signup import SignupService
from src.modules.auth.presentation.api.v1.dependencies import get_signup_service
from src.modules.auth.exceptions import (
    WeakPasswordError,
    InvalidEmailError,
    DatabaseError
)

logger = logging.getLogger(__name__)

router = APIRouter()

class RegisterRequest(BaseModel):
    email: str
    password: str


class RegisterResponse(BaseModel):
    access_token: str
    refresh_token: str


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    service: SignupService = Depends(get_signup_service),
):  
    logger.info("Register endpoint started")
    try:
        access_token, refresh_token = await service.execute(
            email=request.email,
            password=request.password,
        )
    except WeakPasswordError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidEmailError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError:
        raise HTTPException(status_code=500, detail="Something went wrong. Please try again later.")
    except Exception as e:
        logger.exception("Unexpected error during register endpoint")
        raise HTTPException(status_code=500, detail="Something went wrong. Please try again later.")
    
    logger.info("Register finished successfully: email=%s", request.email)
    return RegisterResponse(access_token=access_token, refresh_token=refresh_token)