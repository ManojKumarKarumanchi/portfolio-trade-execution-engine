"""Application configuration module."""
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    """Application configuration settings."""

    # Database settings
    DB_URL: str = os.getenv(
        "DB_URL",
        "postgresql+asyncpg://user:pass@localhost:5432/portfolio_db"
    )

    # Connection pool settings
    POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "1800"))  # 30 minutes

    # Application settings
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"


settings = Settings()
