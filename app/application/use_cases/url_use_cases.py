"""
Use cases: Application logic orchestrating services and repositories.
"""

from datetime import datetime
from typing import Optional

from app.application.services.url_service import (
    AnalyticsService,
    URLShorteningService,
)
from app.core.config import get_settings
from app.core.exceptions import ForbiddenError, URLNotFoundError
from app.domain.repositories import IShortenedURLRepository

settings = get_settings()


class ShortenURLUseCase:
    """Use case: Shorten a new URL."""

    def __init__(self, url_service: URLShorteningService):
        self.url_service = url_service

    async def execute(
        self,
        long_url: str,
        custom_alias: Optional[str] = None,
        expiration_days: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> dict:
        """Execute shorten URL use case."""
        url = await self.url_service.shorten_url(
            long_url=long_url,
            short_code=custom_alias,
            expiration_days=expiration_days,
            user_id=user_id,
        )

        return {
            "short_code": url.short_code,
            "short_url": f"{settings.BASE_URL}/{url.short_code}",
            "long_url": url.long_url,
            "expires_at": url.expires_at.isoformat() if url.expires_at else None,
            "created_at": url.created_at.isoformat(),
        }


class ResolveURLUseCase:
    """Use case: Resolve short code to long URL."""

    def __init__(
        self,
        url_service: URLShorteningService,
        analytics_service: AnalyticsService,
    ):
        self.url_service = url_service
        self.analytics_service = analytics_service

    async def execute(
        self,
        short_code: str,
        ip_address: str,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None,
    ) -> str:
        """Execute resolve URL use case."""
        # Resolve URL
        long_url = await self.url_service.resolve_url(short_code)

        # Track click (async)
        await self.analytics_service.track_click(
            short_code=short_code,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
        )

        return long_url


class GetAnalyticsUseCase:
    """Use case: Get analytics for a shortened URL."""

    def __init__(
        self,
        analytics_service: AnalyticsService,
        url_repository: IShortenedURLRepository,
    ):
        self.analytics_service = analytics_service
        self.url_repository = url_repository

    async def execute(
        self, short_code: str, days: int = 30, user_id: Optional[int] = None
    ) -> dict:
        """Execute get analytics use case."""
        # Check if URL exists
        url = await self.url_repository.get_by_short_code(short_code)
        if not url:
            raise URLNotFoundError(short_code)

        # Check ownership if user_id provided
        if user_id and url.user_id != user_id:
            raise ForbiddenError("You don't have access to this URL's analytics")

        # Get analytics
        analytics = await self.analytics_service.get_analytics(
            short_code=short_code, days=days
        )

        return analytics
