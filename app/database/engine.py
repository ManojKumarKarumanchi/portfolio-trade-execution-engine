"""Database engine module with async SQLAlchemy setup."""
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from app.core.logger import logger

# Create async engine with connection pooling
engine = create_async_engine(
    settings.DB_URL,

    # Connection pooling configuration
    pool_size=settings.POOL_SIZE,
    max_overflow=settings.MAX_OVERFLOW,
    pool_timeout=settings.POOL_TIMEOUT,
    pool_recycle=settings.POOL_RECYCLE,

    # Critical for production: validates connections before using them
    pool_pre_ping=True,

    # Set to True only in development for SQL debugging
    echo=settings.DEBUG,

    # Async settings
    future=True,
)


async def init_db():
    """Initialize database connection."""
    logger.info("Database engine initialized")
    logger.info(f"Pool size: {settings.POOL_SIZE}, Max overflow: {settings.MAX_OVERFLOW}")


async def close_db():
    """Dispose database engine and close all connections."""
    logger.info("Disposing database engine...")
    await engine.dispose()
    logger.info("Database engine disposed")
