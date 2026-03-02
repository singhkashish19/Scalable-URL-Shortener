"""
Application services for core business logic.
"""

from datetime import datetime, timedelta
from typing import Optional

from app.core.exceptions import (
    URLExpiredError,
    URLNotFoundError,
    InvalidURLError,
)
from app.domain.entities import ClickEvent, ShortenedURL
from app.domain.repositories import (
    IClickEventRepository,
    IShortenedURLRepository,
)
from app.infrastructure.cache.redis import CacheService, DistributedCounter
from app.infrastructure.external.services import GeoIPService, URLValidator
from app.core.config import get_settings

settings = get_settings()


class URLShorteningService:
    """Service for URL shortening operations."""

    def __init__(
        self,
        url_repository: IShortenedURLRepository,
        cache_service: CacheService,
        counter: DistributedCounter,
    ):
        self.url_repository = url_repository
        self.cache_service = cache_service
        self.counter = counter

    async def shorten_url(
        self,
        long_url: str,
        short_code: Optional[str] = None,
        expiration_days: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> ShortenedURL:
        """
        Shorten a URL.
        
        Features:
        - URL validation
        - Idempotency (return existing if same URL)
        - Custom short code support
        - Expiration support
        """
        # Validate URL
        is_valid, error_msg = URLValidator.validate(long_url)
        if not is_valid:
            raise InvalidURLError(long_url, error_msg)

        long_url = URLValidator.normalize(long_url)

        # Check for idempotency
        existing = await self.url_repository.get_by_long_url(long_url)
        if existing and not existing.is_expired():
            return existing

        # Create new shortened URL
        expires_at = None
        if expiration_days:
            expires_at = datetime.utcnow() + timedelta(days=expiration_days)
        elif settings.DEFAULT_EXPIRATION_DAYS:
            expires_at = datetime.utcnow() + timedelta(
                days=settings.DEFAULT_EXPIRATION_DAYS
            )

        url = ShortenedURL(
            id=0,  # Will be set by DB
            user_id=user_id,
            short_code=short_code or "",  # Will be generated
            long_url=long_url,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            expires_at=expires_at,
        )

        # Create in repository (will generate short code if needed)
        url = await self.url_repository.create(url)

        # Cache the mapping (if cache available)
        if self.cache_service:
            cache_key = f"url:{url.short_code}"
            try:
                await self.cache_service.set(cache_key, url.long_url)
            except Exception:
                pass  # Cache failure is not critical

        return url

    async def resolve_url(self, short_code: str) -> str:
        """
        Resolve short code to long URL.
        
        Strategy:
        1. Check cache first (Redis)
        2. If miss, check database
        3. Populate cache
        4. Return URL
        """
        # Try cache (if available)
        if self.cache_service:
            cache_key = f"url:{short_code}"
            try:
                cached_url = await self.cache_service.get(cache_key)
                if cached_url:
                    return cached_url
            except Exception:
                pass  # Cache miss, proceed to database

        # Fetch from DB
        url = await self.url_repository.get_by_short_code(short_code)
        if not url:
            raise URLNotFoundError(short_code)

        # Check expiration
        if url.is_expired():
            raise URLExpiredError(short_code)

        # Populate cache (if available)
        if self.cache_service:
            cache_key = f"url:{short_code}"
            try:
                await self.cache_service.set(cache_key, url.long_url)
            except Exception:
                pass  # Cache failure is not critical

        return url.long_url


class AnalyticsService:
    """Service for click tracking and analytics."""

    def __init__(
        self,
        event_repository: IClickEventRepository,
        cache_service: CacheService,
        counter: DistributedCounter,
        geoip_service: Optional[GeoIPService] = None,
    ):
        self.event_repository = event_repository
        self.cache_service = cache_service
        self.counter = counter
        self.geoip_service = geoip_service

    async def track_click(
        self,
        short_code: str,
        ip_address: str,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None,
    ) -> None:
        """
        Track a click event asynchronously.
        
        Strategy:
        1. Increment Redis counters (fast)
        2. Record event in database (async background job)
        """
        # Get country from IP
        country = None
        if self.geoip_service:
            try:
                country = self.geoip_service.get_country(ip_address)
            except Exception:
                pass  # GeoIP lookup failure is not critical

        # Create click event
        event = ClickEvent(
            id=0,
            shortened_url_id=0,  # Will be fetched
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            country=country,
            timestamp=datetime.utcnow(),
        )

        # Increment counters in Redis (if available)
        if self.counter:
            try:
                # Get URL ID
                url = await self.counter.redis.get(f"url:id:{short_code}")
                if url:
                    event.shortened_url_id = int(url)

                # Increment counters in Redis (for real-time analytics)
                await self.counter.increment_url_clicks(short_code)

                # Track unique visitor
                from app.infrastructure.external.services import hash_ip
                ip_hash = hash_ip(ip_address)
                await self.counter.increment_unique_visitor(short_code, ip_hash)

                # Track referrer
                if referrer:
                    await self.counter.track_referrer(short_code, referrer)
            except Exception:
                pass  # Counter failure is not critical

        # Store event in DB (this should be async/background)
        try:
            await self.event_repository.create(event)
        except Exception:
            pass  # Event storage failure is not critical

    async def get_analytics(self, short_code: str, days: int = 30) -> dict:
        """Get analytics for a shortened URL."""
        analytics = await self.event_repository.get_analytics(
            short_code, days=days
        )

        return {
            "short_code": analytics.short_code,
            "total_clicks": analytics.total_clicks,
            "unique_visitors": analytics.unique_visitors,
            "clicks_per_day": analytics.clicks_per_day,
            "top_referrers": analytics.top_referrers,
            "country_distribution": analytics.country_distribution,
            "last_click_at": analytics.last_click_at.isoformat()
            if analytics.last_click_at
            else None,
        }
