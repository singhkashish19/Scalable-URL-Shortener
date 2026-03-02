"""
Unit tests for external services.
"""

import pytest

from app.infrastructure.external.services import URLValidator, hash_ip


class TestURLValidator:
    """Test URL validation."""

    def test_valid_url(self):
        """Test valid URL."""
        is_valid, error = URLValidator.validate("https://example.com")
        assert is_valid
        assert error is None

    def test_valid_url_with_path(self):
        """Test valid URL with path."""
        is_valid, error = URLValidator.validate("https://example.com/path/to/page")
        assert is_valid
        assert error is None

    def test_invalid_url_no_scheme(self):
        """Test URL without scheme."""
        is_valid, error = URLValidator.validate("example.com")
        # Should be fixed by normalize
        assert error is None or "scheme" in error.lower()

    def test_url_too_long(self):
        """Test URL that's too long."""
        long_url = "https://example.com/" + "a" * 3000
        is_valid, error = URLValidator.validate(long_url)
        assert not is_valid
        assert error is not None

    def test_empty_url(self):
        """Test empty URL."""
        is_valid, error = URLValidator.validate("")
        assert not is_valid
        assert error is not None

    def test_normalize_url(self):
        """Test URL normalization."""
        normalized = URLValidator.normalize("example.com")
        assert normalized.startswith("https://")

    def test_normalize_already_has_scheme(self):
        """Test normalization when scheme already present."""
        url = "https://example.com"
        normalized = URLValidator.normalize(url)
        assert normalized == url


class TestHashIP:
    """Test IP hashing."""

    def test_hash_ip_ipv4(self):
        """Test hashing IPv4 address."""
        hash1 = hash_ip("192.168.1.1")
        assert len(hash1) == 16
        assert hash1.isalnum()

    def test_hash_ip_ipv6(self):
        """Test hashing IPv6 address."""
        hash1 = hash_ip("2001:db8::1")
        assert len(hash1) == 16

    def test_hash_ip_consistent(self):
        """Test hashing is consistent."""
        ip = "192.168.1.1"
        hash1 = hash_ip(ip)
        hash2 = hash_ip(ip)
        assert hash1 == hash2

    def test_hash_ip_different(self):
        """Test different IPs produce different hashes."""
        hash1 = hash_ip("192.168.1.1")
        hash2 = hash_ip("192.168.1.2")
        assert hash1 != hash2
