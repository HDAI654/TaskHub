import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel
from typing import List
from src.modules.org.application.get_project_boards import GetProjectBoardsService
from src.modules.org.presentation.api.v1.dependencies import (
    get_get_project_boards_service,
)
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


class BoardInfo(BaseModel):
    board_id: str
    name: str
    description: str
    created_at: str


class GetProjectBoardsResponse(BaseModel):
    boards: List[BoardInfo]


@router.get("/projects/{project_id}/boards", response_model=GetProjectBoardsResponse)
@rate_limit(
    max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="get_project_boards"
)
async def get_project_boards(
    request: Request,
    project_id: str,
    authorization: str = Header(..., alias="Authorization"),
    service: GetProjectBoardsService = Depends(get_get_project_boards_service),
):
    logger.info("GetProjectBoards endpoint started")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    access_token = authorization.split(" ")[1]

    try:
        boards = await service.execute(
            access_token=access_token,
            project_id=project_id,
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
        logger.exception("Unexpected error during get project boards endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("GetProjectBoards finished successfully")
    return GetProjectBoardsResponse(
        boards=[
            BoardInfo(
                board_id=b.id.value,
                name=b.name.value,
                description=b.description.value,
                created_at=b.created_at.value,
            )
            for b in boards
        ]
    )
