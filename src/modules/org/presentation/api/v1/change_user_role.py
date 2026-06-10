import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from src.modules.org.application.change_user_role import ChangeUserRoleService
from src.modules.org.presentation.api.v1.dependencies import (
    get_change_user_role_service,
)
from src.modules.core.exceptions import (
    InvalidToken,
    UserNotFoundError,
    OrgNotFoundError,
    PermissionDenied,
    MemberNotFoundError,
    DatabaseError,
    CacheError,
)
from src.modules.core.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()

RATE_LIMIT_MAX_REQUESTS = 20


class ChangeUserRoleRequest(BaseModel):
    access_token: str
    new_role: str


class ChangeUserRoleResponse(BaseModel):
    message: str


@router.put(
    "/orgs/{org_id}/members/{user_id}/role", response_model=ChangeUserRoleResponse
)
@rate_limit(
    max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="change_role"
)
async def change_user_role(
    request: Request,
    org_id: str,
    user_id: str,
    role_data: ChangeUserRoleRequest,
    service: ChangeUserRoleService = Depends(get_change_user_role_service),
):
    logger.info("ChangeUserRole endpoint started")
    try:
        await service.execute(
            access_token=role_data.access_token,
            org_id=org_id,
            target_user_id=user_id,
            new_role=role_data.new_role,
        )
    except (InvalidToken, UserNotFoundError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except OrgNotFoundError:
        raise HTTPException(status_code=404, detail="Organization not found")
    except PermissionDenied:
        raise HTTPException(status_code=403, detail="Only owner can change user roles")
    except MemberNotFoundError:
        raise HTTPException(
            status_code=404, detail="User is not a member of this organization"
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
        logger.exception("Unexpected error during change user role endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("ChangeUserRole finished successfully")
    return ChangeUserRoleResponse(message="User role changed successfully")
