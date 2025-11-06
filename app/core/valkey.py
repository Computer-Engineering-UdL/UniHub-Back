"""
Valkey (Redis) client with fake implementation for development
"""

import json
from typing import Any, Optional

from app.core.config import settings


class ValkeyClient:
    """Singleton Valkey client with support for fake Redis in development"""

    _instance: Optional["ValkeyClient"] = None
    _client: Optional[Any] = None
    _is_fake: bool = settings.USE_FAKE_VALKEY

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self):
        """Initialize Valkey connection"""
        if self._client is None:
            if self._is_fake:
                import fakeredis.aioredis as fake_redis

                self._client = fake_redis.FakeRedis(decode_responses=True, encoding="utf-8")
            else:
                import redis.asyncio as redis

                self._client = redis.from_url(
                    settings.VALKEY_URL, encoding="utf-8", decode_responses=True, max_connections=50
                )

    async def disconnect(self):
        """Close Valkey connection"""
        if self._client:
            if not self._is_fake:
                await self._client.close()
            self._client = None

    @property
    def client(self):
        """Get the Valkey client"""
        if self._client is None:
            raise RuntimeError("Valkey client not initialized. Call connect() first.")
        return self._client

    @property
    def is_fake(self) -> bool:
        """Check if using fake Redis"""
        return self._is_fake

    async def publish(self, channel: str, message: dict) -> int:
        """Publish a message to a channel"""
        return await self.client.publish(channel, json.dumps(message))

    async def subscribe(self, *channels: str):
        """Subscribe to channels - returns pubsub object"""
        pubsub = self.client.pubsub()
        await pubsub.subscribe(*channels)
        return pubsub

    async def set_cache(self, key: str, value: Any, ttl: int = 3600):
        """Set a cache value with TTL"""
        await self.client.setex(key, ttl, json.dumps(value))

    async def get_cache(self, key: str) -> Optional[Any]:
        """Get a cache value"""
        value = await self.client.get(key)
        return json.loads(value) if value else None

    async def delete_cache(self, key: str):
        """Delete a cache value"""
        await self.client.delete(key)

    async def set_user_connection(self, user_id: int, connection_id: str):
        """Track active user connections"""
        await self.client.sadd(f"user_connections:{user_id}", connection_id)

    async def remove_user_connection(self, user_id: int, connection_id: str):
        """Remove user connection tracking"""
        await self.client.srem(f"user_connections:{user_id}", connection_id)

    async def get_user_connections(self, user_id: int) -> set:
        """Get all active connections for a user"""
        return await self.client.smembers(f"user_connections:{user_id}")

    async def health_check(self) -> bool:
        """Check if Valkey is healthy"""
        try:
            await self.client.ping()
            return True
        except Exception:
            return False


valkey_client = ValkeyClient()
