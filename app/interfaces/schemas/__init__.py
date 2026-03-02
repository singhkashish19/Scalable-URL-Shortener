"""
Pydantic schemas for request/response validation and serialization.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl, validator


class ShortenRequestSchema(BaseModel):
    """Request schema for URL shortening."""

    long_url: str = Field(..., description="URL to shorten", min_length=10, max_length=2048)
    custom_alias: Optional[str] = Field(
        None, description="Custom short code", min_length=3, max_length=12
    )
    expiration_days: Optional[int] = Field(
        None, description="Days until expiration", ge=1, le=365
    )

    class Config:
        json_schema_extra = {
            "example": {
                "long_url": "https://example.com/very/long/url/path",
                "custom_alias": "mylink",
                "expiration_days": 30,
            }
        }


class ShortenResponseSchema(BaseModel):
    """Response schema for URL shortening."""

    short_code: str
    short_url: str
    long_url: str
    expires_at: Optional[str] = None
    created_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "short_code": "abc123",
                "short_url": "http://localhost:8000/abc123",
                "long_url": "https://example.com/very/long/url",
                "expires_at": "2025-03-28T12:00:00",
                "created_at": "2025-02-26T12:00:00",
            }
        }


class AnalyticsSchema(BaseModel):
    """Response schema for analytics."""

    short_code: str
    total_clicks: int
    unique_visitors: int
    clicks_per_day: dict[str, int]
    top_referrers: list[tuple[str, int]]
    country_distribution: dict[str, int]
    last_click_at: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "short_code": "abc123",
                "total_clicks": 1500,
                "unique_visitors": 892,
                "clicks_per_day": {
                    "2025-02-26": 250,
                    "2025-02-27": 310,
                },
                "top_referrers": [
                    ("https://twitter.com", 450),
                    ("https://reddit.com", 320),
                ],
                "country_distribution": {
                    "US": 600,
                    "GB": 200,
                    "CA": 150,
                },
                "last_click_at": "2025-02-27T23:59:00",
            }
        }


class ErrorResponseSchema(BaseModel):
    """Error response schema."""

    error_code: str
    message: str
    details: Optional[dict] = None
    status_code: int

    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "URL_NOT_FOUND",
                "message": "Short code 'abc123' not found",
                "status_code": 404,
            }
        }


class RateLimitInfoSchema(BaseModel):
    """Rate limit info in response headers."""

    limit: int
    remaining: int
    current: int
    reset_in: int


class UserRegisterSchema(BaseModel):
    """Request schema for user registration."""

    email: str = Field(..., min_length=5, max_length=255)
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)

    @validator("email")
    def validate_email(cls, v):
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "john_doe",
                "password": "SecurePassword123",
            }
        }


class UserLoginSchema(BaseModel):
    """Request schema for user login."""

    email: str
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePassword123",
            }
        }


class TokenResponseSchema(BaseModel):
    """Response schema for authentication."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
            }
        }


class URLListItemSchema(BaseModel):
    """Schema for a single URL in list response."""

    short_code: str
    short_url: str
    long_url: str
    created_at: str
    expires_at: Optional[str] = None
    click_count: int = 0


class URLListResponseSchema(BaseModel):
    """Response schema for listing URLs."""

    total: int
    limit: int
    offset: int
    items: list[URLListItemSchema]
