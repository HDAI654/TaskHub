import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from src.modules.org.application.update_column import UpdateColumnService
from src.modules.org.presentation.api.v1.dependencies import get_update_column_service
from src.modules.core.exceptions import (
    InvalidToken,
    UserNotFoundError,
    InvalidNameError,
    InvalidOrderError,
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

RATE_LIMIT_MAX_REQUESTS = 20


class UpdateColumnRequest(BaseModel):
    access_token: str
    new_name: Optional[str] = None
    new_order: Optional[int] = None


class UpdateColumnResponse(BaseModel):
    message: str


@router.put("/columns/{column_id}", response_model=UpdateColumnResponse)
@rate_limit(
    max_requests=RATE_LIMIT_MAX_REQUESTS, window="min", key_prefix="update_column"
)
async def update_column(
    request: Request,
    column_id: str,
    column_data: UpdateColumnRequest,
    service: UpdateColumnService = Depends(get_update_column_service),
):
    logger.info("UpdateColumn endpoint started")
    try:
        await service.execute(
            access_token=column_data.access_token,
            column_id=column_id,
            new_name=column_data.new_name,
            new_order=column_data.new_order,
        )
    except (InvalidToken, UserNotFoundError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except InvalidNameError as e:
        raise HTTPException(
            status_code=400, detail=f"The name of column is invalid: {str(e)}"
        )
    except InvalidOrderError as e:
        raise HTTPException(
            status_code=400, detail=f"The order of column is invalid: {str(e)}"
        )
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
            status_code=403, detail="Only owner or admin can edit columns"
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
        logger.exception("Unexpected error during update column endpoint")
        raise HTTPException(
            status_code=500, detail="Something went wrong. Please try again later."
        )

    logger.info("UpdateColumn finished successfully")
    return UpdateColumnResponse(message="Column updated successfully")
