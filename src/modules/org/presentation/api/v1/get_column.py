import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel
from src.modules.org.application.get_column import GetColumnService
from src.modules.org.presentation.api.v1.dependencies import get_get_column_service
from src.modules.core.exceptions import (
    InvalidToken,
    UserNotFoundError,
    OrgNotFoundError,
    ProjectNotFoundError,
    BoardNotFoundError,
    ColumnNotFoundError,
    PermissionDenied,
    DatabaseError,
    CacheError,
)
from src.modules.core.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()

RATE_LIMIT_MAX_REQUESTS = 30


class GetColumnResponse(BaseModel):
    column_id: str
    board_id: str
    name: str
    order: int


@router.get("/columns/{column_id}", response_model=GetColumnResponse)
@rate_limit(max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="get_column")
async def get_column(
    request: Request,
    column_id: str,
    authorization: str = Header(..., alias="Authorization"),
    service: GetColumnService = Depends(get_get_column_service),
):
    logger.info("GetColumn endpoint started")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    access_token = authorization.split(" ")[1]

    try:
        column = await service.execute(
            access_token=access_token,
            column_id=column_id,
        )
    except (InvalidToken, UserNotFoundError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except ColumnNotFoundError:
        raise HTTPException(status_code=404, detail="Column not found")
    except BoardNotFoundError:
        raise HTTPException(status_code=404, detail="Board not found")
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")
    except OrgNotFoundError:
        raise HTTPException(status_code=404, detail="Organization not found")
    except PermissionDenied:
        raise HTTPException(
            status_code=403, detail="You don't have access to this column"
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
        logger.exception("Unexpected error during get column endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("GetColumn finished successfully")
    return GetColumnResponse(
        column_id=column.id.value,
        board_id=column.board_id.value,
        name=column.name.value,
        order=column.order.value,
    )
