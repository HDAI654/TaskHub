import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List
from src.modules.org.application.get_org_projects import GetOrgProjectsService
from src.modules.org.presentation.api.v1.dependencies import (
    get_get_org_projects_service,
)
from src.modules.core.exceptions import (
    InvalidToken,
    UserNotFoundError,
    OrgNotFoundError,
    PermissionDenied,
    DatabaseError,
    CacheError,
)
from src.modules.core.rate_limiter import rate_limit
from src.modules.org.domain.entities.project import PrjEntity

logger = logging.getLogger(__name__)

router = APIRouter()

RATE_LIMIT_MAX_REQUESTS = 30


class GetOrgProjectsRequest(BaseModel):
    access_token: str
    org_id: str


class ProjectInfo(BaseModel):
    project_id: str
    name: str
    description: str
    created_at: str


class GetOrgProjectsResponse(BaseModel):
    projects: List[ProjectInfo]


@router.post("/orgs/projects", response_model=GetOrgProjectsResponse)
@rate_limit(
    max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="get_org_projects"
)
async def get_org_projects(
    request: Request,
    projects_data: GetOrgProjectsRequest,
    service: GetOrgProjectsService = Depends(get_get_org_projects_service),
):
    logger.info("GetOrgProjects endpoint started")
    try:
        projects = await service.execute(
            access_token=projects_data.access_token,
            org_id=projects_data.org_id,
        )
    except (InvalidToken, UserNotFoundError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except OrgNotFoundError:
        raise HTTPException(status_code=404, detail="Organization not found")
    except PermissionDenied:
        raise HTTPException(
            status_code=403, detail="You don't have access to this organization"
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
        logger.exception("Unexpected error during get org projects endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("GetOrgProjects finished successfully")
    return GetOrgProjectsResponse(
        projects=[
            ProjectInfo(
                project_id=p.id.value,
                name=p.name.value,
                description=p.description.value,
                created_at=p.created_at.value,
            )
            for p in projects
        ]
    )
