"""Pydantic response models for API endpoints."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class HealthResponse(BaseModel):
    status: str = "ok"
    timestamp: datetime


class ViewerOpenResponse(BaseModel):
    request_id: str
    message: str = "Status refresh triggered"


class StatusResponse(BaseModel):
    """Status response for viewers."""
    request_status: str = Field(description="'pending', 'completed', or 'cached'")
    sound_status: Optional[str] = None
    movement_status: Optional[str] = None
    network_status: Optional[str] = None
    outdoor_status: Optional[str] = None
    contact_suggestion: Optional[str] = None
    contact_methods: list[str] = Field(default_factory=list)
    device_battery: Optional[int] = None
    summary: Optional[str] = None
    last_updated: Optional[datetime] = None
    last_updated_ago: Optional[str] = None
    is_cached: bool = False
    sharing_enabled: bool = True

    # Owner contact info (from settings)
    whatsapp_link: Optional[str] = None
    meet_link: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_contact_name: Optional[str] = None


class AccessLogResponse(BaseModel):
    logs: list[dict] = Field(default_factory=list)
    total: int = 0


class OwnerSettingsResponse(BaseModel):
    sharing_enabled: bool = True
    whatsapp_link: Optional[str] = None
    meet_link: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    fcm_device_token: Optional[str] = None


class WhitelistResponse(BaseModel):
    users: list[dict] = Field(default_factory=list)


class MessageResponse(BaseModel):
    message: str
    success: bool = True
