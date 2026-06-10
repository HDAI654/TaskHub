import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel
from typing import List
from src.modules.org.application.get_user_orgs import GetUserOrgsService
from src.modules.org.presentation.api.v1.dependencies import get_get_user_orgs_service
from src.modules.core.exceptions import (
    InvalidToken,
    UserNotFoundError,
    DatabaseError,
    CacheError,
)
from src.modules.core.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()

RATE_LIMIT_MAX_REQUESTS = 30


class OrgInfo(BaseModel):
    organization_id: str
    name: str
    role: str
    joined_at: str


class GetUserOrgsResponse(BaseModel):
    orgs: List[OrgInfo]


@router.get("/users/orgs", response_model=GetUserOrgsResponse)
@rate_limit(
    max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="get_user_orgs"
)
async def get_user_orgs(
    request: Request,
    authorization: str = Header(..., alias="Authorization"),
    service: GetUserOrgsService = Depends(get_get_user_orgs_service),
):
    logger.info("GetUserOrgs endpoint started")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    access_token = authorization.split(" ")[1]

    try:
        orgs = await service.execute(access_token=access_token)
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
        logger.exception("Unexpected error during get user orgs endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("GetUserOrgs finished successfully")
    return GetUserOrgsResponse(
        orgs=[
            OrgInfo(
                organization_id=org["organization_id"],
                name=org["name"],
                role=org["role"],
                joined_at=org["joined_at"],
            )
            for org in orgs
        ]
    )
