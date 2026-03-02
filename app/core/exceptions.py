"""
Custom exception classes for the application.
Centralized exception handling across all layers.
"""

from typing import Optional


class AppException(Exception):
    """Base exception for the application."""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[dict] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class URLNotFoundError(AppException):
    """Raised when a shortened URL is not found."""

    def __init__(self, short_code: str):
        super().__init__(
            message=f"Short code '{short_code}' not found",
            error_code="URL_NOT_FOUND",
            status_code=404,
            details={"short_code": short_code},
        )


class URLExpiredError(AppException):
    """Raised when a shortened URL has expired."""

    def __init__(self, short_code: str):
        super().__init__(
            message=f"Short code '{short_code}' has expired",
            error_code="URL_EXPIRED",
            status_code=410,
            details={"short_code": short_code},
        )


class InvalidURLError(AppException):
    """Raised when URL validation fails."""

    def __init__(self, url: str, reason: str):
        super().__init__(
            message=f"Invalid URL: {reason}",
            error_code="INVALID_URL",
            status_code=400,
            details={"url": url, "reason": reason},
        )


class DuplicateShortCodeError(AppException):
    """Raised when attempting to create duplicate short code."""

    def __init__(self, short_code: str):
        super().__init__(
            message=f"Short code '{short_code}' already exists",
            error_code="DUPLICATE_SHORT_CODE",
            status_code=409,
            details={"short_code": short_code},
        )


class RateLimitExceededError(AppException):
    """Raised when rate limit is exceeded."""

    def __init__(self, ip_address: str, limit: int, period: int):
        super().__init__(
            message=f"Rate limit exceeded: {limit} requests per {period} seconds",
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"ip_address": ip_address, "limit": limit, "period": period},
        )


class UserNotFoundError(AppException):
    """Raised when user is not found."""

    def __init__(self, user_id: int):
        super().__init__(
            message=f"User {user_id} not found",
            error_code="USER_NOT_FOUND",
            status_code=404,
            details={"user_id": user_id},
        )


class UnauthorizedError(AppException):
    """Raised when authentication fails."""

    def __init__(self, reason: str = "Unauthorized"):
        super().__init__(
            message=reason,
            error_code="UNAUTHORIZED",
            status_code=401,
        )


class ForbiddenError(AppException):
    """Raised when user doesn't have permission."""

    def __init__(self, reason: str = "Forbidden"):
        super().__init__(
            message=reason,
            error_code="FORBIDDEN",
            status_code=403,
        )
