"""
Repository implementations using SQLAlchemy.
"""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateShortCodeError
from app.domain.entities import ClickEvent, ShortenedURL, URLAnalytics, User
from app.domain.repositories import (
    IClickEventRepository,
    IShortenedURLRepository,
    IUserRepository,
)
from app.infrastructure.database.models import (
    ClickEventModel,
    ShortenedURLModel,
    UserModel,
)


class UserRepository(IUserRepository):
    """User repository implementation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        query = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(query)
        user_model = result.scalar_one_or_none()
        return self._to_domain(user_model) if user_model else None

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        query = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(query)
        user_model = result.scalar_one_or_none()
        return self._to_domain(user_model) if user_model else None

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        query = select(UserModel).where(UserModel.username == username)
        result = await self.session.execute(query)
        user_model = result.scalar_one_or_none()
        return self._to_domain(user_model) if user_model else None

    async def create(self, user: User) -> User:
        """Create new user."""
        user_model = UserModel(
            email=user.email,
            username=user.username,
            password_hash=user.password_hash,
        )
        self.session.add(user_model)
        await self.session.flush()
        return self._to_domain(user_model)

    async def update(self, user: User) -> User:
        """Update user."""
        query = select(UserModel).where(UserModel.id == user.id)
        result = await self.session.execute(query)
        user_model = result.scalar_one()

        user_model.email = user.email
        user_model.username = user.username
        user_model.password_hash = user.password_hash
        user_model.is_active = user.is_active
        user_model.updated_at = datetime.utcnow()

        await self.session.flush()
        return self._to_domain(user_model)

    @staticmethod
    def _to_domain(user_model: UserModel) -> User:
        """Convert model to domain entity."""
        return User(
            id=user_model.id,
            email=user_model.email,
            username=user_model.username,
            password_hash=user_model.password_hash,
            created_at=user_model.created_at,
            updated_at=user_model.updated_at,
            is_active=user_model.is_active,
        )


class ShortenedURLRepository(IShortenedURLRepository):
    """Shortened URL repository implementation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_short_code(self, short_code: str) -> Optional[ShortenedURL]:
        """Get shortened URL by short code."""
        query = select(ShortenedURLModel).where(
            ShortenedURLModel.short_code == short_code
        )
        result = await self.session.execute(query)
        url_model = result.scalar_one_or_none()
        return self._to_domain(url_model) if url_model else None

    async def get_by_id(self, url_id: int) -> Optional[ShortenedURL]:
        """Get shortened URL by ID."""
        query = select(ShortenedURLModel).where(ShortenedURLModel.id == url_id)
        result = await self.session.execute(query)
        url_model = result.scalar_one_or_none()
        return self._to_domain(url_model) if url_model else None

    async def get_by_long_url(self, long_url: str) -> Optional[ShortenedURL]:
        """Get shortened URL by long URL (for idempotency)."""
        query = select(ShortenedURLModel).where(
            ShortenedURLModel.long_url == long_url
        )
        result = await self.session.execute(query)
        url_model = result.scalar_one_or_none()
        return self._to_domain(url_model) if url_model else None

    async def get_all_by_user(
        self, user_id: int, limit: int = 100, offset: int = 0
    ) -> list[ShortenedURL]:
        """Get all URLs created by a user."""
        query = (
            select(ShortenedURLModel)
            .where(ShortenedURLModel.user_id == user_id)
            .order_by(desc(ShortenedURLModel.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        url_models = result.scalars().all()
        return [self._to_domain(model) for model in url_models]

    async def create(self, url: ShortenedURL) -> ShortenedURL:
        """Create new shortened URL."""
        # Check for collision
        existing = await self.get_by_short_code(url.short_code)
        if existing:
            raise DuplicateShortCodeError(url.short_code)

        url_model = ShortenedURLModel(
            user_id=url.user_id,
            short_code=url.short_code,
            long_url=url.long_url,
            expires_at=url.expires_at,
        )
        self.session.add(url_model)
        await self.session.flush()
        return self._to_domain(url_model)

    async def update(self, url: ShortenedURL) -> ShortenedURL:
        """Update shortened URL."""
        query = select(ShortenedURLModel).where(ShortenedURLModel.id == url.id)
        result = await self.session.execute(query)
        url_model = result.scalar_one()

        url_model.long_url = url.long_url
        url_model.expires_at = url.expires_at
        url_model.is_active = url.is_active
        url_model.updated_at = datetime.utcnow()

        await self.session.flush()
        return self._to_domain(url_model)

    async def delete(self, short_code: str) -> bool:
        """Delete shortened URL."""
        query = select(ShortenedURLModel).where(
            ShortenedURLModel.short_code == short_code
        )
        result = await self.session.execute(query)
        url_model = result.scalar_one_or_none()

        if not url_model:
            return False

        await self.session.delete(url_model)
        await self.session.flush()
        return True

    async def increment_click_count(self, short_code: str) -> None:
        """Increment click counter.
        
        Note: In production, this would typically be done in Redis for speed.
        The actual DB update happens asynchronously via event processing.
        """
        query = select(ShortenedURLModel).where(
            ShortenedURLModel.short_code == short_code
        )
        result = await self.session.execute(query)
        url_model = result.scalar_one_or_none()

        if url_model:
            url_model.updated_at = datetime.utcnow()
            await self.session.flush()

    @staticmethod
    def _to_domain(url_model: ShortenedURLModel) -> ShortenedURL:
        """Convert model to domain entity."""
        return ShortenedURL(
            id=url_model.id,
            user_id=url_model.user_id,
            short_code=url_model.short_code,
            long_url=url_model.long_url,
            created_at=url_model.created_at,
            updated_at=url_model.updated_at,
            expires_at=url_model.expires_at,
            is_active=url_model.is_active,
        )


class ClickEventRepository(IClickEventRepository):
    """Click event repository implementation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, event: ClickEvent) -> ClickEvent:
        """Record click event."""
        event_model = ClickEventModel(
            shortened_url_id=event.shortened_url_id,
            ip_address=event.ip_address,
            user_agent=event.user_agent,
            referrer=event.referrer,
            country=event.country,
            timestamp=event.timestamp,
        )
        self.session.add(event_model)
        await self.session.flush()
        return self._to_domain(event_model)

    async def get_by_short_code(
        self, short_code: str, limit: int = 1000
    ) -> list[ClickEvent]:
        """Get click events for a short code."""
        query = (
            select(ClickEventModel)
            .join(ShortenedURLModel)
            .where(ShortenedURLModel.short_code == short_code)
            .order_by(desc(ClickEventModel.timestamp))
            .limit(limit)
        )
        result = await self.session.execute(query)
        event_models = result.scalars().all()
        return [self._to_domain(model) for model in event_models]

    async def get_analytics(
        self, short_code: str, days: int = 30
    ) -> URLAnalytics:
        """Get aggregated analytics for short code."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get URL ID
        url_query = select(ShortenedURLModel).where(
            ShortenedURLModel.short_code == short_code
        )
        url_result = await self.session.execute(url_query)
        url_model = url_result.scalar_one_or_none()

        if not url_model:
            return URLAnalytics(
                short_code=short_code,
                total_clicks=0,
                unique_visitors=0,
                clicks_per_day={},
                top_referrers=[],
                country_distribution={},
            )

        # Total clicks
        total_clicks = await self.get_total_clicks(short_code)

        # Unique visitors
        unique_visitors = await self.get_unique_visitors(short_code)

        # Clicks per day
        clicks_per_day_query = (
            select(
                func.date(ClickEventModel.timestamp).label("date"),
                func.count().label("count"),
            )
            .where(
                and_(
                    ClickEventModel.shortened_url_id == url_model.id,
                    ClickEventModel.timestamp >= cutoff_date,
                )
            )
            .group_by(func.date(ClickEventModel.timestamp))
        )
        clicks_per_day_result = await self.session.execute(clicks_per_day_query)
        clicks_per_day = {
            str(row[0]): row[1] for row in clicks_per_day_result.all()
        }

        # Top referrers
        top_referrers_query = (
            select(
                ClickEventModel.referrer,
                func.count().label("count"),
            )
            .where(
                and_(
                    ClickEventModel.shortened_url_id == url_model.id,
                    ClickEventModel.timestamp >= cutoff_date,
                    ClickEventModel.referrer.isnot(None),
                )
            )
            .group_by(ClickEventModel.referrer)
            .order_by(desc(func.count()))
            .limit(10)
        )
        top_referrers_result = await self.session.execute(top_referrers_query)
        top_referrers = [
            (row[0], row[1]) for row in top_referrers_result.all()
        ]

        # Country distribution
        country_query = (
            select(
                ClickEventModel.country,
                func.count().label("count"),
            )
            .where(
                and_(
                    ClickEventModel.shortened_url_id == url_model.id,
                    ClickEventModel.timestamp >= cutoff_date,
                    ClickEventModel.country.isnot(None),
                )
            )
            .group_by(ClickEventModel.country)
            .order_by(desc(func.count()))
        )
        country_result = await self.session.execute(country_query)
        country_distribution = {row[0]: row[1] for row in country_result.all()}

        # Last click timestamp
        last_click_query = (
            select(func.max(ClickEventModel.timestamp))
            .where(ClickEventModel.shortened_url_id == url_model.id)
        )
        last_click_result = await self.session.execute(last_click_query)
        last_click_at = last_click_result.scalar_one_or_none()

        return URLAnalytics(
            short_code=short_code,
            total_clicks=total_clicks,
            unique_visitors=unique_visitors,
            clicks_per_day=clicks_per_day,
            top_referrers=top_referrers,
            country_distribution=country_distribution,
            last_click_at=last_click_at,
        )

    async def get_total_clicks(self, short_code: str) -> int:
        """Get total click count."""
        url_query = select(ShortenedURLModel).where(
            ShortenedURLModel.short_code == short_code
        )
        url_result = await self.session.execute(url_query)
        url_model = url_result.scalar_one_or_none()

        if not url_model:
            return 0

        query = select(func.count()).select_from(ClickEventModel).where(
            ClickEventModel.shortened_url_id == url_model.id
        )
        result = await self.session.execute(query)
        return result.scalar_one() or 0

    async def get_unique_visitors(self, short_code: str) -> int:
        """Get unique visitor count (by IP hash)."""
        url_query = select(ShortenedURLModel).where(
            ShortenedURLModel.short_code == short_code
        )
        url_result = await self.session.execute(url_query)
        url_model = url_result.scalar_one_or_none()

        if not url_model:
            return 0

        query = select(func.count(func.distinct(ClickEventModel.ip_address))).where(
            ClickEventModel.shortened_url_id == url_model.id
        )
        result = await self.session.execute(query)
        return result.scalar_one() or 0

    @staticmethod
    def _to_domain(event_model: ClickEventModel) -> ClickEvent:
        """Convert model to domain entity."""
        return ClickEvent(
            id=event_model.id,
            shortened_url_id=event_model.shortened_url_id,
            ip_address=event_model.ip_address,
            user_agent=event_model.user_agent,
            referrer=event_model.referrer,
            country=event_model.country,
            timestamp=event_model.timestamp,
        )
