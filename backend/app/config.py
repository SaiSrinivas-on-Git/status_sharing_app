"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Firebase
    firebase_credentials_path: str = Field(
        default="firebase-credentials.json",
        description="Path to Firebase service account JSON"
    )
    firebase_project_id: str = Field(
        default="",
        description="Firebase project ID"
    )

    # Owner
    owner_uid: str = Field(
        default="",
        description="Firebase UID of the device owner"
    )

    # FCM
    fcm_device_token: Optional[str] = Field(
        default=None,
        description="FCM token of the Android device (fallback; prefer Firestore)"
    )

    # Google Maps
    google_maps_api_key: Optional[str] = Field(
        default=None,
        description="Google Maps API key for outdoor heuristic"
    )

    # CORS
    cors_origins: str = Field(
        default="http://localhost:8080,http://127.0.0.1:8080",
        description="Comma-separated allowed CORS origins"
    )

    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8080)
    debug: bool = Field(default=False)

    # Rate limiting
    rate_limit_viewer_per_minute: int = Field(default=10)

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# Singleton
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
