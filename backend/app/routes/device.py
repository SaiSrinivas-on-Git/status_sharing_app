"""Device routes — receive status uploads from Android app."""

from fastapi import APIRouter, Depends
from google.cloud.firestore_v1 import Client as FirestoreClient
import logging

from app.dependencies import require_owner, get_firestore_client
from app.services.firestore_repo import FirestoreRepository
from app.models.requests import DeviceUploadRequest, FCMTokenUpdate
from app.models.responses import MessageResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/device", tags=["Device"])


@router.post("/upload-status", response_model=MessageResponse)
async def upload_status(
    payload: DeviceUploadRequest,
    decoded_token: dict = Depends(require_owner),
    db: FirestoreClient = Depends(get_firestore_client),
):
    """
    Receive derived status from Android device.
    Updates latest_status and marks refresh_request as completed.
    """
    repo = FirestoreRepository(db)

    # Update latest status (only derived data, never raw GPS)
    status_data = {
        "sound_status": payload.sound_status,
        "movement_status": payload.movement_status,
        "network_status": payload.network_status,
        "outdoor_status": payload.outdoor_status,
        "contact_suggestion": payload.contact_suggestion,
        "contact_methods": payload.contact_methods,
        "device_battery": payload.device_battery,
        "summary": payload.summary,
    }
    repo.upsert_latest_status(payload.owner_id, status_data)

    # Mark refresh request as completed
    try:
        repo.complete_refresh_request(payload.request_id)
    except Exception as e:
        logger.warning(f"Could not complete refresh request {payload.request_id}: {e}")

    logger.info(f"Status uploaded for request {payload.request_id}")
    return MessageResponse(message="Status uploaded successfully", success=True)


@router.post("/update-fcm-token", response_model=MessageResponse)
async def update_fcm_token(
    payload: FCMTokenUpdate,
    decoded_token: dict = Depends(require_owner),
    db: FirestoreClient = Depends(get_firestore_client),
):
    """Update the FCM device token (called by Android app on token refresh)."""
    repo = FirestoreRepository(db)
    owner_id = decoded_token["uid"]
    repo.update_owner_settings(owner_id, {"fcm_device_token": payload.token})
    logger.info(f"FCM token updated for owner {owner_id}")
    return MessageResponse(message="FCM token updated", success=True)
