# Status Sharing System

A **privacy-safe, real-time status sharing system** where one device owner shares their contextual availability with whitelisted viewers. Status is fetched on-demand from an Android device via Firebase Cloud Messaging, processed through a derivation engine, and displayed on a web dashboard.

## Architecture

```
Viewer (Web) → Backend (FastAPI/Cloud Run) → FCM → Android Device
                                              ↑
                    Android collects data, derives status, uploads ─┘
```

## Quick Links

- [Setup Guide](docs/setup-guide.md) — **Start here** for step-by-step setup
- [API Schema](docs/api-schema.md) — API request/response formats
- [Firestore Setup](docs/firestore-setup.md) — Database schema
- [Deployment Guide](docs/deployment.md) — Deploy to Cloud Run & Firebase Hosting
- [APK Build Guide](docs/android-build-guide.md) — Build and install the Android app
- [Cost Optimization](docs/cost-optimization.md) — Keep costs minimal

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.11, FastAPI, Firebase Admin SDK |
| Frontend | Vanilla HTML/CSS/JS, Firebase Auth SDK |
| Android | Kotlin, Jetpack Compose, Firebase Messaging |
| Database | Cloud Firestore |
| Hosting | Cloud Run (backend), Firebase Hosting (frontend) |
| Auth | Firebase Authentication (Google Sign-In) |
| Messaging | Firebase Cloud Messaging (FCM) |

## Project Structure

```
├── backend/          # FastAPI backend
├── frontend/         # Web dashboard
├── android-app/      # Android app (Kotlin/Compose)
└── docs/             # Documentation
```

## Security Principles

- ✅ No raw GPS coordinates exposed to viewers
- ✅ All derived statuses use human-readable phrases
- ✅ Firebase Auth required on all API endpoints
- ✅ Whitelist enforced server-side (never frontend)
- ✅ Access attempts are logged
- ✅ CORS restricted to frontend domain
