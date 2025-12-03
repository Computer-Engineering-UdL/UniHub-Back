import json
from typing import Any, Optional

import redis.asyncio as redis

from app.core.config import settings


class ValkeyClient:
    def __init__(self, url: str, use_fake: bool = False):
        self._url = url
        self._use_fake = use_fake
        self._client: Optional[redis.Redis] = None

    async def connect(self):
        if self._client:
            return

        if self._use_fake:
            from fakeredis import aioredis as fake_redis

            self._client = fake_redis.FakeRedis(decode_responses=True, encoding="utf-8")
        else:
            self._client = redis.from_url(self._url, encoding="utf-8", decode_responses=True, max_connections=50)

    async def disconnect(self):
        if self._client and not self._use_fake:
            await self._client.close()
        self._client = None

    @property
    def client(self) -> redis.Redis:
        if not self._client:
            raise RuntimeError("Valkey client not initialized.")
        return self._client

    async def publish(self, channel: str, message: dict | str) -> int:
        payload = json.dumps(message) if isinstance(message, dict) else message
        return await self.client.publish(channel, payload)

    async def set(self, key: str, value: Any, ttl: int = settings.VALKEY_TTL):
        if hasattr(value, "model_dump_json"):
            await self.client.setex(key, ttl, value.model_dump_json())
        else:
            await self.client.setex(
                key,
                ttl,
                json.dumps(value, default=lambda o: o.__dict__)
            )

    async def unset(self, key: str):
        await self.client.delete(key)

    async def get(self, key: str) -> Optional[Any]:
        val = await self.client.get(key)
        return json.loads(val) if val else None

    async def has(self, key: str) -> bool:
        return await self.client.exists(key)

    def raw(self):
        return self.client


valkey_client = ValkeyClient(settings.VALKEY_URL, settings.USE_FAKE_VALKEY)
