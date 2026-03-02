"""
Domain entities - pure business logic, no dependencies on infrastructure.
These represent core concepts of the URL shortening domain.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """User entity."""

    id: int
    email: str
    username: str
    password_hash: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email}, username={self.username})"


@dataclass
class ShortenedURL:
    """Shortened URL entity."""

    id: int
    user_id: Optional[int]
    short_code: str
    long_url: str
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    click_count: int = 0

    def __repr__(self) -> str:
        return f"ShortenedURL(short_code={self.short_code}, long_url={self.long_url})"

    def is_expired(self) -> bool:
        """Check if URL has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


@dataclass
class ClickEvent:
    """Click event entity for analytics."""

    id: int
    shortened_url_id: int
    ip_address: str
    user_agent: str
    referrer: Optional[str]
    country: Optional[str]
    timestamp: datetime

    def __repr__(self) -> str:
        return (
            f"ClickEvent(url_id={self.shortened_url_id}, "
            f"ip={self.ip_address}, timestamp={self.timestamp})"
        )


@dataclass
class URLAnalytics:
    """Analytics aggregation for a shortened URL."""

    short_code: str
    total_clicks: int
    unique_visitors: int
    clicks_per_day: dict[str, int]
    top_referrers: list[tuple[str, int]]
    country_distribution: dict[str, int]
    last_click_at: Optional[datetime] = None

    def __repr__(self) -> str:
        return (
            f"URLAnalytics(code={self.short_code}, "
            f"clicks={self.total_clicks}, unique={self.unique_visitors})"
        )
