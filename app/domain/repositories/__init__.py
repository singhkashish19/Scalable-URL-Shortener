"""
Repository interfaces (contracts) for data access.
Implementations are in infrastructure layer.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from app.domain.entities import ClickEvent, ShortenedURL, URLAnalytics, User


class IUserRepository(ABC):
    """Repository interface for user operations."""

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        pass

    @abstractmethod
    async def create(self, user: User) -> User:
        """Create new user."""
        pass

    @abstractmethod
    async def update(self, user: User) -> User:
        """Update user."""
        pass


class IShortenedURLRepository(ABC):
    """Repository interface for shortened URL operations."""

    @abstractmethod
    async def get_by_short_code(self, short_code: str) -> Optional[ShortenedURL]:
        """Get shortened URL by short code."""
        pass

    @abstractmethod
    async def get_by_id(self, url_id: int) -> Optional[ShortenedURL]:
        """Get shortened URL by ID."""
        pass

    @abstractmethod
    async def get_by_long_url(self, long_url: str) -> Optional[ShortenedURL]:
        """Get shortened URL by long URL (for idempotency)."""
        pass

    @abstractmethod
    async def get_all_by_user(self, user_id: int, limit: int = 100, offset: int = 0) -> list[ShortenedURL]:
        """Get all URLs created by a user."""
        pass

    @abstractmethod
    async def create(self, url: ShortenedURL) -> ShortenedURL:
        """Create new shortened URL."""
        pass

    @abstractmethod
    async def update(self, url: ShortenedURL) -> ShortenedURL:
        """Update shortened URL."""
        pass

    @abstractmethod
    async def delete(self, short_code: str) -> bool:
        """Delete shortened URL."""
        pass

    @abstractmethod
    async def increment_click_count(self, short_code: str) -> None:
        """Increment click counter (fast operation)."""
        pass


class IClickEventRepository(ABC):
    """Repository interface for click event operations."""

    @abstractmethod
    async def create(self, event: ClickEvent) -> ClickEvent:
        """Record click event."""
        pass

    @abstractmethod
    async def get_by_short_code(self, short_code: str, limit: int = 1000) -> list[ClickEvent]:
        """Get click events for a short code."""
        pass

    @abstractmethod
    async def get_analytics(self, short_code: str, days: int = 30) -> URLAnalytics:
        """Get aggregated analytics for short code."""
        pass

    @abstractmethod
    async def get_total_clicks(self, short_code: str) -> int:
        """Get total click count."""
        pass

    @abstractmethod
    async def get_unique_visitors(self, short_code: str) -> int:
        """Get unique visitor count (by IP hash)."""
        pass
