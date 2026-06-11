import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel
from src.modules.org.application.delete_board import DeleteBoardService
from src.modules.org.presentation.api.v1.dependencies import get_delete_board_service
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

RATE_LIMIT_MAX_REQUESTS = 10


class DeleteBoardResponse(BaseModel):
    message: str


@router.delete("/boards/{board_id}", response_model=DeleteBoardResponse)
@rate_limit(
    max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="delete_board"
)
async def delete_board(
    request: Request,
    board_id: str,
    authorization: str = Header(..., alias="Authorization"),
    service: DeleteBoardService = Depends(get_delete_board_service),
):
    logger.info("DeleteBoard endpoint started")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    access_token = authorization.split(" ")[1]

    try:
        await service.execute(
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
            status_code=403, detail="Only owner or admin can delete boards"
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
        logger.exception("Unexpected error during delete board endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("DeleteBoard finished successfully")
    return DeleteBoardResponse(message="Board deleted successfully")
