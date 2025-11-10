from typing import Any, Dict, Optional

from fastapi import WebSocket
from fastapi_websocket_pubsub import PubSubClient

from app.core.logger import logger
from app.core.valkey import valkey_client


class WebSocketManager:
    """
    Manages WebSocket connections and pub/sub via Valkey.
    """

    def __init__(self):
        self.valkey = valkey_client
        self.clients: Dict[str, Dict[str, Any]] = {}

        self.subscriptions: Dict[str, set] = {}

    async def connect(self, websocket: WebSocket, client_id: str, user_id: Optional[int] = None) -> PubSubClient:
        """
        Connect a WebSocket client and set up pub/sub.

        Args:
            websocket: FastAPI WebSocket connection
            client_id: Unique identifier for this connection
            user_id: Optional user ID for tracking connections
        """
        await websocket.accept()

        callback = self._create_message_callback(client_id, websocket)

        default_topics = self._get_default_topics(user_id)

        client = PubSubClient(topics=default_topics, callback=callback)

        self.clients[client_id] = {"client": client, "websocket": websocket, "callback": callback, "user_id": user_id}

        self.subscriptions[client_id] = set(default_topics)

        if user_id:
            await self.valkey.set_user_connection(user_id, client_id)

        logger.info(f"WebSocket client connected: {client_id}, user: {user_id}, topics: {default_topics}")
        return client

    async def disconnect(self, client_id: str, user_id: Optional[int] = None):
        """Disconnect a WebSocket client and clean up."""
        if client_id in self.clients:
            del self.clients[client_id]

        if client_id in self.subscriptions:
            del self.subscriptions[client_id]

        if user_id:
            await self.valkey.remove_user_connection(user_id, client_id)

        logger.info(f"WebSocket client disconnected: {client_id}")

    async def publish(self, topic: str, message: Dict[str, Any], user_id: Optional[int] = None):
        """
        Publish a message to all connected clients subscribed to the topic.

        This bypasses Valkey and sends directly to WebSocket clients.
        Use this for immediate pub/sub within the same process.

        Args:
            topic: Topic name (e.g., "project:42:updates")
            message: Message data
            user_id: Optional user ID to target specific user
        """

        sent_count = 0

        for client_id, client_data in self.clients.items():
            if topic in self.subscriptions.get(client_id, set()):
                if user_id and client_data.get("user_id") != user_id:
                    continue

                try:
                    websocket = client_data["websocket"]
                    await websocket.send_json({"type": "message", "topic": topic, "data": message})
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send message to client {client_id}: {e}")

        logger.debug(f"Published to topic '{topic}': sent to {sent_count} clients")

    async def publish_via_valkey(self, topic: str, message: Dict[str, Any], user_id: Optional[int] = None):
        """
        Publish a message via Valkey pub/sub.
        Use this for cross-process/cross-server pub/sub.

        Args:
            topic: Channel/topic name
            message: Message data (will be JSON serialized)
            user_id: Optional user ID to target specific user
        """

        payload = {"topic": topic, "data": message, "user_id": user_id}

        channel = f"ws:{topic}" if not user_id else f"ws:user:{user_id}:{topic}"
        await self.valkey.publish(channel, payload)

        logger.debug(f"Published to Valkey {channel}: {message}")

    async def subscribe(self, client_id: str, topics: list[str]):
        """Subscribe a client to additional topics."""
        if client_id in self.clients:
            client_data = self.clients[client_id]
            client = client_data["client"]
            callback = client_data["callback"]

            for topic in topics:
                await client.subscribe(topic, callback)

                self.subscriptions[client_id].add(topic)

            logger.info(f"Client {client_id} subscribed to {topics}")

    async def unsubscribe(self, client_id: str, topics: list[str]):
        """Unsubscribe a client from topics."""
        if client_id in self.clients:
            client = self.clients[client_id]["client"]

            for topic in topics:
                await client.unsubscribe(topic)

                self.subscriptions[client_id].discard(topic)

            logger.info(f"Client {client_id} unsubscribed from {topics}")

    def _get_default_topics(self, user_id: Optional[int] = None) -> list[str]:
        """Get default topics for a connection."""
        topics = ["broadcast"]

        if user_id:
            topics.extend(
                [
                    f"user:{user_id}:notifications",
                    f"user:{user_id}:messages",
                ]
            )

        return topics

    def _create_message_callback(self, client_id: str, websocket: WebSocket):
        """Create a callback function for handling incoming messages."""

        async def callback(data: Dict[str, Any], topic: str):
            logger.debug(f"Client {client_id} received on {topic}: {data}")

            try:
                await websocket.send_json({"type": "message", "topic": topic, "data": data})
            except Exception as e:
                logger.error(f"Failed to send message to client {client_id}: {e}")

        return callback


ws_manager = WebSocketManager()
