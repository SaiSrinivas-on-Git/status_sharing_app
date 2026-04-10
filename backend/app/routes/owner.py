"""Owner routes — logs, settings, and whitelist management."""

from fastapi import APIRouter, Depends
from google.cloud.firestore_v1 import Client as FirestoreClient
import logging

from app.dependencies import require_owner, get_firestore_client
from app.config import get_settings
from app.services.firestore_repo import FirestoreRepository
from app.models.requests import OwnerSettingsUpdate, WhitelistModify
from app.models.responses import (
    AccessLogResponse, OwnerSettingsResponse,
    WhitelistResponse, MessageResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/owner", tags=["Owner"])


@router.get("/logs", response_model=AccessLogResponse)
async def get_logs(
    limit: int = 50,
    decoded_token: dict = Depends(require_owner),
    db: FirestoreClient = Depends(get_firestore_client),
):
    """Get access logs (owner only)."""
    repo = FirestoreRepository(db)
    logs = repo.get_access_logs(limit=limit)
    return AccessLogResponse(logs=logs, total=len(logs))


@router.get("/settings", response_model=OwnerSettingsResponse)
async def get_settings_route(
    decoded_token: dict = Depends(require_owner),
    db: FirestoreClient = Depends(get_firestore_client),
):
    """Get owner settings."""
    settings = get_settings()
    repo = FirestoreRepository(db)
    data = repo.get_owner_settings(settings.owner_uid)
    return OwnerSettingsResponse(
        sharing_enabled=data.get("sharing_enabled", True),
        whatsapp_link=data.get("whatsapp_link"),
        meet_link=data.get("meet_link"),
        emergency_contact=data.get("emergency_contact"),
        emergency_contact_name=data.get("emergency_contact_name"),
        fcm_device_token=data.get("fcm_device_token"),
    )


@router.put("/settings", response_model=MessageResponse)
async def update_settings(
    updates: OwnerSettingsUpdate,
    decoded_token: dict = Depends(require_owner),
    db: FirestoreClient = Depends(get_firestore_client),
):
    """Update owner settings."""
    settings = get_settings()
    repo = FirestoreRepository(db)

    update_dict = updates.model_dump(exclude_none=True)
    if update_dict:
        repo.update_owner_settings(settings.owner_uid, update_dict)

    return MessageResponse(message="Settings updated successfully")


@router.get("/whitelist", response_model=WhitelistResponse)
async def get_whitelist(
    decoded_token: dict = Depends(require_owner),
    db: FirestoreClient = Depends(get_firestore_client),
):
    """Get all whitelisted viewers."""
    repo = FirestoreRepository(db)
    users = repo.get_whitelist()
    # Sanitize output
    safe_users = [
        {
            "uid": u.get("uid"),
            "email": u.get("email"),
            "display_name": u.get("display_name"),
            "approved": u.get("approved", False),
            "created_at": u.get("created_at").isoformat() if u.get("created_at") else None,
        }
        for u in users
    ]
    return WhitelistResponse(users=safe_users)


@router.post("/whitelist/add", response_model=MessageResponse)
async def add_to_whitelist(
    payload: WhitelistModify,
    decoded_token: dict = Depends(require_owner),
    db: FirestoreClient = Depends(get_firestore_client),
):
    """Add a user to the whitelist."""
    repo = FirestoreRepository(db)
    repo.add_to_whitelist(payload.email, payload.display_name)
    logger.info(f"Added {payload.email} to whitelist")
    return MessageResponse(message=f"Added {payload.email} to whitelist")


@router.post("/whitelist/remove", response_model=MessageResponse)
async def remove_from_whitelist(
    payload: WhitelistModify,
    decoded_token: dict = Depends(require_owner),
    db: FirestoreClient = Depends(get_firestore_client),
):
    """Remove a user from the whitelist."""
    repo = FirestoreRepository(db)
    removed = repo.remove_from_whitelist(payload.email)
    if removed:
        logger.info(f"Removed {payload.email} from whitelist")
        return MessageResponse(message=f"Removed {payload.email} from whitelist")
    else:
        return MessageResponse(message=f"User {payload.email} not found", success=False)
