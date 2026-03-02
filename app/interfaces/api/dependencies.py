"""
Dependency injection container.
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.short_code_service import ShortCodeGenerator
from app.application.services.url_service import (
    AnalyticsService,
    URLShorteningService,
)
from app.application.use_cases.url_use_cases import (
    GetAnalyticsUseCase,
    ResolveURLUseCase,
    ShortenURLUseCase,
)
from app.infrastructure.cache.redis import (
    CacheService,
    DistributedCounter,
    RateLimiter,
    redis_client,
)
from app.infrastructure.database.connection import async_session_factory
from app.infrastructure.database.repositories import (
    ClickEventRepository,
    ShortenedURLRepository,
    UserRepository,
)
from app.infrastructure.external.services import GeoIPService, URLValidator
from app.core.config import get_settings

settings = get_settings()


async def get_url_repository() -> ShortenedURLRepository:
    """Get URL repository."""
    async with async_session_factory() as session:
        return ShortenedURLRepository(session)


async def get_click_event_repository() -> ClickEventRepository:
    """Get click event repository."""
    async with async_session_factory() as session:
        return ClickEventRepository(session)


async def get_user_repository() -> UserRepository:
    """Get user repository."""
    async with async_session_factory() as session:
        return UserRepository(session)


async def get_cache_service() -> Optional[CacheService]:
    """Get cache service."""
    if redis_client is None:
        return None
    return CacheService(redis_client)


async def get_distributed_counter() -> Optional[DistributedCounter]:
    """Get distributed counter."""
    if redis_client is None:
        return None
    return DistributedCounter(redis_client)


async def get_rate_limiter() -> Optional[RateLimiter]:
    """Get rate limiter."""
    if redis_client is None:
        return None
    return RateLimiter(
        redis_client,
        settings.RATE_LIMIT_REQUESTS,
        settings.RATE_LIMIT_PERIOD,
    )


async def get_geoip_service() -> GeoIPService:
    """Get GeoIP service."""
    return GeoIPService()


async def get_url_shortening_service() -> URLShorteningService:
    """Get URL shortening service."""
    url_repository = await get_url_repository()
    cache_service = await get_cache_service()
    counter = await get_distributed_counter()
    return URLShorteningService(url_repository, cache_service, counter)


async def get_analytics_service() -> AnalyticsService:
    """Get analytics service."""
    event_repository = await get_click_event_repository()
    cache_service = await get_cache_service()
    counter = await get_distributed_counter()
    geoip_service = await get_geoip_service()
    return AnalyticsService(event_repository, cache_service, counter, geoip_service)


async def get_shorten_url_use_case() -> ShortenURLUseCase:
    """Get shorten URL use case."""
    url_service = await get_url_shortening_service()
    return ShortenURLUseCase(url_service)


async def get_resolve_url_use_case() -> ResolveURLUseCase:
    """Get resolve URL use case."""
    url_service = await get_url_shortening_service()
    analytics_service = await get_analytics_service()
    return ResolveURLUseCase(url_service, analytics_service)


async def get_get_analytics_use_case() -> GetAnalyticsUseCase:
    """Get analytics use case."""
    analytics_service = await get_analytics_service()
    url_repository = await get_url_repository()
    return GetAnalyticsUseCase(analytics_service, url_repository)
