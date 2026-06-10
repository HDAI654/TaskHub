import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel
from src.modules.org.application.remove_member import RemoveMemberService
from src.modules.org.presentation.api.v1.dependencies import get_remove_member_service
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


class RemoveMemberResponse(BaseModel):
    message: str


@router.delete("/orgs/{org_id}/members/{user_id}", response_model=RemoveMemberResponse)
@rate_limit(
    max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="remove_member"
)
async def remove_member(
    request: Request,
    org_id: str,
    user_id: str,
    authorization: str = Header(..., alias="Authorization"),
    service: RemoveMemberService = Depends(get_remove_member_service),
):
    logger.info("RemoveMember endpoint started")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    access_token = authorization.split(" ")[1]

    try:
        await service.execute(
            access_token=access_token,
            org_id=org_id,
            user_to_remove_id=user_id,
        )
    except (InvalidToken, UserNotFoundError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except OrgNotFoundError:
        raise HTTPException(status_code=404, detail="Organization not found")
    except PermissionDenied:
        raise HTTPException(
            status_code=403, detail="Only owner or admin can remove members"
        )
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
        logger.exception("Unexpected error during remove member endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("RemoveMember finished successfully")
    return RemoveMemberResponse(message="Member removed successfully")
