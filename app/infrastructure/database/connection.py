"""
Database connection and session management with production-grade pooling.

Features:
- Async SQLAlchemy 2.0 setup
- Optimized connection pooling (QueuePool)
- Connection health checks (pool_pre_ping)
- Automatic connection recycling
- Future-mode compatible
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from app.core.config import get_settings

settings = get_settings()

# Create async engine with production-grade pooling
# QueuePool: Thread-safe queue for connection management
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    poolclass=QueuePool,  # Use queue instead of default for better concurrency
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    pool_pre_ping=True,  # Validate connections (prevents "connection reset" errors)
    future=True,  # Enable SQLAlchemy 2.0 behavior
    connect_args={
        "timeout": 10,
        "command_timeout": 30,
    },
)

# Create session factory with optimal settings
async_session_factory = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Prevent lazy load after commit
    autoflush=False,  # Manual flush for better control
    autocommit=False,  # Explicit transaction management
    future=True,  # SQLAlchemy 2.0 API
)


async def get_db_session() -> AsyncSession:
    """Get database session for dependency injection."""
    async with async_session_factory() as session:
        yield session


async def init_db() -> None:
    """Initialize database (create tables)."""
    from app.infrastructure.database.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """Drop all tables (for testing)."""
    from app.infrastructure.database.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
