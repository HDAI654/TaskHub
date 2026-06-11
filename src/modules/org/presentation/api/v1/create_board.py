import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from src.modules.org.application.create_board import CreateBoardService
from src.modules.org.presentation.api.v1.dependencies import get_create_board_service
from src.modules.core.exceptions import (
    InvalidToken,
    UserNotFoundError,
    OrgNotFoundError,
    ProjectNotFoundError,
    PermissionDenied,
    InvalidNameError,
    InvalidDescriptionError,
    DatabaseError,
    CacheError,
)
from src.modules.core.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()

RATE_LIMIT_MAX_REQUESTS = 20


class CreateBoardRequest(BaseModel):
    access_token: str
    name: str
    description: str


class CreateBoardResponse(BaseModel):
    board_id: str
    name: str
    description: str


@router.post(
    "/projects/{project_id}/boards",
    response_model=CreateBoardResponse,
    status_code=status.HTTP_201_CREATED,
)
@rate_limit(
    max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="create_board"
)
async def create_board(
    request: Request,
    project_id: str,
    board_data: CreateBoardRequest,
    service: CreateBoardService = Depends(get_create_board_service),
):
    logger.info("CreateBoard endpoint started")
    try:
        board = await service.execute(
            access_token=board_data.access_token,
            project_id=project_id,
            name=board_data.name,
            description=board_data.description,
        )
    except (InvalidToken, UserNotFoundError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")
    except OrgNotFoundError:
        raise HTTPException(status_code=404, detail="Organization not found")
    except PermissionDenied:
        raise HTTPException(
            status_code=403, detail="Only owner or admin can create boards"
        )
    except InvalidNameError as e:
        raise HTTPException(
            status_code=400, detail=f"The name of board is invalid: {str(e)}"
        )
    except InvalidDescriptionError as e:
        raise HTTPException(
            status_code=400, detail=f"The description of board is invalid: {str(e)}"
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
        logger.exception("Unexpected error during create board endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("CreateBoard finished successfully")
    return CreateBoardResponse(
        board_id=board.id.value,
        name=board.name.value,
        description=board.description.value,
    )
