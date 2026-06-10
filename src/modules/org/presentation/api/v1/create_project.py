import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from src.modules.org.application.create_project import CreateProjectService
from src.modules.org.presentation.api.v1.dependencies import get_create_project_service
from src.modules.core.exceptions import (
    InvalidToken,
    UserNotFoundError,
    OrgNotFoundError,
    PermissionDenied,
    InvalidNameError,
    DatabaseError,
    CacheError,
)
from src.modules.core.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()

RATE_LIMIT_MAX_REQUESTS = 20


class CreateProjectRequest(BaseModel):
    access_token: str
    name: str
    description: str


class CreateProjectResponse(BaseModel):
    project_id: str
    name: str
    description: str


@router.post(
    "/orgs/{org_id}/projects",
    response_model=CreateProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
@rate_limit(
    max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="create_project"
)
async def create_project(
    request: Request,
    org_id: str,
    project_data: CreateProjectRequest,
    service: CreateProjectService = Depends(get_create_project_service),
):
    logger.info("CreateProject endpoint started")
    try:
        project = await service.execute(
            access_token=project_data.access_token,
            org_id=org_id,
            name=project_data.name,
            description=project_data.description,
        )
    except (InvalidToken, UserNotFoundError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except OrgNotFoundError:
        raise HTTPException(status_code=404, detail="Organization not found")
    except PermissionDenied:
        raise HTTPException(
            status_code=403, detail="Only owner or admin can create projects"
        )
    except InvalidNameError as e:
        raise HTTPException(
            status_code=400, detail=f"The name of project is invalid: {str(e)}"
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
        logger.exception("Unexpected error during create project endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("CreateProject finished successfully")
    return CreateProjectResponse(
        project_id=project.id.value,
        name=project.name.value,
        description=project.description.value,
    )
