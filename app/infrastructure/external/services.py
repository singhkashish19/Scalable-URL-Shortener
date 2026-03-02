"""
External services: GeoIP, URL validation, etc.
"""

import hashlib
import re
from typing import Optional

import geoip2.database
import geoip2.errors
from urllib.parse import urlparse


class URLValidator:
    """URL validation and normalization."""

    # Basic URL regex
    URL_PATTERN = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # or IP
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    BLOCKED_DOMAINS = {"bit.ly", "tinyurl.com", "goo.gl"}  # prevent recursion

    @classmethod
    def validate(cls, url: str) -> tuple[bool, Optional[str]]:
        """
        Validate URL format.
        
        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        if not url:
            return False, "URL cannot be empty"

        if len(url) > 2048:
            return False, "URL is too long (max 2048 characters)"

        if not cls.URL_PATTERN.match(url):
            return False, "Invalid URL format"

        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False, "URL must include scheme and domain"

            # Check for blocked domains
            domain = parsed.netloc.lower()
            if any(domain.endswith(blocked) for blocked in cls.BLOCKED_DOMAINS):
                return False, "URL shortener URLs are not allowed"

            return True, None
        except Exception as e:
            return False, f"URL parsing error: {str(e)}"

    @classmethod
    def normalize(cls, url: str) -> str:
        """Normalize URL (add scheme if missing)."""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        return url


class GeoIPService:
    """GeoIP lookup service for analytics."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize GeoIP service.
        
        Note: In production, use MaxMind GeoIP2 database.
        For demo purposes, we use a placeholder implementation.
        """
        self.db_path = db_path
        self.reader = None

        if db_path:
            try:
                self.reader = geoip2.database.Reader(db_path)
            except Exception:
                pass

    def get_country(self, ip_address: str) -> Optional[str]:
        """Get country code from IP address."""
        if not self.reader:
            return None

        try:
            response = self.reader.country(ip_address)
            return response.country.iso_code
        except geoip2.errors.AddressNotFoundError:
            return None
        except Exception:
            return None

    def close(self) -> None:
        """Close database connection."""
        if self.reader:
            self.reader.close()


def hash_ip(ip_address: str) -> str:
    """Hash IP address for privacy in logs."""
    return hashlib.sha256(ip_address.encode()).hexdigest()[:16]
