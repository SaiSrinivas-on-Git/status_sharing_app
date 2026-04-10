"""Status routes — polling endpoint for viewers."""

from fastapi import APIRouter, Depends, Query
from google.cloud.firestore_v1 import Client as FirestoreClient
import logging

from app.dependencies import require_whitelisted, get_firestore_client
from app.config import get_settings
from app.services.firestore_repo import FirestoreRepository
from app.models.responses import StatusResponse
from app.utils.helpers import time_ago

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/status", tags=["Status"])


@router.get("/latest", response_model=StatusResponse)
async def get_latest_status(
    request_id: str = Query(None, description="Request ID from viewer/open"),
    decoded_token: dict = Depends(require_whitelisted),
    db: FirestoreClient = Depends(get_firestore_client),
):
    """
    Get the latest status for the owner.

    If request_id is provided:
      - Check if refresh request is completed → return fresh status
      - If still pending → return { request_status: "pending" }

    If no request_id (or stale):
      - Return cached latest_status with is_cached=True
    """
    settings = get_settings()
    repo = FirestoreRepository(db)
    owner_id = settings.owner_uid

    # Check sharing enabled
    owner_settings = repo.get_owner_settings(owner_id)
    if not owner_settings.get("sharing_enabled", True):
        return StatusResponse(
            request_status="disabled",
            sharing_enabled=False,
        )

    # Check refresh request status
    if request_id:
        refresh_req = repo.get_refresh_request(request_id)
        if refresh_req and refresh_req.get("status") == "pending":
            return StatusResponse(request_status="pending")

    # Get latest status
    status_data = repo.get_latest_status(owner_id)
    if not status_data:
        return StatusResponse(
            request_status="no_data",
            sound_status="No status available yet",
            movement_status="Device hasn't reported",
            network_status="Unknown",
            outdoor_status="Unknown",
            is_cached=True,
        )

    # Determine if this is a fresh response or cached
    is_cached = True
    request_status = "cached"
    if request_id:
        refresh_req = repo.get_refresh_request(request_id)
        if refresh_req and refresh_req.get("status") == "completed":
            is_cached = False
            request_status = "completed"

    # Build response
    timestamp = status_data.get("timestamp")
    return StatusResponse(
        request_status=request_status,
        sound_status=status_data.get("sound_status", "Unknown"),
        movement_status=status_data.get("movement_status", "Unknown"),
        network_status=status_data.get("network_status", "Unknown"),
        outdoor_status=status_data.get("outdoor_status", "Unknown"),
        contact_suggestion=status_data.get("contact_suggestion"),
        contact_methods=status_data.get("contact_methods", []),
        device_battery=status_data.get("device_battery"),
        summary=status_data.get("summary"),
        last_updated=timestamp,
        last_updated_ago=time_ago(timestamp) if timestamp else None,
        is_cached=is_cached,
        sharing_enabled=True,
        whatsapp_link=owner_settings.get("whatsapp_link"),
        meet_link=owner_settings.get("meet_link"),
        emergency_contact=owner_settings.get("emergency_contact"),
        emergency_contact_name=owner_settings.get("emergency_contact_name"),
    )
