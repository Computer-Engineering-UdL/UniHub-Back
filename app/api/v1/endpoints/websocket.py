import uuid
from typing import Optional

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.core.dependencies import get_current_user_ws
from app.core.logger import logger
from app.core.websocket import ws_manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, user: Optional[dict] = Depends(get_current_user_ws)):
    """
    WebSocket endpoint for real-time pub/sub.

    Usage:
        ws://localhost:8080/api/v1/ws?token=<jwt_token>

    Subscribed topics:
        - ws:broadcast (all clients)
        - ws:user:{user_id}:notifications (user-specific)
        - ws:user:{user_id}:messages (user-specific)
    """
    client_id = str(uuid.uuid4())
    user_id = user.get("sub") if user else None

    try:
        client = await ws_manager.connect(websocket, client_id, user_id)

        async with client:
            try:
                while True:
                    data = await websocket.receive_json()

                    action = data.get("action")

                    if action == "subscribe":
                        topics = data.get("topics", [])
                        await ws_manager.subscribe(client_id, topics)
                        await websocket.send_json({"type": "subscribed", "topics": topics})

                    elif action == "unsubscribe":
                        topics = data.get("topics", [])
                        await ws_manager.unsubscribe(client_id, topics)
                        await websocket.send_json({"type": "unsubscribed", "topics": topics})

                    elif action == "ping":
                        await websocket.send_json({"type": "pong"})

            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected normally")

    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")

    finally:
        await ws_manager.disconnect(client_id, user_id)
