"""Health check routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db_dependency
from app.database.retry import db_retry
from app.core.logger import logger

router = APIRouter(tags=["health"])


@router.get("/health")
@db_retry()
async def health_check(db: AsyncSession = Depends(get_db_dependency)):
    """
    Health check endpoint.

    Verifies:
    - API is running
    - Database connection is healthy

    Returns:
        Health status with database connectivity

    Example:
        GET /health
    """
    try:
        # Test database connection
        await db.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
            "service": "portfolio-trade-execution-engine"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


@router.get("/brokers")
async def list_supported_brokers():
    """
    List supported brokers.

    Returns:
        List of broker names supported by this system

    Example:
        GET /brokers
    """
    from app.brokers import BrokerFactory

    return {
        "supported_brokers": BrokerFactory.supported_brokers(),
        "count": len(BrokerFactory.supported_brokers())
    }
