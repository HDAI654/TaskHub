import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel
from src.modules.org.application.get_board import GetBoardService
from src.modules.org.presentation.api.v1.dependencies import get_get_board_service
from src.modules.core.exceptions import (
    InvalidToken,
    UserNotFoundError,
    OrgNotFoundError,
    ProjectNotFoundError,
    BoardNotFoundError,
    PermissionDenied,
    DatabaseError,
    CacheError,
)
from src.modules.core.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()

RATE_LIMIT_MAX_REQUESTS = 30


class GetBoardResponse(BaseModel):
    board_id: str
    project_id: str
    name: str
    description: str
    created_at: str


@router.get("/boards/{board_id}", response_model=GetBoardResponse)
@rate_limit(max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="get_board")
async def get_board(
    request: Request,
    board_id: str,
    authorization: str = Header(..., alias="Authorization"),
    service: GetBoardService = Depends(get_get_board_service),
):
    logger.info("GetBoard endpoint started")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    access_token = authorization.split(" ")[1]

    try:
        board = await service.execute(
            access_token=access_token,
            board_id=board_id,
        )
    except (InvalidToken, UserNotFoundError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except BoardNotFoundError:
        raise HTTPException(status_code=404, detail="Board not found")
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")
    except OrgNotFoundError:
        raise HTTPException(status_code=404, detail="Organization not found")
    except PermissionDenied:
        raise HTTPException(
            status_code=403, detail="You don't have access to this board"
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
        logger.exception("Unexpected error during get board endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("GetBoard finished successfully")
    return GetBoardResponse(
        board_id=board.id.value,
        project_id=board.prj_id.value,
        name=board.name.value,
        description=board.description.value,
        created_at=board.created_at.value,
    )
