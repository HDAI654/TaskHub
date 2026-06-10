import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel
from src.modules.org.application.get_org import GetOrgService
from src.modules.org.presentation.api.v1.dependencies import get_get_org_service
from src.modules.core.exceptions import (
    InvalidToken,
    UserNotFoundError,
    OrgNotFoundError,
    DatabaseError,
    CacheError,
)
from src.modules.core.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()

RATE_LIMIT_MAX_REQUESTS = 30


class GetOrgResponse(BaseModel):
    org_id: str
    name: str
    created_at: str


@router.get("/orgs/{org_id}", response_model=GetOrgResponse)
@rate_limit(max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="get_org")
async def get_org(
    request: Request,
    org_id: str,
    authorization: str = Header(..., alias="Authorization"),
    service: GetOrgService = Depends(get_get_org_service),
):
    logger.info("GetOrg endpoint started")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    access_token = authorization.split(" ")[1]

    try:
        org = await service.execute(
            access_token=access_token,
            org_id=org_id,
        )
    except (InvalidToken, UserNotFoundError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except OrgNotFoundError:
        raise HTTPException(status_code=404, detail="Organization not found")
    except DatabaseError:
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )
    except CacheError:
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )
    except Exception as e:
        logger.exception("Unexpected error during get org endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("GetOrg finished successfully")
    return GetOrgResponse(
        org_id=org.id.value,
        name=org.name.value,
        created_at=org.created_at.value,
    )
