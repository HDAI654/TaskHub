import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from src.modules.org.application.add_member import AddMemberService
from src.modules.org.presentation.api.v1.dependencies import get_add_member_service
from src.modules.core.exceptions import (
    InvalidToken,
    UserNotFoundError,
    OrgNotFoundError,
    PermissionDenied,
    MemberDuplicateError,
    MemberNotFoundError,
    DatabaseError,
    CacheError,
)
from src.modules.core.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()

RATE_LIMIT_MAX_REQUESTS = 20


class AddMemberRequest(BaseModel):
    access_token: str
    org_id: str
    user_id: str
    role: str


class AddMemberResponse(BaseModel):
    message: str


@router.post(
    "/orgs/members",
    response_model=AddMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
@rate_limit(max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="add_member")
async def add_member(
    request: Request,
    member_data: AddMemberRequest,
    service: AddMemberService = Depends(get_add_member_service),
):
    logger.info("AddMember endpoint started")
    try:
        await service.execute(
            access_token=member_data.access_token,
            org_id=member_data.org_id,
            user_to_add_id=member_data.user_id,
            role=member_data.role,
        )
    except (InvalidToken, UserNotFoundError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except OrgNotFoundError:
        raise HTTPException(status_code=404, detail="Organization not found")
    except PermissionDenied:
        raise HTTPException(
            status_code=403, detail="Only owner or admin can add members"
        )
    except MemberDuplicateError:
        raise HTTPException(
            status_code=409, detail="User is already a member of this organization"
        )
    except MemberNotFoundError:
        raise HTTPException(status_code=404, detail="User to add not found")
    except DatabaseError:
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )
    except CacheError:
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )
    except Exception as e:
        logger.exception("Unexpected error during add member endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("AddMember finished successfully")
    return AddMemberResponse(message="Member added successfully")
