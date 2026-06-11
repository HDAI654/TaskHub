import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from src.modules.org.application.update_board import UpdateBoardService
from src.modules.org.presentation.api.v1.dependencies import get_update_board_service
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

RATE_LIMIT_MAX_REQUESTS = 20


class UpdateBoardRequest(BaseModel):
    access_token: str
    new_name: Optional[str] = None
    new_description: Optional[str] = None


class UpdateBoardResponse(BaseModel):
    message: str


@router.put("/boards/{board_id}", response_model=UpdateBoardResponse)
@rate_limit(
    max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="update_board"
)
async def update_board(
    request: Request,
    board_id: str,
    board_data: UpdateBoardRequest,
    service: UpdateBoardService = Depends(get_update_board_service),
):
    logger.info("UpdateBoard endpoint started")
    try:
        await service.execute(
            access_token=board_data.access_token,
            board_id=board_id,
            new_name=board_data.new_name,
            new_description=board_data.new_description,
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
            status_code=403, detail="Only owner or admin can edit boards"
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
        logger.exception("Unexpected error during update board endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("UpdateBoard finished successfully")
    return UpdateBoardResponse(message="Board updated successfully")
