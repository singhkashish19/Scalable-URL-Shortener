"""
SQLAlchemy ORM models for database schema.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for ORM models."""

    pass


class UserModel(Base):
    """User database model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    urls: Mapped[list["ShortenedURLModel"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_username", "username"),
    )


class ShortenedURLModel(Base):
    """Shortened URL database model."""

    __tablename__ = "urls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    short_code: Mapped[str] = mapped_column(String(12), unique=True, nullable=False)
    long_url: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user: Mapped["UserModel"] = relationship(back_populates="urls")
    click_events: Mapped[list["ClickEventModel"]] = relationship(
        back_populates="url", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_urls_short_code", "short_code"),
        Index("idx_urls_user_id", "user_id"),
        Index("idx_urls_created_at", "created_at"),
        Index("idx_urls_expires_at", "expires_at"),
        Index("idx_urls_long_url", "long_url"),
    )


class ClickEventModel(Base):
    """Click event database model (append-only).
    
    Design notes:
    - Append-only table for immutability and performance
    - Heavily indexed for analytics queries
    - Partitioning strategy: partition by DATE(timestamp) for large scale
    - TTL: Events older than retention period can be archived to cold storage
    """

    __tablename__ = "click_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shortened_url_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("urls.id", ondelete="CASCADE"), nullable=False
    )
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)  # IPv6 support
    user_agent: Mapped[str] = mapped_column(String(500), nullable=True)
    referrer: Mapped[str] = mapped_column(String(500), nullable=True)
    country: Mapped[str] = mapped_column(String(2), nullable=True)  # ISO country code
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    url: Mapped["ShortenedURLModel"] = relationship(back_populates="click_events")

    __table_args__ = (
        Index("idx_click_events_shortened_url_id", "shortened_url_id"),
        Index("idx_click_events_timestamp", "timestamp"),
        Index("idx_click_events_ip_address", "ip_address"),
        Index("idx_click_events_url_timestamp", "shortened_url_id", "timestamp"),
        # Composite index for common analytics queries
        Index(
            "idx_click_events_url_ts_country",
            "shortened_url_id",
            "timestamp",
            "country",
        ),
    )
