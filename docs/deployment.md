# Deployment Guide

## Backend — Cloud Run

### Prerequisites
- [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install) installed
- Same Google account as your Firebase project

### Step 1: Login to gcloud

```bash
gcloud auth login
gcloud config set project YOUR_FIREBASE_PROJECT_ID
```

### Step 2: Enable Required APIs

```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable fcm.googleapis.com
```

### Step 3: Deploy to Cloud Run

```bash
cd backend

gcloud run deploy status-backend \
    --source . \
    --platform managed \
    --region asia-south1 \
    --allow-unauthenticated \
    --set-env-vars="FIREBASE_PROJECT_ID=YOUR_PROJECT_ID,OWNER_UID=YOUR_OWNER_UID,CORS_ORIGINS=https://YOUR_FIREBASE_APP.web.app" \
    --memory=512Mi \
    --min-instances=0 \
    --max-instances=3 \
    --timeout=60
```

> For the Firebase credentials, either:
> - Use Cloud Run's default service account (recommended) — replace the Firebase Admin init to use `firebase_admin.initialize_app()` without a credentials file
> - Or upload the credentials JSON and reference it via `--set-env-vars`

### Step 4: Note the Service URL

After deployment, Cloud Run will print a URL like:
```
https://status-backend-xxxxx-xx.a.run.app
```

Update this URL in:
1. `frontend/js/api.js` → `API_BASE_URL`
2. `android-app/app/build.gradle.kts` → `BACKEND_URL` (release build)
3. Backend `CORS_ORIGINS` env var (add your frontend domain)

---

## Frontend — Firebase Hosting

### Step 1: Install Firebase CLI

```bash
npm install -g firebase-tools
```

### Step 2: Login

```bash
firebase login
```

### Step 3: Initialize Hosting

```bash
cd frontend
firebase init hosting
```

When prompted:
- Select your Firebase project
- Public directory: `.` (current directory)
- Single-page app: `Yes`
- GitHub deploys: `No`
- Overwrite `index.html`: `No`

### Step 4: Update Frontend Config

Edit `frontend/js/auth.js` — set `FIREBASE_CONFIG` with your project values.
Edit `frontend/js/api.js` — set `API_BASE_URL` to your Cloud Run URL.

### Step 5: Deploy

```bash
cd frontend
firebase deploy --only hosting
```

Your app will be live at: `https://YOUR_PROJECT_ID.web.app`

---

## Android App

See [Android Build Guide](android-build-guide.md).

Before building the release APK, update the `BACKEND_URL` in `build.gradle.kts` to your Cloud Run URL.

---

## Environment Variables Reference

### Backend (.env)

| Variable | Required | Description |
|----------|----------|-------------|
| `FIREBASE_CREDENTIALS_PATH` | Yes* | Path to service account JSON |
| `FIREBASE_PROJECT_ID` | Yes | Firebase project ID |
| `OWNER_UID` | Yes | Owner's Firebase UID |
| `CORS_ORIGINS` | Yes | Comma-separated allowed origins |
| `GOOGLE_MAPS_API_KEY` | No | For outdoor heuristic |
| `FCM_DEVICE_TOKEN` | No | Fallback FCM token |
| `HOST` | No | Default: 0.0.0.0 |
| `PORT` | No | Default: 8080 |
| `DEBUG` | No | Default: false |

*On Cloud Run with default service account, credentials are auto-provided.

### Frontend (hardcoded in auth.js)

| Value | Description |
|-------|-------------|
| `FIREBASE_CONFIG` | Firebase web app config object |
| `API_BASE_URL` | Backend URL |

### Android (in build.gradle.kts)

| Value | Description |
|-------|-------------|
| `BACKEND_URL` | Backend URL |
| Web Client ID | In `MainActivity.kt` for Google Sign-In |
