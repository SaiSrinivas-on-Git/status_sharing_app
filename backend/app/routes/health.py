"""Health check endpoint."""

from fastapi import APIRouter
from app.models.responses import HealthResponse
from app.utils.helpers import utc_now

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Cloud Run."""
    return HealthResponse(status="ok", timestamp=utc_now())
