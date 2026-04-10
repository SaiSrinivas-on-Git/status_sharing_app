"""Viewer routes — trigger status refresh and poll for results."""

from fastapi import APIRouter, Depends, Request, HTTPException
from google.cloud.firestore_v1 import Client as FirestoreClient
import logging

from app.dependencies import require_whitelisted, get_firestore_client
from app.config import get_settings
from app.services.firestore_repo import FirestoreRepository
from app.services.fcm_service import FCMService
from app.models.responses import ViewerOpenResponse
from app.utils.helpers import generate_request_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/viewer", tags=["Viewer"])


@router.post("/open", response_model=ViewerOpenResponse)
async def viewer_open(
    request: Request,
    decoded_token: dict = Depends(require_whitelisted),
    db: FirestoreClient = Depends(get_firestore_client),
):
    """
    Viewer opens the status page.
    1. Auth + whitelist verified (by dependency)
    2. Generate request_id
    3. Log access
    4. Create pending refresh_request
    5. Send FCM to Android device
    6. Return request_id for polling
    """
    settings = get_settings()
    repo = FirestoreRepository(db)
    viewer_uid = decoded_token["uid"]
    viewer_email = decoded_token.get("email", "unknown")

    # Check if sharing is enabled
    owner_settings = repo.get_owner_settings(settings.owner_uid)
    if not owner_settings.get("sharing_enabled", True):
        raise HTTPException(
            status_code=403,
            detail="Status sharing is currently disabled by the owner"
        )

    # Generate request ID
    request_id = generate_request_id()

    # Log access
    user_agent = request.headers.get("user-agent", "")
    client_ip = request.client.host if request.client else "unknown"
    repo.log_access(
        viewer_uid=viewer_uid,
        result="success",
        viewer_email=viewer_email,
        user_agent=user_agent,
        ip_address=client_ip,
    )

    # Create pending refresh request
    repo.create_refresh_request(
        request_id=request_id,
        viewer_uid=viewer_uid,
        owner_id=settings.owner_uid,
    )

    # Trigger FCM
    fcm_token = repo.get_fcm_token(settings.owner_uid)
    if not fcm_token:
        # Fall back to env var
        fcm_token = settings.fcm_device_token

    if fcm_token:
        fcm = FCMService()
        success = fcm.send_refresh_trigger(fcm_token, request_id)
        if not success:
            logger.warning(f"FCM trigger failed for request {request_id}")
    else:
        logger.warning("No FCM token available — device will not be notified")

    return ViewerOpenResponse(
        request_id=request_id,
        message="Status refresh triggered"
    )
