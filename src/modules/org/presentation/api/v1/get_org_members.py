import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from src.modules.org.application.get_org_members import GetOrgMembersService
from src.modules.org.presentation.api.v1.dependencies import get_get_org_members_service
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


class GetOrgMembersRequest(BaseModel):
    access_token: str
    org_id: str
    role: Optional[str] = None


class MemberInfo(BaseModel):
    user_id: str
    role: str
    joined_at: str


class GetOrgMembersResponse(BaseModel):
    members: List[MemberInfo]


@router.post("/orgs/members/list", response_model=GetOrgMembersResponse)
@rate_limit(
    max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="get_org_members"
)
async def get_org_members(
    request: Request,
    members_data: GetOrgMembersRequest,
    service: GetOrgMembersService = Depends(get_get_org_members_service),
):
    logger.info("GetOrgMembers endpoint started")
    try:
        members = await service.execute(
            access_token=members_data.access_token,
            org_id=members_data.org_id,
            role=members_data.role,
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
        logger.exception("Unexpected error during get org members endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("GetOrgMembers finished successfully")
    return GetOrgMembersResponse(
        members=[
            MemberInfo(
                user_id=member["user_id"],
                role=member["role"],
                joined_at=member["joined_at"],
            )
            for member in members
        ]
    )
