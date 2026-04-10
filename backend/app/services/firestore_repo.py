"""Firestore repository — CRUD operations for all collections."""

from google.cloud.firestore_v1 import Client as FirestoreClient
from datetime import datetime, timezone
from typing import Optional
import logging

from app.models.firestore import (
    UserDoc, LatestStatusDoc, RefreshRequestDoc,
    AccessLogDoc, OwnerSettingsDoc
)
from app.utils.helpers import utc_now

logger = logging.getLogger(__name__)


class FirestoreRepository:
    """Data access layer for all Firestore collections."""

    def __init__(self, db: FirestoreClient):
        self.db = db

    # ── Users ───────────────────────────────────────────────────────────────

    def get_user(self, uid: str) -> Optional[dict]:
        doc = self.db.collection("users").document(uid).get()
        return doc.to_dict() if doc.exists else None

    def get_user_by_email(self, email: str) -> Optional[dict]:
        docs = (
            self.db.collection("users")
            .where("email", "==", email)
            .limit(1)
            .stream()
        )
        for doc in docs:
            data = doc.to_dict()
            data["uid"] = doc.id
            return data
        return None

    def create_user(self, uid: str, email: str, display_name: str = None,
                    approved: bool = False, role: str = "viewer") -> dict:
        now = utc_now()
        data = {
            "uid": uid,
            "email": email,
            "display_name": display_name or email.split("@")[0],
            "approved": approved,
            "role": role,
            "created_at": now,
            "updated_at": now,
        }
        self.db.collection("users").document(uid).set(data)
        logger.info(f"Created user {uid} ({email})")
        return data

    def update_user(self, uid: str, updates: dict) -> None:
        updates["updated_at"] = utc_now()
        self.db.collection("users").document(uid).update(updates)

    def get_whitelist(self) -> list[dict]:
        docs = self.db.collection("users").where("role", "==", "viewer").stream()
        result = []
        for doc in docs:
            data = doc.to_dict()
            data["uid"] = doc.id
            result.append(data)
        return result

    def add_to_whitelist(self, email: str, display_name: str = None) -> dict:
        """Add a user to the whitelist. Creates a placeholder if UID unknown."""
        existing = self.get_user_by_email(email)
        if existing:
            self.update_user(existing["uid"], {"approved": True})
            return existing

        # Create a placeholder document keyed by a sanitized email
        placeholder_id = email.replace("@", "_at_").replace(".", "_")
        return self.create_user(
            uid=placeholder_id,
            email=email,
            display_name=display_name,
            approved=True,
            role="viewer",
        )

    def remove_from_whitelist(self, email: str) -> bool:
        existing = self.get_user_by_email(email)
        if existing:
            self.update_user(existing["uid"], {"approved": False})
            return True
        return False

    # ── Latest Status ───────────────────────────────────────────────────────

    def get_latest_status(self, owner_id: str) -> Optional[dict]:
        doc = self.db.collection("latest_status").document(owner_id).get()
        return doc.to_dict() if doc.exists else None

    def upsert_latest_status(self, owner_id: str, status_data: dict) -> None:
        status_data["owner_id"] = owner_id
        status_data["timestamp"] = utc_now()
        self.db.collection("latest_status").document(owner_id).set(
            status_data, merge=True
        )
        logger.info(f"Updated latest_status for owner {owner_id}")

    # ── Refresh Requests ────────────────────────────────────────────────────

    def create_refresh_request(self, request_id: str, viewer_uid: str,
                                owner_id: str) -> dict:
        now = utc_now()
        data = {
            "request_id": request_id,
            "viewer_uid": viewer_uid,
            "owner_id": owner_id,
            "status": "pending",
            "created_at": now,
            "completed_at": None,
        }
        self.db.collection("refresh_requests").document(request_id).set(data)
        return data

    def get_refresh_request(self, request_id: str) -> Optional[dict]:
        doc = self.db.collection("refresh_requests").document(request_id).get()
        return doc.to_dict() if doc.exists else None

    def complete_refresh_request(self, request_id: str) -> None:
        self.db.collection("refresh_requests").document(request_id).update({
            "status": "completed",
            "completed_at": utc_now(),
        })

    # ── Access Logs ─────────────────────────────────────────────────────────

    def log_access(self, viewer_uid: str, result: str = "success",
                   viewer_email: str = None, user_agent: str = None,
                   ip_address: str = None) -> None:
        data = {
            "viewer_uid": viewer_uid,
            "viewer_email": viewer_email,
            "timestamp": utc_now(),
            "result": result,
            "user_agent": user_agent,
            "ip_address": ip_address,
        }
        self.db.collection("access_logs").add(data)

    def get_access_logs(self, limit: int = 50, offset: int = 0) -> list[dict]:
        docs = (
            self.db.collection("access_logs")
            .order_by("timestamp", direction="DESCENDING")
            .limit(limit)
            .stream()
        )
        logs = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            # Convert timestamps to ISO strings for JSON serialization
            if data.get("timestamp"):
                data["timestamp"] = data["timestamp"].isoformat()
            logs.append(data)
        return logs

    def get_access_logs_count(self) -> int:
        # Firestore doesn't have a native count — approximate
        docs = self.db.collection("access_logs").stream()
        return sum(1 for _ in docs)

    # ── Owner Settings ──────────────────────────────────────────────────────

    def get_owner_settings(self, owner_id: str) -> dict:
        doc = self.db.collection("owner_settings").document(owner_id).get()
        if doc.exists:
            return doc.to_dict()
        # Create default settings
        default = {
            "owner_id": owner_id,
            "sharing_enabled": True,
            "whatsapp_link": None,
            "meet_link": None,
            "emergency_contact": None,
            "emergency_contact_name": None,
            "fcm_device_token": None,
            "updated_at": utc_now(),
        }
        self.db.collection("owner_settings").document(owner_id).set(default)
        return default

    def update_owner_settings(self, owner_id: str, updates: dict) -> dict:
        updates["updated_at"] = utc_now()
        self.db.collection("owner_settings").document(owner_id).set(
            updates, merge=True
        )
        return self.get_owner_settings(owner_id)

    def get_fcm_token(self, owner_id: str) -> Optional[str]:
        settings = self.get_owner_settings(owner_id)
        return settings.get("fcm_device_token")
