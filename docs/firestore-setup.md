# Firestore Schema & Setup

## Collections

### `users`
Document ID: Firebase UID

```json
{
    "uid": "string — Firebase UID",
    "email": "string — user email",
    "display_name": "string — optional display name",
    "approved": "boolean — whether this user can view status",
    "role": "string — 'viewer' or 'owner'",
    "created_at": "timestamp",
    "updated_at": "timestamp"
}
```

### `latest_status`
Document ID: Owner's Firebase UID

```json
{
    "owner_id": "string — owner UID",
    "sound_status": "string — 'Phone is on silent' etc.",
    "movement_status": "string — 'Currently stationary' etc.",
    "network_status": "string — 'Network looks good' etc.",
    "outdoor_status": "string — 'Likely indoors' etc.",
    "contact_suggestion": "string|null — suggestion text",
    "contact_methods": "array[string] — ['whatsapp', 'meet', etc.]",
    "device_battery": "number|null — 0-100",
    "summary": "string — one-line summary",
    "timestamp": "timestamp — when status was last updated"
}
```

### `refresh_requests`
Document ID: UUID (request_id)

```json
{
    "request_id": "string — UUID",
    "viewer_uid": "string — who requested the refresh",
    "owner_id": "string — whose status was requested",
    "status": "string — 'pending' or 'completed'",
    "created_at": "timestamp",
    "completed_at": "timestamp|null"
}
```

### `access_logs`
Document ID: Auto-generated

```json
{
    "viewer_uid": "string",
    "viewer_email": "string|null",
    "timestamp": "timestamp",
    "result": "string — 'success', 'denied:not_registered', 'denied:not_approved'",
    "user_agent": "string|null",
    "ip_address": "string|null"
}
```

### `owner_settings`
Document ID: Owner's Firebase UID

```json
{
    "owner_id": "string",
    "sharing_enabled": "boolean — master toggle",
    "whatsapp_link": "string|null — https://wa.me/...",
    "meet_link": "string|null — https://meet.google.com/...",
    "emergency_contact": "string|null — tel:+91...",
    "emergency_contact_name": "string|null",
    "fcm_device_token": "string|null — FCM token from Android",
    "updated_at": "timestamp"
}
```

## Indexes Required

Firestore requires composite indexes for some queries:

1. **access_logs**: `timestamp` (Descending) — auto-created on first query
2. **users**: `role` + `approved` — auto-created on first query

## Security Rules

For production, use these Firestore security rules:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Deny all client-side access — all operations go through backend
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```

The backend uses the Admin SDK which bypasses security rules, so we deny all direct client access.
