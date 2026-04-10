# Complete Setup Guide — Step by Step

This guide walks you through setting up the entire system from scratch.

---

## Prerequisites

| Tool | Version | Installation |
|------|---------|-------------|
| Python | 3.11+ | [python.org/downloads](https://www.python.org/downloads/) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org/) (already installed) |
| Git | any | [git-scm.com](https://git-scm.com/) |
| Google Account | — | For Firebase |
| Android Studio | latest | [developer.android.com/studio](https://developer.android.com/studio) (for APK build) |

---

## Step 1: Create a Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **"Create a project"**
3. Enter a name (e.g., `status-sharing-app`)
4. **Disable** Google Analytics (optional, saves cost)
5. Click **"Create project"**
6. Wait for it to be ready, then click **"Continue"**

---

## Step 2: Enable Firebase Authentication

1. In Firebase Console, go to **Build → Authentication**
2. Click **"Get Started"**
3. Under **Sign-in providers**, click **"Google"**
4. Toggle **"Enable"** on
5. Set a **support email** (your email)
6. Click **"Save"**

---

## Step 3: Create a Firestore Database

1. Go to **Build → Firestore Database**
2. Click **"Create database"**
3. Select **"Start in test mode"** (we'll secure it later)
4. Choose a location close to you (e.g., `asia-south1` for India)
5. Click **"Create"**

---

## Step 4: Register a Web App (for Frontend)

1. In Firebase Console, click the **gear icon** → **Project settings**
2. Scroll down to **"Your apps"**
3. Click the **Web icon** (`</>`)
4. Enter a nickname (e.g., `status-web`)
5. Check **"Also set up Firebase Hosting"**
6. Click **"Register app"**
7. **Copy the Firebase config object** — you'll need this:

```javascript
const firebaseConfig = {
    apiKey: "AIza...",
    authDomain: "your-project.firebaseapp.com",
    projectId: "your-project-id",
    storageBucket: "your-project.firebasestorage.app",
    messagingSenderId: "123456789",
    appId: "1:123456789:web:abc..."
};
```

8. Open `frontend/js/auth.js` and replace the `FIREBASE_CONFIG` object with your values.

---

## Step 5: Register an Android App (for FCM)

1. In Firebase Console → Project Settings → **"Your apps"**
2. Click the **Android icon**
3. Enter package name: `com.statusapp`
4. Enter nickname: `Status App`
5. Click **"Register app"**
6. **Download `google-services.json`**
7. Place it at: `android-app/app/google-services.json`

---

## Step 6: Get a Firebase Service Account Key (for Backend)

1. In Firebase Console → **gear icon** → **Project settings**
2. Go to **"Service accounts"** tab
3. Click **"Generate new private key"**
4. Download the JSON file
5. Rename it to `firebase-credentials.json`
6. Place it at: `backend/firebase-credentials.json`

---

## Step 7: Find Your Firebase UID (Owner)

1. Sign in to your web app (or any Firebase app) with your Google account
2. Go to Firebase Console → **Build → Authentication → Users**
3. Find your email and copy the **User UID** column value
4. This is your `OWNER_UID`

---

## Step 8: Configure the Backend

1. Copy the example env file:
```bash
cd backend
copy .env.example .env
```

2. Edit `.env` with your values:
```
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
FIREBASE_PROJECT_ID=your-project-id
OWNER_UID=your-firebase-uid
CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080
DEBUG=true
```

---

## Step 9: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

---

## Step 10: Run the Backend Locally

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

You should see:
```
INFO: Uvicorn running on http://0.0.0.0:8080
```

Test it: Open `http://localhost:8080/health` in browser — should show `{"status": "ok", ...}`.

---

## Step 11: Serve the Frontend Locally

Open a new terminal:
```bash
cd frontend
npx -y serve . -l 5000
```

Open `http://localhost:5000` in your browser.

> **Important**: Update `API_BASE_URL` in `frontend/js/api.js` to point to your backend:
> ```javascript
> const API_BASE_URL = 'http://localhost:8080';
> ```

---

## Step 12: Set Up the Android App

See the [Android Build Guide](android-build-guide.md) for detailed instructions.

---

## Step 13: Add Yourself to the Whitelist

After signing in to the web app for the first time, you need to add approved viewers.

### Using the Owner Panel (if you're signed in as the owner):
1. Click the gear icon in the top right
2. Go to the "Whitelist" tab
3. Enter the email of a viewer
4. Click "Add"

### Using the Firebase Console directly:
1. Go to Firestore → Create collection `users`
2. Add a document with ID = the viewer's Firebase UID:
```json
{
    "uid": "viewer-firebase-uid",
    "email": "viewer@gmail.com",
    "display_name": "Viewer Name",
    "approved": true,
    "role": "viewer"
}
```
3. Also add the owner's document:
```json
{
    "uid": "owner-firebase-uid",
    "email": "owner@gmail.com",
    "display_name": "Owner",
    "approved": true,
    "role": "owner"
}
```

---

## Step 14: Test the Complete Flow

1. **Backend** running on port 8080
2. **Frontend** running on port 5000
3. **Android app** installed and signed in as owner
4. Open the frontend in a browser
5. Sign in with a **whitelisted** Google account
6. The app should trigger a refresh → Android device collects data → status appears

---

## Optional: Google Maps API Key

For the outdoor heuristic (location derivation), you need a Google Maps API key:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable **Geocoding API** and **Roads API**
3. Create an API key under **APIs & Services → Credentials**
4. Restrict the key to these APIs only
5. Add to your backend `.env`:
```
GOOGLE_MAPS_API_KEY=your-google-maps-api-key
```

> **Free tier**: Geocoding API gives $200/month free credit. The app is rate-limited to 10 calls/minute with 5-minute caching, so costs should be minimal.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Access denied" on frontend | Your Google account isn't in the whitelist. Add it via Firestore console. |
| FCM not triggering | Ensure `google-services.json` is in the Android app, and the FCM token is uploaded. |
| Backend 500 error | Check `firebase-credentials.json` path and `FIREBASE_PROJECT_ID`. |
| CORS error | Add your frontend URL to `CORS_ORIGINS` in `.env`. |
| Android permissions denied | Go to Settings → Apps → Status App → Permissions and grant all. |
