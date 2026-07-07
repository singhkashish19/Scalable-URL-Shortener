"""
Redis cache implementation for distributed caching and rate limiting.

Architecture:
- Multi-tier TTL strategy: Different TTLs for different content types
- Graceful degradation: System works even if Redis fails
- Efficient key patterns: Namespaced keys for easy invalidation
- HyperLogLog for memory-efficient unique counts
- Sorted sets for leaderboards/top queries
"""

import json
import logging
from typing import Any, Optional
from enum import Enum

import redis.asyncio as redis

from app.core.config import get_settings
from app.infrastructure.constants import (
    CACHE_TTL_URL_MAPPING,
    CACHE_TTL_ANALYTICS,
    CACHE_TTL_CLICK_COUNTERS,
    CACHE_TTL_SESSION,
    RATE_LIMIT_DEFAULT_REQUESTS,
    RATE_LIMIT_DEFAULT_PERIOD,
    ANALYTICS_HLL_PRECISION,
    ANALYTICS_TOP_REFERRERS_LIMIT,
)

settings = get_settings()
logger = logging.getLogger(__name__)

# Connection pool for Redis
redis_client: Optional[redis.Redis] = None


class CacheTTL(Enum):
    """TTL presets for different cache types (in seconds).
    
    Values are centralized in app/infrastructure/constants.py
    for single source of truth.
    """
    
    # URL mappings: Cache for 24 hours (heavily accessed, stable)
    URL_MAPPING = CACHE_TTL_URL_MAPPING
    
    # Analytics: Cache for 1 hour (frequently accessed, can be stale)
    ANALYTICS = CACHE_TTL_ANALYTICS
    
    # Click counts: Cache for 5 minutes (real-time data, less critical)
    CLICK_COUNTERS = CACHE_TTL_CLICK_COUNTERS
    
    # Session data: Cache for 30 minutes
    SESSION = CACHE_TTL_SESSION


async def init_redis() -> redis.Redis:
    """Initialize Redis connection with connection pooling."""
    global redis_client
    try:
        redis_client = await redis.from_url(
            settings.REDIS_URL, 
            encoding="utf8", 
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True,
        )
        await redis_client.ping()
        logger.info("Redis connection established successfully")
        return redis_client
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        redis_client = None
        raise


async def close_redis() -> None:
    """Close Redis connection."""
    if redis_client:
        try:
            await redis_client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")


