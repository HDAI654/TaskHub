import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from src.modules.org.application.update_project import UpdateProjectService
from src.modules.org.presentation.api.v1.dependencies import get_update_project_service
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

RATE_LIMIT_MAX_REQUESTS = 20


class UpdateProjectRequest(BaseModel):
    access_token: str
    project_id: str
    new_name: Optional[str] = None
    new_description: Optional[str] = None


class UpdateProjectResponse(BaseModel):
    message: str


@router.put("/projects", response_model=UpdateProjectResponse)
@rate_limit(
    max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="update_project"
)
async def update_project(
    request: Request,
    project_data: UpdateProjectRequest,
    service: UpdateProjectService = Depends(get_update_project_service),
):
    logger.info("UpdateProject endpoint started")
    try:
        await service.execute(
            access_token=project_data.access_token,
            project_id=project_data.project_id,
            new_name=project_data.new_name,
            new_description=project_data.new_description,
        )
    except (InvalidToken, UserNotFoundError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")
    except OrgNotFoundError:
        raise HTTPException(status_code=404, detail="Organization not found")
    except PermissionDenied:
        raise HTTPException(
            status_code=403, detail="Only owner or admin can edit projects"
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
        logger.exception("Unexpected error during update project endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("UpdateProject finished successfully")
    return UpdateProjectResponse(message="Project updated successfully")
