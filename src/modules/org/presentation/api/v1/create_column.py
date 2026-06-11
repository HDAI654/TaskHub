import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from src.modules.org.application.create_column import CreateColumnService
from src.modules.org.presentation.api.v1.dependencies import get_create_column_service
from src.modules.core.exceptions import (
    InvalidToken,
    UserNotFoundError,
    OrgNotFoundError,
    ProjectNotFoundError,
    BoardNotFoundError,
    PermissionDenied,
    InvalidNameError,
    InvalidOrderError,
    DatabaseError,
    CacheError,
)
from src.modules.core.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()

RATE_LIMIT_MAX_REQUESTS = 20


class CreateColumnRequest(BaseModel):
    access_token: str
    name: str
    order: int


class CreateColumnResponse(BaseModel):
    column_id: str
    name: str
    order: int


@router.post(
    "/boards/{board_id}/columns",
    response_model=CreateColumnResponse,
    status_code=status.HTTP_201_CREATED,
)
@rate_limit(
    max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="create_column"
)
async def create_column(
    request: Request,
    board_id: str,
    column_data: CreateColumnRequest,
    service: CreateColumnService = Depends(get_create_column_service),
):
    logger.info("CreateColumn endpoint started")
    try:
        column = await service.execute(
            access_token=column_data.access_token,
            board_id=board_id,
            name=column_data.name,
            order=column_data.order,
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
            status_code=403, detail="Only owner or admin can create columns"
        )
    except InvalidNameError as e:
        raise HTTPException(
            status_code=400, detail=f"The name of column is invalid: {str(e)}"
        )
    except InvalidOrderError as e:
        raise HTTPException(
            status_code=400, detail=f"The order of column is invalid: {str(e)}"
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
        logger.exception("Unexpected error during create column endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("CreateColumn finished successfully")
    return CreateColumnResponse(
        column_id=column.id.value,
        name=column.name.value,
        order=column.order.value,
    )
