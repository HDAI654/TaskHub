from fastapi import APIRouter
from src.modules.card.presentation.websocket import router as websocket_router

router = APIRouter(prefix="/ws", tags=["WebSocket"])


router.include_router(websocket_router)
