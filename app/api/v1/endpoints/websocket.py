import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketState
from websockets.frames import CloseCode

from app.core import get_db
from app.core.valkey import valkey_client
from app.domains.auth.auth_service import verify_token
from app.domains.websocket.websocket_connection_service import WebSocketConnectionService
from app.domains.websocket.websocket_manager import ws_manager

router = APIRouter()
logger = logging.getLogger(__name__)


async def redis_listener(websocket: WebSocket, pubsub):
    """
    Background task: Listens for Redis messages and forwards them to the WebSocket.
    """
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    payload = message["data"]

                    if isinstance(payload, bytes):
                        payload = payload.decode("utf-8")

                    data = json.loads(payload)

                    if websocket.client_state == WebSocketState.CONNECTED:
                        await websocket.send_json(data)
                except Exception as e:
                    logger.error(f"Error forwarding Redis message to WS: {e}")
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Redis listener error: {e}")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...), db: Session = Depends(get_db)):
    connection_id = str(uuid.uuid4())
    user_id = None
    pubsub = None
    listener_task = None

    try:
        payload = await verify_token(token)
        user_id = uuid.UUID(payload.get("sub"))

        await ws_manager.connect(websocket, user_id, connection_id)

        ws_connection_service = WebSocketConnectionService(db)

        channel_topics = ws_connection_service.get_user_channel_subscriptions(user_id)

        topics_to_subscribe = [f"user:{user_id}", "global"] + (channel_topics or [])

        pubsub = valkey_client.client.pubsub()
        await pubsub.subscribe(*topics_to_subscribe)

        listener_task = asyncio.create_task(redis_listener(websocket, pubsub))

        while True:
            client_data = await websocket.receive_json()

            await ws_connection_service.handle_client_message(client_data, user_id)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket authentication/connection error: {e}")

        if websocket.client_state == WebSocketState.CONNECTING:
            await websocket.close(code=CloseCode.POLICY_VIOLATION)
        elif websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close(code=CloseCode.INTERNAL_ERROR)
    finally:
        if listener_task:
            listener_task.cancel()
            try:
                await listener_task
            except asyncio.CancelledError:
                pass

        if pubsub:
            await pubsub.unsubscribe()
            await pubsub.close()

        if user_id:
            await ws_manager.disconnect(user_id, connection_id)
