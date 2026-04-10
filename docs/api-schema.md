# API Schema — Request & Response Reference

Base URL: `http://localhost:8080` (local) or `https://your-cloud-run-url.run.app` (production)

All endpoints (except `/health`) require a Firebase ID token in the `Authorization` header:
```
Authorization: Bearer <firebase-id-token>
```

---

## Health Check

### `GET /health`

No authentication required.

**Response:**
```json
{
    "status": "ok",
    "timestamp": "2026-04-10T12:00:00Z"
}
```

---

## Viewer Endpoints

### `POST /viewer/open`

Triggers a status refresh. Requires whitelisted user.

**Request:** Empty body (auth in header)

**Response:**
```json
{
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Status refresh triggered"
}
```

**Errors:**
- `401` — Invalid/missing token
- `403` — User not whitelisted, or sharing disabled

---

### `GET /status/latest?request_id=<uuid>`

Poll for status. Requires whitelisted user.

**Response (pending):**
```json
{
    "request_status": "pending"
}
```

**Response (completed):**
```json
{
    "request_status": "completed",
    "sound_status": "Phone is on vibrate",
    "movement_status": "Currently stationary",
    "network_status": "Network looks good (WiFi connected)",
    "outdoor_status": "Likely indoors",
    "contact_suggestion": null,
    "contact_methods": ["call", "whatsapp", "meet"],
    "device_battery": 72,
    "summary": "Phone on vibrate, stationary",
    "last_updated": "2026-04-10T12:05:00Z",
    "last_updated_ago": "2 minutes ago",
    "is_cached": false,
    "sharing_enabled": true,
    "whatsapp_link": "https://wa.me/91XXXXXXXXXX",
    "meet_link": "https://meet.google.com/xxx-xxxx-xxx",
    "emergency_contact": "tel:+91XXXXXXXXXX",
    "emergency_contact_name": "Mom"
}
```

**Response (cached — device didn't respond):**
```json
{
    "request_status": "cached",
    "sound_status": "Phone is reachable",
    "is_cached": true,
    "last_updated_ago": "15 minutes ago",
    "..."
}
```

---

## Device Endpoints

### `POST /device/upload-status`

Upload derived status from Android device. Requires owner auth.

**Request:**
```json
{
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "owner_id": "firebase-owner-uid",
    "sound_status": "Phone is on vibrate",
    "movement_status": "Currently stationary",
    "network_status": "Network looks good (WiFi connected)",
    "outdoor_status": "Likely indoors",
    "contact_suggestion": null,
    "contact_methods": ["call", "whatsapp", "meet"],
    "device_battery": 72,
    "summary": "Phone on vibrate, stationary"
}
```

**Response:**
```json
{
    "message": "Status uploaded successfully",
    "success": true
}
```

---

### `POST /device/update-fcm-token`

Update FCM token. Requires owner auth.

**Request:**
```json
{
    "token": "dHJ5X3RoaXNfaXNfYV9mYWtlX3Rva2Vu..."
}
```

**Response:**
```json
{
    "message": "FCM token updated",
    "success": true
}
```

---

## Owner Endpoints

All require owner auth (Firebase UID must match `OWNER_UID`).

### `GET /owner/logs?limit=50`

**Response:**
```json
{
    "logs": [
        {
            "id": "abc123",
            "viewer_uid": "viewer-uid",
            "viewer_email": "viewer@gmail.com",
            "timestamp": "2026-04-10T12:00:00+00:00",
            "result": "success",
            "ip_address": "192.168.1.1"
        }
    ],
    "total": 1
}
```

### `GET /owner/settings`

```json
{
    "sharing_enabled": true,
    "whatsapp_link": "https://wa.me/91XXXXXXXXXX",
    "meet_link": "https://meet.google.com/xxx-xxxx-xxx",
    "emergency_contact": "tel:+91XXXXXXXXXX",
    "emergency_contact_name": "Mom",
    "fcm_device_token": "dHJ5X3Ro..."
}
```

### `PUT /owner/settings`

```json
{
    "sharing_enabled": true,
    "whatsapp_link": "https://wa.me/91XXXXXXXXXX",
    "meet_link": null,
    "emergency_contact": "tel:+91XXXXXXXXXX",
    "emergency_contact_name": "Mom"
}
```

### `GET /owner/whitelist`

```json
{
    "users": [
        {
            "uid": "viewer-uid",
            "email": "viewer@gmail.com",
            "display_name": "Friend",
            "approved": true,
            "created_at": "2026-04-10T10:00:00+00:00"
        }
    ]
}
```

### `POST /owner/whitelist/add`

```json
{ "email": "friend@gmail.com", "display_name": "Friend" }
```

### `POST /owner/whitelist/remove`

```json
{ "email": "friend@gmail.com" }
```

---

## Testing with cURL

```bash
# Health check
curl http://localhost:8080/health

# Viewer open (replace TOKEN with a Firebase ID token)
curl -X POST http://localhost:8080/viewer/open \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json"

# Poll status
curl http://localhost:8080/status/latest?request_id=REQUEST_ID \
  -H "Authorization: Bearer TOKEN"

# Simulate device upload (as owner)
curl -X POST http://localhost:8080/device/upload-status \
  -H "Authorization: Bearer OWNER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "REQUEST_ID",
    "owner_id": "OWNER_UID",
    "sound_status": "Phone is reachable",
    "movement_status": "Currently stationary",
    "network_status": "Network looks good",
    "outdoor_status": "Likely indoors",
    "device_battery": 85,
    "summary": "Available and reachable",
    "contact_methods": ["call", "whatsapp"]
  }'
```
