import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from src.modules.org.application.delete_org import DeleteOrgService
from src.modules.org.presentation.api.v1.dependencies import get_delete_org_service
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

RATE_LIMIT_MAX_REQUESTS = 5


class DeleteOrgRequest(BaseModel):
    access_token: str
    org_id: str


class DeleteOrgResponse(BaseModel):
    message: str


@router.post(
    "/orgs/delete", response_model=DeleteOrgResponse, status_code=status.HTTP_200_OK
)
@rate_limit(max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="delete_org")
async def delete_org(
    request: Request,
    org_data: DeleteOrgRequest,
    service: DeleteOrgService = Depends(get_delete_org_service),
):
    logger.info("DeleteOrg endpoint started")
    try:
        await service.execute(
            access_token=org_data.access_token,
            org_id=org_data.org_id,
        )
    except (InvalidToken, UserNotFoundError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except OrgNotFoundError:
        raise HTTPException(status_code=404, detail="Organization not found")
    except PermissionDenied:
        raise HTTPException(
            status_code=403, detail="Only owner can delete organization"
        )
    except DatabaseError:
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )
    except CacheError:
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )
    except Exception as e:
        logger.exception("Unexpected error during delete org endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("DeleteOrg finished successfully")
    return DeleteOrgResponse(message="Organization deleted successfully")
