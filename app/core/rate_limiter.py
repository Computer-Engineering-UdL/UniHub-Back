from datetime import datetime
from enum import Enum
from typing import Tuple

from app.core.valkey import valkey_client


class RateLimitStrategy(str, Enum):
    """Different rate limiting strategies"""

    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""

    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds")


class RateLimiter:
    """Rate limiting service using Valkey"""

    @staticmethod
    async def check_rate_limit(
        key: str, max_requests: int, window_seconds: int, strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    ) -> Tuple[bool, int, int]:
        """
        Check if rate limit is exceeded

        Args:
            key: Unique identifier
            max_requests: Maximum number of requests allowed
            window_seconds: Time window in seconds
            strategy: Rate limiting strategy to use

        Returns:
            Tuple of (is_allowed, remaining_requests, retry_after_seconds)
        """
        if strategy == RateLimitStrategy.FIXED_WINDOW:
            return await RateLimiter._fixed_window(key, max_requests, window_seconds)
        elif strategy == RateLimitStrategy.SLIDING_WINDOW:
            return await RateLimiter._sliding_window(key, max_requests, window_seconds)
        elif strategy == RateLimitStrategy.TOKEN_BUCKET:
            return await RateLimiter._token_bucket(key, max_requests, window_seconds)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    @staticmethod
    async def _fixed_window(key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int, int]:
        """
        Fixed window rate limiting
        Simple but can allow bursts at window boundaries
        """
        redis_key = f"rate_limit:fixed:{key}"
        client = valkey_client.client

        current = await client.incr(redis_key)

        if current == 1:
            await client.expire(redis_key, window_seconds)

        ttl = await client.ttl(redis_key)
        retry_after = ttl if ttl > 0 else window_seconds

        is_allowed = current <= max_requests
        remaining = max(0, max_requests - current)

        return is_allowed, remaining, retry_after

    @staticmethod
    async def _sliding_window(key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int, int]:
        """
        Sliding window rate limiting using sorted sets
        More accurate than fixed window
        """
        redis_key = f"rate_limit:sliding:{key}"
        client = valkey_client.client

        now = datetime.utcnow().timestamp()
        window_start = now - window_seconds

        pipe = client.pipeline()

        pipe.zremrangebyscore(redis_key, 0, window_start)

        pipe.zcard(redis_key)

        pipe.zadd(redis_key, {str(now): now})

        pipe.expire(redis_key, window_seconds)

        results = await pipe.execute()
        current_count = results[1]

        is_allowed = current_count < max_requests
        remaining = max(0, max_requests - current_count - 1)

        if not is_allowed:
            oldest_scores = await client.zrange(redis_key, 0, 0, withscores=True)
            if oldest_scores:
                oldest_timestamp = oldest_scores[0][1]
                retry_after = int(oldest_timestamp + window_seconds - now)
            else:
                retry_after = window_seconds
        else:
            retry_after = 0

        return is_allowed, remaining, retry_after

    @staticmethod
    async def _token_bucket(key: str, capacity: int, refill_rate: int) -> Tuple[bool, int, int]:
        """
        Token bucket algorithm
        Allows smooth rate limiting with burst capability
        """
        redis_key = f"rate_limit:bucket:{key}"
        client = valkey_client.client

        now = datetime.utcnow().timestamp()

        bucket_data = await client.hgetall(redis_key)

        if not bucket_data:
            tokens = capacity - 1
            last_refill = now
            await client.hset(redis_key, mapping={"tokens": str(tokens), "last_refill": str(last_refill)})
            await client.expire(redis_key, 3600)
            return True, tokens, 0

        tokens = float(bucket_data.get("tokens", 0))
        last_refill = float(bucket_data.get("last_refill", now))

        time_passed = now - last_refill
        tokens_to_add = time_passed * refill_rate
        tokens = min(capacity, tokens + tokens_to_add)

        if tokens >= 1:
            tokens -= 1
            await client.hset(redis_key, mapping={"tokens": str(tokens), "last_refill": str(now)})
            await client.expire(redis_key, 3600)
            return True, int(tokens), 0
        else:
            tokens_needed = 1 - tokens
            retry_after = int(tokens_needed / refill_rate) + 1
            return False, 0, retry_after

    @staticmethod
    async def reset_rate_limit(key: str):
        """Reset rate limit for a key (useful for testing or admin actions)"""
        patterns = [f"rate_limit:fixed:{key}", f"rate_limit:sliding:{key}", f"rate_limit:bucket:{key}"]
        for pattern in patterns:
            await valkey_client.client.delete(pattern)

    @staticmethod
    async def get_rate_limit_info(key: str, strategy: RateLimitStrategy) -> dict:
        """Get current rate limit status without incrementing"""
        if strategy == RateLimitStrategy.FIXED_WINDOW:
            redis_key = f"rate_limit:fixed:{key}"
            current = await valkey_client.client.get(redis_key)
            ttl = await valkey_client.client.ttl(redis_key)
            return {"current_count": int(current) if current else 0, "reset_in": ttl if ttl > 0 else 0}

        elif strategy == RateLimitStrategy.SLIDING_WINDOW:
            redis_key = f"rate_limit:sliding:{key}"
            count = await valkey_client.client.zcard(redis_key)
            return {"current_count": count, "window_type": "sliding"}

        elif strategy == RateLimitStrategy.TOKEN_BUCKET:
            redis_key = f"rate_limit:bucket:{key}"
            bucket_data = await valkey_client.client.hgetall(redis_key)
            return {
                "tokens": float(bucket_data.get("tokens", 0)) if bucket_data else 0,
                "last_refill": bucket_data.get("last_refill") if bucket_data else None,
            }


class CooldownManager:
    """Simplified cooldown manager for specific actions"""

    @staticmethod
    async def check_cooldown(user_id: int, action: str, cooldown_seconds: int) -> Tuple[bool, int]:
        """
        Check if action is on cooldown

        Returns:
            Tuple of (can_perform, seconds_remaining)
        """
        key = f"cooldown:{action}:{user_id}"
        client = valkey_client.client

        exists = await client.exists(key)

        if exists:
            ttl = await client.ttl(key)
            return False, ttl

        await client.setex(key, cooldown_seconds, "1")
        return True, 0

    @staticmethod
    async def reset_cooldown(user_id: int, action: str):
        """Reset cooldown for a user action"""
        key = f"cooldown:{action}:{user_id}"
        await valkey_client.client.delete(key)

    @staticmethod
    async def get_remaining_cooldown(user_id: int, action: str) -> int:
        """Get remaining cooldown time in seconds"""
        key = f"cooldown:{action}:{user_id}"
        ttl = await valkey_client.client.ttl(key)
        return ttl if ttl > 0 else 0
