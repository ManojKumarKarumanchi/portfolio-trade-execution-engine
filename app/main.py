"""Main FastAPI application."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logger import logger
from app.database import init_db, close_db
from app.routes import execution_router, health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    This replaces the deprecated @app.on_event decorators.
    """
    # Startup
    logger.info("Starting Portfolio Trade Execution Engine...")
    await init_db()
    logger.info("Application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Portfolio Trade Execution Engine...")
    await close_db()
    logger.info("Application shutdown complete")


# Create FastAPI application with lifespan
app = FastAPI(
    title="Portfolio Trade Execution Engine",
    description="Production-grade trade execution system for systematic quant investing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware (configure as needed for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router)
app.include_router(execution_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Portfolio Trade Execution Engine",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