class CacheService:
    """
    Service for distributed caching with graceful degradation.
    
    Design:
    - Wraps all cache operations in try-except blocks
    - System continues even if cache unavailable
    - Log failures without disrupting core functionality
    """

    def __init__(self, redis: redis.Redis):
        self.redis = redis

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with error handling."""
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.warning(f"Cache GET failed for key {key}: {e}")
            return None

    async def set(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with error handling."""
        try:
            if ttl is None:
                ttl = settings.REDIS_CACHE_TTL

            serialized = (
                json.dumps(value) if not isinstance(value, str) else value
            )
            await self.redis.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.warning(f"Cache SET failed for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache with error handling."""
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache DELETE failed for key {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern (e.g., 'url:*')."""
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache DELETE_PATTERN failed for pattern {pattern}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return bool(await self.redis.exists(key))
        except Exception as e:
            logger.warning(f"Cache EXISTS check failed for key {key}: {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter with error handling."""
        try:
            return await self.redis.incrby(key, amount)
        except Exception as e:
            logger.warning(f"Cache INCREMENT failed for key {key}: {e}")
            return 0

    async def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement counter with error handling."""
        try:
            return await self.redis.decrby(key, amount)
        except Exception as e:
            logger.warning(f"Cache DECREMENT failed for key {key}: {e}")
            return 0

    async def ttl(self, key: str) -> int:
        """Get remaining TTL of a key in seconds."""
        try:
            return await self.redis.ttl(key)
        except Exception as e:
            logger.warning(f"Cache TTL check failed for key {key}: {e}")
            return -1

    async def flush_all(self) -> bool:
        """Flush all cache (for testing only)."""
        try:
            await self.redis.flushdb()
            return True
        except Exception as e:
            logger.error(f"Cache FLUSH_ALL failed: {e}")
            return False

    async def get_cache_info(self) -> dict:
        """Get Redis cache statistics."""
        try:
            info = await self.redis.info()
            return {
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands": info.get("total_commands_processed", 0),
            }
        except Exception as e:
            logger.warning(f"Failed to get cache info: {e}")
            return {}


class RateLimiter:
    """
    Redis-based rate limiter using sliding window algorithm.
    
    Algorithm:
    - Increment counter on each request
    - Set expiry on first request
    - Check if count exceeds limit
    
    Advantages:
    - Simple implementation
    - O(1) time complexity
    - Works well with Redis atomic operations
    
    Tradeoffs:
    - Not true sliding window (calendar-based, not request-based)
    - May allow burst at period boundaries
    """

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
        try:
            key = f"rate_limit:{identifier}"
            current = await self.redis.incr(key)

            if current == 1:
                # First request, set expiry
                await self.redis.expire(key, self.period)

            ttl = await self.redis.ttl(key)
            info = {
                "limit": self.requests,
                "current": current,
                "remaining": max(0, self.requests - current),
                "reset_in": ttl,
            }

            return current <= self.requests, info
        except Exception as e:
            logger.warning(f"Rate limiter check failed for {identifier}: {e}")
            # On error, allow request to proceed (fail-open for availability)
            return True, {
                "limit": self.requests,
                "current": 0,
                "remaining": self.requests,
                "reset_in": -1,
            }

    async def reset(self, identifier: str) -> bool:
        """Reset rate limit for identifier."""
        try:
            key = f"rate_limit:{identifier}"
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Failed to reset rate limit for {identifier}: {e}")
            return False


class DistributedCounter:
    """
    Distributed counter service for tracking clicks and real-time analytics.
    
    Strategy:
    - Redis serves as real-time analytics source (in-memory, fast)
    - Counters aggregated in Redis using efficient data structures
    - Periodic flush to database for durability
    
    Data Structures Used:
    - Strings: For total click counts
    - HyperLogLog: For unique visitor estimation (O(1) memory, constant size)
    - Sorted Sets: For top-N queries (referrers)
    
    TTL Strategy:
    - Counters kept indefinitely (until manually flushed)
    - Allows for real-time analytics queries
    """

    def __init__(self, redis: redis.Redis):
        self.redis = redis

    async def increment_url_clicks(self, short_code: str, amount: int = 1) -> int:
        """Increment click counter for a short code."""
        try:
            key = f"clicks:{short_code}"
            return await self.redis.incrby(key, amount)
        except Exception as e:
            logger.warning(f"Failed to increment click counter for {short_code}: {e}")
            return 0

    async def get_click_count(self, short_code: str) -> int:
        """Get current click count."""
        try:
            key = f"clicks:{short_code}"
            result = await self.redis.get(key)
            return int(result) if result else 0
        except Exception as e:
            logger.warning(f"Failed to get click count for {short_code}: {e}")
            return 0

    async def increment_unique_visitor(
        self, short_code: str, ip_hash: str
    ) -> bool:
        """
        Track unique visitor using HyperLogLog.
        
        HyperLogLog Benefits:
        - Constant O(1) space regardless of unique visitors
        - Trade accuracy for space (typically 2% error)
        - Perfect for approximate unique counts
        """
        try:
            key = f"unique_visitors:{short_code}"
            await self.redis.pfadd(key, ip_hash)
            return True
        except Exception as e:
            logger.warning(f"Failed to track visitor for {short_code}: {e}")
            return False

    async def get_unique_visitor_estimate(self, short_code: str) -> int:
        """Get estimated unique visitor count using HyperLogLog."""
        try:
            key = f"unique_visitors:{short_code}"
            return await self.redis.pfcount(key)
        except Exception as e:
            logger.warning(f"Failed to get unique visitor count for {short_code}: {e}")
            return 0

    async def track_referrer(self, short_code: str, referrer: str) -> bool:
        """Track referrer with sorted set for TOP N queries."""
        try:
            key = f"referrers:{short_code}"
            await self.redis.zincrby(key, 1, referrer)
            return True
        except Exception as e:
            logger.warning(f"Failed to track referrer for {short_code}: {e}")
            return False

    async def get_top_referrers(
        self, short_code: str, limit: int = 10
    ) -> list[tuple[str, int]]:
        """Get top referrers by count."""
        try:
            key = f"referrers:{short_code}"
            results = await self.redis.zrevrange(
                key, 0, limit - 1, withscores=True
            )
            return [(referrer, int(score)) for referrer, score in results]
        except Exception as e:
            logger.warning(f"Failed to get top referrers for {short_code}: {e}")
            return []

    async def flush_counters(self, short_code: str) -> dict:
        """
        Flush all counters for a short code and return values.
        
        This is called periodically to persist Redis counters to database
        and maintain a durable record of analytics.
        """
        try:
            clicks = await self.get_click_count(short_code)
            unique = await self.get_unique_visitor_estimate(short_code)

            return {
                "clicks": clicks,
                "unique_visitors": unique,
            }
        except Exception as e:
            logger.error(f"Failed to flush counters for {short_code}: {e}")
            return {}
