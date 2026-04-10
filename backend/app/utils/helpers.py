"""Utility helpers."""

from datetime import datetime, timezone
import uuid


def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())


def time_ago(dt: datetime) -> str:
    """Human-readable time-ago string."""
    if dt is None:
        return "unknown"

    now = utc_now()
    diff = now - dt

    seconds = int(diff.total_seconds())
    if seconds < 60:
        return f"{seconds} seconds ago"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = seconds // 86400
        return f"{days} day{'s' if days != 1 else ''} ago"
