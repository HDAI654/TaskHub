import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from src.modules.org.application.create_org import CreateOrgService
from src.modules.org.presentation.api.v1.dependencies import get_create_org_service
from src.modules.core.exceptions import (
    InvalidToken,
    UserNotFoundError,
    InvalidNameError,
    DatabaseError,
    CacheError,
)
from src.modules.core.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()

RATE_LIMIT_MAX_REQUESTS = 5


class CreateOrgRequest(BaseModel):
    access_token: str
    name: str


class CreateOrgResponse(BaseModel):
    org_id: str
    name: str


@router.post(
    "/orgs", response_model=CreateOrgResponse, status_code=status.HTTP_201_CREATED
)
@rate_limit(max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="create_org")
async def create_org(
    request: Request,
    org_data: CreateOrgRequest,
    service: CreateOrgService = Depends(get_create_org_service),
):
    logger.info("CreateOrg endpoint started")
    try:
        org = await service.execute(
            access_token=org_data.access_token,
            name=org_data.name,
        )
    except (InvalidToken, UserNotFoundError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except InvalidNameError:
        raise HTTPException(status_code=400, detail="Invalid organization name !")
    except DatabaseError:
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )
    except CacheError:
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )
    except Exception as e:
        logger.exception("Unexpected error during create org endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("CreateOrg finished successfully")
    return CreateOrgResponse(org_id=org.id.value, name=org.name.value)
