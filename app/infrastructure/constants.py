"""
Application-wide constants and configuration values.

This module centralizes all magic numbers and constants to enable:
- Single source of truth for all values
- Easy modification without searching codebase
- Clear documentation of each constant's purpose
"""

# ============================================================================
# HTTP & API
# ============================================================================

# Maximum attempts to generate unique short code before failing
MAX_SHORT_CODE_COLLISION_RETRIES = 5

# URL length validation
MAX_URL_LENGTH = 2048
MIN_URL_LENGTH = 10


# ============================================================================
# RATE LIMITING
# ============================================================================

# Default rate limit: 100 requests per 60 seconds
RATE_LIMIT_DEFAULT_REQUESTS = 100
RATE_LIMIT_DEFAULT_PERIOD = 60  # seconds

# Rate limit for specific operations
RATE_LIMIT_CREATE_URL_REQUESTS = 50
RATE_LIMIT_CREATE_URL_PERIOD = 300  # 5 minutes


# ============================================================================
# SHORT CODE GENERATION
# ============================================================================

# Snowflake ID generation
SNOWFLAKE_MACHINE_ID = 1  # This server's machine ID (0-1023)
SNOWFLAKE_EPOCH = 1609459200000  # 2021-01-01 in UTC milliseconds

# Short code length (encoded Base62)
SHORT_CODE_MIN_LENGTH = 6  # e.g., "aBc123"
SHORT_CODE_MAX_LENGTH = 12  # e.g., "pVn2jJwd6m"


# ============================================================================
# DATABASE
# ============================================================================

# Connection pool settings
DB_CONNECTION_POOL_SIZE = 20
DB_CONNECTION_MAX_OVERFLOW = 10
DB_CONNECTION_TIMEOUT = 30  # seconds

# Query timeout
DB_QUERY_TIMEOUT = 30  # seconds


# ============================================================================
# CACHE: REDIS
# ============================================================================

# Cache TTL values (in seconds)
# These define how long data is cached before expiration

# URL mappings: long URL -> short URL mapping
# Usually doesn't change, safe to cache for 24 hours
CACHE_TTL_URL_MAPPING = 86400  # 24 hours

# Analytics data: click counts, user data
# Can be slightly stale, refresh every hour
CACHE_TTL_ANALYTICS = 3600  # 1 hour

# Click counters: real-time counter increments
# Should be semi-real-time, refresh every 5 minutes
CACHE_TTL_CLICK_COUNTERS = 300  # 5 minutes

# Session data: authentication, temporary data
# Must be relatively fresh
CACHE_TTL_SESSION = 1800  # 30 minutes

# Cache key patterns (used for Redis key generation)
CACHE_KEY_URL_PATTERN = "url:{short_code}"
CACHE_KEY_CLICKS_PATTERN = "clicks:{short_code}"
CACHE_KEY_UNIQUE_VISITORS_PATTERN = "unique_visitors:{short_code}"
CACHE_KEY_REFERRERS_PATTERN = "referrers:{short_code}"


# ============================================================================
# ANALYTICS
# ============================================================================

# Time window for tracking unique visitors (in seconds)
ANALYTICS_UNIQUE_VISITOR_TTL = 604800  # 7 days

# HyperLogLog cardinality error tolerance
# Higher precision = more memory usage
ANALYTICS_HLL_PRECISION = 14

# Maximum number of top referrers to track
ANALYTICS_TOP_REFERRERS_LIMIT = 10

# Maximum number of recent clicks to store
ANALYTICS_RECENT_CLICKS_LIMIT = 100


# ============================================================================
# LOGGING
# ============================================================================

# Log levels
LOG_LEVEL_PRODUCTION = "INFO"
LOG_LEVEL_DEVELOPMENT = "DEBUG"

# Sensitive fields to mask in logs (don't log full values)
LOGGING_MASKED_FIELDS = [
    "password",
    "token",
    "secret",
    "api_key",
    "auth",
]


# ============================================================================
# ERROR HANDLING
# ============================================================================

# Circuit breaker settings (for cascading failure prevention)
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5  # Fail after N consecutive failures
CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60  # Try recovery after N seconds


# ============================================================================
# SECURITY
# ============================================================================

# CORS settings
CORS_ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:8000"]

# Password requirements
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_NUMBERS = True
PASSWORD_REQUIRE_SPECIAL = True


# ============================================================================
# PERFORMANCE
# ============================================================================

# Request/response timeout
REQUEST_TIMEOUT = 30  # seconds

# Background task timing
BACKGROUND_TASK_BATCH_SIZE = 100
BACKGROUND_TASK_DELAY = 5  # seconds


# ============================================================================
# TESTING
# ============================================================================

# Test database (use in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Test Redis (use fake Redis for tests)
TEST_REDIS_URL = "redis://localhost:6379/1"


# ============================================================================
# CONSTANTS FOR DOCUMENTATION ONLY
# ============================================================================

# Snowflake ID structure (64-bit):
#   [41-bit timestamp] [10-bit machine ID] [12-bit sequence]
#
# - Timestamp: Milliseconds since epoch, supports ~139 years
# - Machine ID: Supports 1024 different machines/datacenters
# - Sequence: Supports 4096 IDs per millisecond per machine
#
# Result: Globally unique, time-ordered, compact IDs
#
# Example: 697332671369449472 (decimal) → "pVn2jJwd6m" (Base62)

# Base62 alphabet (used for encoding IDs into short codes):
# Numbers: 0-9 (10 chars)
# Uppercase: A-Z (26 chars)
# Lowercase: a-z (26 chars)
# Total: 62 unique characters
#
# Why Base62?
# - URL-safe (no special characters)
# - Case-sensitive (adds security by making guessing harder)
# - Compact (2^64 base62 = ~86 quadrillion combinations)

