import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status, Header
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


class DeleteOrgResponse(BaseModel):
    message: str


@router.delete(
    "/orgs/{org_id}", response_model=DeleteOrgResponse, status_code=status.HTTP_200_OK
)
@rate_limit(max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="delete_org")
async def delete_org(
    request: Request,
    org_id: str,
    authorization: str = Header(..., alias="Authorization"),
    service: DeleteOrgService = Depends(get_delete_org_service),
):
    logger.info("DeleteOrg endpoint started")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    access_token = authorization.split(" ")[1]

    try:
        await service.execute(
            access_token=access_token,
            org_id=org_id,
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
