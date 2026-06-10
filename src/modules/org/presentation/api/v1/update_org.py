import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from src.modules.org.application.update_org import UpdateOrgService
from src.modules.org.presentation.api.v1.dependencies import get_update_org_service
from src.modules.core.exceptions import (
    InvalidToken,
    UserNotFoundError,
    OrgNotFoundError,
    PermissionDenied,
    DatabaseError,
    CacheError,
)
from src.modules.core.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()

RATE_LIMIT_MAX_REQUESTS = 10


class UpdateOrgRequest(BaseModel):
    access_token: str
    new_name: str


class UpdateOrgResponse(BaseModel):
    message: str


@router.put("/orgs/{org_id}", response_model=UpdateOrgResponse)
@rate_limit(max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="update_org")
async def update_org(
    request: Request,
    org_id: str,
    org_data: UpdateOrgRequest,
    service: UpdateOrgService = Depends(get_update_org_service),
):
    logger.info("UpdateOrg endpoint started")
    try:
        await service.execute(
            access_token=org_data.access_token,
            org_id=org_id,
            new_name=org_data.new_name,
        )
    except (InvalidToken, UserNotFoundError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except OrgNotFoundError:
        raise HTTPException(status_code=404, detail="Organization not found")
    except PermissionDenied:
        raise HTTPException(status_code=403, detail="Only owner can edit organization")
    except DatabaseError:
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )
    except CacheError:
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )
    except Exception as e:
        logger.exception("Unexpected error during update org endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("UpdateOrg finished successfully")
    return UpdateOrgResponse(message="Organization updated successfully")
