"""Database retry logic using tenacity for SQLAlchemy operations."""
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
)
from sqlalchemy.exc import (
    OperationalError,
    DBAPIError,
    DisconnectionError,
)

from app.core.logger import logger


def db_retry():
    """Decorator for retrying database operations on transient errors.

    Retries on:
    - OperationalError: database connection failures, timeouts
    - DBAPIError: low-level database API errors
    - DisconnectionError: connection lost during operation
    """
    return retry(
        reraise=True,

        # Retry only on transient database errors
        retry=retry_if_exception_type((
            OperationalError,
            DBAPIError,
            DisconnectionError,
        )),

        # Stop after 5 attempts
        stop=stop_after_attempt(5),

        # Exponential backoff: 0.5s, 1s, 2s, 4s, 8s (capped at 10s)
        wait=wait_exponential(multiplier=0.5, min=1, max=10),

        # Logging hooks for observability
        before_sleep=before_sleep_log(logger, logger.level),
        after=after_log(logger, logger.level),
    )
