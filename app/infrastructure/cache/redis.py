"""
Redis cache implementation for distributed caching and rate limiting.
"""

import json
from typing import Any, Optional

import redis.asyncio as redis

from app.core.config import get_settings

settings = get_settings()

# Connection pool for Redis
redis_client: Optional[redis.Redis] = None


async def init_redis() -> redis.Redis:
    """Initialize Redis connection."""
    global redis_client
    redis_client = await redis.from_url(
        settings.REDIS_URL, encoding="utf8", decode_responses=True
    )
    await redis_client.ping()
    return redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    if redis_client:
        await redis_client.close()


class CacheService:
    """Service for distributed caching."""

    def __init__(self, redis: redis.Redis):
        self.redis = redis

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        value = await self.redis.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    async def set(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> None:
        """Set value in cache."""
        if ttl is None:
            ttl = settings.REDIS_CACHE_TTL

        serialized = (
            json.dumps(value) if not isinstance(value, str) else value
        )
        await self.redis.setex(key, ttl, serialized)

    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        await self.redis.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return await self.redis.exists(key)

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter."""
        return await self.redis.incrby(key, amount)

    async def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement counter."""
        return await self.redis.decrby(key, amount)

    async def flush_all(self) -> None:
        """Flush all cache (for testing)."""
        await self.redis.flushdb()


class RateLimiter:
    """Redis-based rate limiter using sliding window."""

    def __init__(self, redis: redis.Redis, requests: int, period: int):
        """
        Initialize rate limiter.
        
        Args:
            redis: Redis client
            requests: Number of requests allowed
            period: Time period in seconds
        """
        self.redis = redis
        self.requests = requests
        self.period = period

    async def is_allowed(self, identifier: str) -> tuple[bool, dict]:
        """
        Check if request is allowed for identifier.
        
        Returns:
            Tuple of (allowed: bool, info: dict with rate limit info)
        """
        key = f"rate_limit:{identifier}"
        current = await self.redis.incr(key)

        if current == 1:
            # First request, set expiry
            await self.redis.expire(key, self.period)

        info = {
            "limit": self.requests,
            "current": current,
            "remaining": max(0, self.requests - current),
            "reset_in": await self.redis.ttl(key),
        }

        return current <= self.requests, info

    async def reset(self, identifier: str) -> None:
        """Reset rate limit for identifier."""
        key = f"rate_limit:{identifier}"
        await self.redis.delete(key)


class DistributedCounter:
    """Distributed counter for tracking clicks and aggregating analytics.
    
    Strategy:
    - Aggregate counts in Redis for real-time analytics
    - Periodically flush to database
    - Use Redis for up-to-the-second accuracy
    """

    def __init__(self, redis: redis.Redis):
        self.redis = redis

    async def increment_url_clicks(self, short_code: str, amount: int = 1) -> int:
        """Increment click counter for a short code."""
        key = f"clicks:{short_code}"
        return await self.redis.incrby(key, amount)

    async def get_click_count(self, short_code: str) -> int:
        """Get current click count."""
        key = f"clicks:{short_code}"
        result = await self.redis.get(key)
        return int(result) if result else 0

    async def increment_unique_visitor(self, short_code: str, ip_hash: str) -> bool:
        """Track unique visitor using HyperLogLog."""
        key = f"unique_visitors:{short_code}"
        return await self.redis.pfadd(key, ip_hash)

    async def get_unique_visitor_estimate(self, short_code: str) -> int:
        """Get estimated unique visitor count."""
        key = f"unique_visitors:{short_code}"
        return await self.redis.pfcount(key)

    async def track_referrer(self, short_code: str, referrer: str) -> None:
        """Track referrer with sorted set for TOP N queries."""
        key = f"referrers:{short_code}"
        return await self.redis.zincrby(key, 1, referrer)

    async def get_top_referrers(
        self, short_code: str, limit: int = 10
    ) -> list[tuple[str, int]]:
        """Get top referrers."""
        key = f"referrers:{short_code}"
        results = await self.redis.zrevrange(key, 0, limit - 1, withscores=True)
        return [(referrer, int(score)) for referrer, score in results]

    async def flush_counters(self, short_code: str) -> dict:
        """Flush all counters for a short code and return values.
        
        This is called periodically to persist Redis counters to database.
        """
        clicks_key = f"clicks:{short_code}"
        unique_key = f"unique_visitors:{short_code}"
        referrers_key = f"referrers:{short_code}"

        clicks = await self.get_click_count(short_code)
        unique = await self.get_unique_visitor_estimate(short_code)

        return {
            "clicks": clicks,
            "unique_visitors": unique,
        }
