import uuid
from typing import Dict, Set

from fastapi import WebSocket

from app.domains.websocket.websocket_repository import SocketRepository


class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

        self.user_connections: Dict[str, Set[str]] = {}

        self.repository = SocketRepository()

    async def connect(self, websocket: WebSocket, user_id: uuid.UUID, connection_id: str):
        """
        Accepts the socket, stores it in memory, and syncs status to Valkey/Redis.
        """
        await websocket.accept()

        self.active_connections[connection_id] = websocket

        user_id_str = str(user_id)

        if user_id_str not in self.user_connections:
            self.user_connections[user_id_str] = set()
        self.user_connections[user_id_str].add(connection_id)

        await self.repository.add_user_connection(user_id_str, connection_id)

    async def disconnect(self, user_id: uuid.UUID, connection_id: str):
        """
        Removes socket from memory and Valkey/Redis.
        """

        if connection_id in self.active_connections:
            del self.active_connections[connection_id]

        user_id_str = str(user_id)
        if user_id_str in self.user_connections:
            self.user_connections[user_id_str].discard(connection_id)
            if not self.user_connections[user_id_str]:
                del self.user_connections[user_id_str]

        await self.repository.remove_user_connection(user_id_str, connection_id)

    async def send_to_connection(self, connection_id: str, message: dict):
        """
        Send a message to a specific connection ID (if it exists on this server).
        """
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_json(message)
            except RuntimeError:
                pass
            except Exception as e:
                print(f"Error sending to connection {connection_id}: {e}")

    async def send_to_user(self, user_id: uuid.UUID, message: dict):
        """
        Send message to all active connections for a specific user on THIS server.
        """
        user_id_str = str(user_id)
        if user_id_str in self.user_connections:
            for conn_id in list(self.user_connections[user_id_str]):
                await self.send_to_connection(conn_id, message)

    async def broadcast(self, message: dict):
        """
        Send message to ALL connected users on THIS server.
        """

        for websocket in list(self.active_connections.values()):
            try:
                await websocket.send_json(message)
            except Exception:
                pass


ws_manager = WebSocketManager()
