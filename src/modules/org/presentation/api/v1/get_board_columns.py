import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel
from typing import List
from src.modules.org.application.get_board_columns import GetBoardColumnsService
from src.modules.org.presentation.api.v1.dependencies import (
    get_get_board_columns_service,
)
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


class ColumnInfo(BaseModel):
    column_id: str
    name: str
    order: int


class GetBoardColumnsResponse(BaseModel):
    columns: List[ColumnInfo]


@router.get("/boards/{board_id}/columns", response_model=GetBoardColumnsResponse)
@rate_limit(
    max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="get_board_columns"
)
async def get_board_columns(
    request: Request,
    board_id: str,
    authorization: str = Header(..., alias="Authorization"),
    service: GetBoardColumnsService = Depends(get_get_board_columns_service),
):
    logger.info("GetBoardColumns endpoint started")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    access_token = authorization.split(" ")[1]

    try:
        columns = await service.execute(
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
        logger.exception("Unexpected error during get board columns endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("GetBoardColumns finished successfully")
    return GetBoardColumnsResponse(
        columns=[
            ColumnInfo(
                column_id=c.id.value,
                name=c.name.value,
                order=c.order.value,
            )
            for c in columns
        ]
    )
