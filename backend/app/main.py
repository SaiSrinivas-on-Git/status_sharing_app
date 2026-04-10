"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

from app.config import get_settings
from app.logging_config import setup_logging
from app.dependencies import init_firebase
from app.middleware.cors import setup_cors
from app.routes import health, viewer, status, device, owner


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — initialize Firebase on startup."""
    settings = get_settings()
    setup_logging(debug=settings.debug)
    logger = logging.getLogger(__name__)

    logger.info("Starting Status Sharing Backend...")
    init_firebase()
    logger.info("Firebase Admin SDK initialized")

    yield

    logger.info("Shutting down Status Sharing Backend...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Status Sharing System",
        description="Privacy-safe, real-time status sharing backend",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Middleware
    setup_cors(app)

    # Routes
    app.include_router(health.router)
    app.include_router(viewer.router)
    app.include_router(status.router)
    app.include_router(device.router)
    app.include_router(owner.router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
