from app.core.valkey import valkey_client


class SocketRepository:
    """
    Handles raw data operations for WebSockets in Redis.
    """

    @property
    def _redis(self):
        return valkey_client.client

    async def add_user_connection(self, user_id: str, connection_id: str):
        await self._redis.sadd(f"user_connections:{user_id}", connection_id)

    async def remove_user_connection(self, user_id: str, connection_id: str):
        await self._redis.srem(f"user_connections:{user_id}", connection_id)

    async def get_user_connections(self, user_id: str) -> set[str]:
        return await self._redis.smembers(f"user_connections:{user_id}")
