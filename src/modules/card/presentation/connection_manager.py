import logging
import json
from fastapi import WebSocket, WebSocketDisconnect, Depends, APIRouter

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections per board room."""

    def __init__(self):
        self.active_connections: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, board_id: str):
        """Accept a new WebSocket connection and add it to the board room."""
        await websocket.accept()
        if board_id not in self.active_connections:
            self.active_connections[board_id] = set()
        self.active_connections[board_id].add(websocket)
        logger.info(
            f"WebSocket connected to board {board_id}. Total connections: {len(self.active_connections[board_id])}"
        )

    def disconnect(self, websocket: WebSocket, board_id: str):
        """Remove a WebSocket connection from the board room."""
        if board_id in self.active_connections:
            self.active_connections[board_id].discard(websocket)
            if not self.active_connections[board_id]:
                del self.active_connections[board_id]
        logger.info(f"WebSocket disconnected from board {board_id}")

    async def broadcast(self, board_id: str, message: dict):
        """Send a JSON message to all connections in the board room."""
        if board_id not in self.active_connections:
            return
        data = json.dumps(message, default=str)
        for connection in self.active_connections[board_id]:
            try:
                await connection.send_text(data)
            except Exception as e:
                logger.exception(
                    f"Failed to send message to a client in board {board_id}: {e}"
                )
