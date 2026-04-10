"""Pydantic request models for API endpoints."""

from pydantic import BaseModel, Field
from typing import Optional


class DeviceUploadRequest(BaseModel):
    """Payload from Android device with derived status."""
    request_id: str
    owner_id: str

    # Derived status strings (NOT raw data)
    sound_status: str = Field(description="e.g., 'Phone is on silent'")
    movement_status: str = Field(description="e.g., 'Currently travelling'")
    network_status: str = Field(description="e.g., 'Network looks good'")
    outdoor_status: str = Field(default="Location uncertain", description="e.g., 'Likely outdoors'")
    contact_suggestion: Optional[str] = Field(default=None, description="e.g., 'Try WhatsApp or Meet'")
    contact_methods: list[str] = Field(default_factory=list, description="e.g., ['whatsapp', 'meet']")

    # Optional metadata (non-sensitive)
    device_battery: Optional[int] = Field(default=None, ge=0, le=100)
    summary: Optional[str] = Field(default=None, description="One-line summary")


class OwnerSettingsUpdate(BaseModel):
    """Update owner settings."""
    sharing_enabled: Optional[bool] = None
    whatsapp_link: Optional[str] = None
    meet_link: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_contact_name: Optional[str] = None


class WhitelistModify(BaseModel):
    """Add or remove a user from the whitelist."""
    email: str = Field(description="Email of the user to add/remove")
    display_name: Optional[str] = None


class FCMTokenUpdate(BaseModel):
    """Update the device FCM token."""
    token: str
