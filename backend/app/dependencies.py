"""Dependency injection: Firebase Admin SDK, Firestore client, Auth."""

import firebase_admin
from firebase_admin import credentials, firestore, auth, messaging
from google.cloud.firestore_v1 import Client as FirestoreClient
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from app.config import get_settings, Settings

logger = logging.getLogger(__name__)

# ── Firebase Admin SDK (singleton) ──────────────────────────────────────────

_firebase_app: Optional[firebase_admin.App] = None
_firestore_client: Optional[FirestoreClient] = None

security = HTTPBearer(auto_error=False)


def init_firebase() -> None:
    """Initialize Firebase Admin SDK. Call once at startup."""
    global _firebase_app, _firestore_client
    if _firebase_app is not None:
        return

    settings = get_settings()
    try:
        cred = credentials.Certificate(settings.firebase_credentials_path)
        _firebase_app = firebase_admin.initialize_app(cred, {
            "projectId": settings.firebase_project_id,
        })
        _firestore_client = firestore.client()
        logger.info("Firebase Admin SDK initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        raise


def get_firestore_client() -> FirestoreClient:
    """Get the Firestore client instance."""
    if _firestore_client is None:
        init_firebase()
    return _firestore_client


# ── Auth Dependencies ───────────────────────────────────────────────────────

async def verify_firebase_token(
    credentials_header: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """
    Verify Firebase ID token from Authorization header.
    Returns the decoded token payload (contains uid, email, etc.)
    """
    if credentials_header is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )

    token = credentials_header.credentials
    try:
        decoded = auth.verify_id_token(token)
        return decoded
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        )


async def require_whitelisted(
    decoded_token: dict = Depends(verify_firebase_token),
    db: FirestoreClient = Depends(get_firestore_client),
) -> dict:
    """Verify the user is in the whitelist (approved=True in users collection)."""
    uid = decoded_token.get("uid")
    user_doc = db.collection("users").document(uid).get()

    if not user_doc.exists:
        logger.warning(f"Access denied: user {uid} not in users collection")
        # Log denied access
        _log_denied_access(db, uid, "not_registered")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: not registered",
        )

    user_data = user_doc.to_dict()
    if not user_data.get("approved", False):
        logger.warning(f"Access denied: user {uid} not approved")
        _log_denied_access(db, uid, "not_approved")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: not approved",
        )

    decoded_token["_user_data"] = user_data
    return decoded_token


async def require_owner(
    decoded_token: dict = Depends(verify_firebase_token),
) -> dict:
    """Verify the user is the owner."""
    settings = get_settings()
    uid = decoded_token.get("uid")

    if uid != settings.owner_uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: owner only",
        )
    return decoded_token


def _log_denied_access(db: FirestoreClient, uid: str, reason: str) -> None:
    """Log a denied access attempt."""
    from datetime import datetime, timezone
    try:
        db.collection("access_logs").add({
            "viewer_uid": uid,
            "timestamp": datetime.now(timezone.utc),
            "result": f"denied:{reason}",
        })
    except Exception as e:
        logger.error(f"Failed to log denied access: {e}")
