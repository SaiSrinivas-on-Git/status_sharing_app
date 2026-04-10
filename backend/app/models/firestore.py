"""Pydantic models for Firestore documents."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserDoc(BaseModel):
    """Represents a user in the 'users' collection."""
    uid: str
    email: str
    display_name: Optional[str] = None
    approved: bool = False
    role: str = "viewer"  # "viewer" or "owner"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LatestStatusDoc(BaseModel):
    """Represents derived status in 'latest_status' collection."""
    owner_id: str
    sound_status: str = "Unknown"
    movement_status: str = "Unknown"
    network_status: str = "Unknown"
    outdoor_status: str = "Unknown"
    contact_suggestion: Optional[str] = None
    contact_methods: list[str] = Field(default_factory=list)
    timestamp: Optional[datetime] = None
    device_battery: Optional[int] = None
    summary: Optional[str] = None


class RefreshRequestDoc(BaseModel):
    """Represents a status refresh request."""
    request_id: str
    viewer_uid: str
    owner_id: str
    status: str = "pending"  # "pending", "completed", "timeout"
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AccessLogDoc(BaseModel):
    """Represents an access log entry."""
    viewer_uid: str
    viewer_email: Optional[str] = None
    timestamp: Optional[datetime] = None
    result: str = "success"  # "success", "denied:not_registered", "denied:not_approved"
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class OwnerSettingsDoc(BaseModel):
    """Represents owner settings."""
    owner_id: str = ""
    sharing_enabled: bool = True
    whatsapp_link: Optional[str] = None
    meet_link: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    fcm_device_token: Optional[str] = None
    updated_at: Optional[datetime] = None
