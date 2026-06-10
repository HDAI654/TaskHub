import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from src.modules.org.application.delete_project import DeleteProjectService
from src.modules.org.presentation.api.v1.dependencies import get_delete_project_service
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

RATE_LIMIT_MAX_REQUESTS = 10


class DeleteProjectRequest(BaseModel):
    access_token: str
    project_id: str


class DeleteProjectResponse(BaseModel):
    message: str


@router.post("/projects/delete", response_model=DeleteProjectResponse)
@rate_limit(
    max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="delete_project"
)
async def delete_project(
    request: Request,
    project_data: DeleteProjectRequest,
    service: DeleteProjectService = Depends(get_delete_project_service),
):
    logger.info("DeleteProject endpoint started")
    try:
        await service.execute(
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
            status_code=403, detail="Only owner or admin can delete projects"
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
        logger.exception("Unexpected error during delete project endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("DeleteProject finished successfully")
    return DeleteProjectResponse(message="Project deleted successfully")
