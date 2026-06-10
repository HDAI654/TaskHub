import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from src.modules.org.application.get_project import GetProjectService
from src.modules.org.presentation.api.v1.dependencies import get_get_project_service
from src.modules.core.exceptions import (
    InvalidToken,
    UserNotFoundError,
    OrgNotFoundError,
    ProjectNotFoundError,
    PermissionDenied,
    DatabaseError,
    CacheError,
)
from src.modules.core.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()

RATE_LIMIT_MAX_REQUESTS = 30


class GetProjectRequest(BaseModel):
    access_token: str
    project_id: str


class GetProjectResponse(BaseModel):
    project_id: str
    org_id: str
    name: str
    description: str
    created_at: str


@router.post("/projects/get", response_model=GetProjectResponse)
@rate_limit(
    max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="get_project"
)
async def get_project(
    request: Request,
    project_data: GetProjectRequest,
    service: GetProjectService = Depends(get_get_project_service),
):
    logger.info("GetProject endpoint started")
    try:
        project = await service.execute(
            access_token=project_data.access_token,
            project_id=project_data.project_id,
        )
    except (InvalidToken, UserNotFoundError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")
    except OrgNotFoundError:
        raise HTTPException(status_code=404, detail="Organization not found")
    except PermissionDenied:
        raise HTTPException(
            status_code=403, detail="You don't have access to this project"
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
        logger.exception("Unexpected error during get project endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("GetProject finished successfully")
    return GetProjectResponse(
        project_id=project.id.value,
        org_id=project.org_id.value,
        name=project.name.value,
        description=project.description.value,
        created_at=project.created_at.value,
    )
