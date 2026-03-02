"""
Unit tests for exceptions.
"""

import pytest

from app.core.exceptions import (
    DuplicateShortCodeError,
    ForbiddenError,
    InvalidURLError,
    RateLimitExceededError,
    URLExpiredError,
    URLNotFoundError,
    UnauthorizedError,
)


class TestExceptions:
    """Test custom exceptions."""

    def test_url_not_found_error(self):
        """Test URLNotFoundError."""
        exc = URLNotFoundError("abc123")
        assert exc.status_code == 404
        assert exc.error_code == "URL_NOT_FOUND"
        assert "abc123" in exc.message

    def test_url_expired_error(self):
        """Test URLExpiredError."""
        exc = URLExpiredError("abc123")
        assert exc.status_code == 410
        assert exc.error_code == "URL_EXPIRED"

    def test_invalid_url_error(self):
        """Test InvalidURLError."""
        exc = InvalidURLError("bad_url", "Invalid format")
        assert exc.status_code == 400
        assert exc.error_code == "INVALID_URL"

    def test_duplicate_short_code_error(self):
        """Test DuplicateShortCodeError."""
        exc = DuplicateShortCodeError("abc123")
        assert exc.status_code == 409
        assert exc.error_code == "DUPLICATE_SHORT_CODE"

    def test_rate_limit_exceeded_error(self):
        """Test RateLimitExceededError."""
        exc = RateLimitExceededError("192.168.1.1", 100, 60)
        assert exc.status_code == 429
        assert exc.error_code == "RATE_LIMIT_EXCEEDED"

    def test_unauthorized_error(self):
        """Test UnauthorizedError."""
        exc = UnauthorizedError()
        assert exc.status_code == 401
        assert exc.error_code == "UNAUTHORIZED"

    def test_forbidden_error(self):
        """Test ForbiddenError."""
        exc = ForbiddenError()
        assert exc.status_code == 403
        assert exc.error_code == "FORBIDDEN"
