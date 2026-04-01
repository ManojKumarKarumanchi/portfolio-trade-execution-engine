"""Database session management for async SQLAlchemy."""
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from contextlib import asynccontextmanager
import time

from .engine import engine
from app.core.logger import logger

# Session factory - creates new sessions bound to the engine
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
    autoflush=False,  # Manual flush control for better performance
    autocommit=False,  # Explicit transaction control
)


@asynccontextmanager
async def get_db():
    """
    Async context manager for database sessions.

    Usage:
        async with get_db() as session:
            result = await session.execute(query)
            await session.commit()

    Features:
    - Automatic commit on success
    - Automatic rollback on exception
    - Session cleanup
    - Execution time tracking
    """
    session: AsyncSession = SessionLocal()
    start = time.time()

    try:
        yield session
        await session.commit()

    except Exception as e:
        await session.rollback()
        logger.error(f"Database error - rolling back transaction: {e}", exc_info=True)
        raise

    finally:
        await session.close()
        duration = time.time() - start
        logger.info(f"DB session completed in {duration:.4f}s")


async def get_db_dependency():
    """
    FastAPI dependency for injecting database sessions.

    Usage in FastAPI routes:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db_dependency)):
            result = await db.execute(query)
            return result
    """
    async with get_db() as session:
        yield session
