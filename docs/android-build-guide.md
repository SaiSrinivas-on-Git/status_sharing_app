# Android APK Build Guide

This guide helps you build and install the Status App APK on your Android phone.

---

## Option 1: Build with Android Studio (Recommended)

### Step 1: Install Android Studio

1. Download from [developer.android.com/studio](https://developer.android.com/studio)
2. Run the installer — select all default options
3. On first launch, let it download the Android SDK (this takes ~10 minutes)

### Step 2: Open the Android Project

1. Open Android Studio
2. Select **"Open"** (not "New Project")
3. Navigate to `c:\Users\Admin\TSAI_EAG_V3\android-app`
4. Click **"OK"**
5. Wait for Gradle sync to complete (may take several minutes the first time)

### Step 3: Add Firebase Configuration

1. Copy your `google-services.json` file (downloaded from Firebase Console)
2. Place it at: `android-app/app/google-services.json`

### Step 4: Configure Backend URL

Edit `android-app/app/build.gradle.kts` and update the `BACKEND_URL`:

```kotlin
// For testing with local backend via USB debugging:
buildConfigField("String", "BACKEND_URL", "\"http://10.0.2.2:8080\"")

// For production (after deploying to Cloud Run):
buildConfigField("String", "BACKEND_URL", "\"https://your-cloud-run-url.run.app\"")
```

### Step 5: Configure Google Sign-In

1. Go to Firebase Console → Authentication → Sign-in method → Google
2. Note the **Web client ID** (looks like `123456-abcdef.apps.googleusercontent.com`)
3. Open `android-app/app/src/main/java/com/statusapp/ui/MainActivity.kt`
4. Replace `YOUR_WEB_CLIENT_ID` with your actual Web Client ID:
```kotlin
.requestIdToken("123456-abcdef.apps.googleusercontent.com")
```

### Step 6: Build the Debug APK

1. In Android Studio, go to **Build → Build Bundle(s) / APK(s) → Build APK(s)**
2. Wait for the build to complete
3. Click **"locate"** in the notification, or find the APK at:
   ```
   android-app/app/build/outputs/apk/debug/app-debug.apk
   ```

### Step 7: Install on Your Phone

**Method A: Via USB (recommended)**
1. Enable **Developer Options** on your phone (Settings → About → tap Build Number 7 times)
2. Enable **USB Debugging** in Developer Options
3. Connect your phone via USB
4. In Android Studio, your phone should appear — click ▶️ Run
5. The app installs and launches automatically

**Method B: Manual APK install**
1. Transfer `app-debug.apk` to your phone (email, Google Drive, USB)
2. Open the APK file on your phone
3. If prompted, enable "Install from unknown sources"
4. Tap "Install"

---

## Option 2: Build from Command Line (without Android Studio GUI)

### Step 1: Install JDK 17

```bash
# Windows — download and install from:
# https://adoptium.net/temurin/releases/ 
# Select: JDK 17, Windows x64, .msi installer
```

After installing, verify:
```bash
java -version
# Should show: openjdk version "17.x.x"
```

### Step 2: Install Android SDK Command-Line Tools

1. Download **Command line tools only** from [developer.android.com/studio#command-tools](https://developer.android.com/studio#command-tools)
2. Extract to `C:\Android\cmdline-tools\latest\`
3. Set environment variables:
```powershell
$env:ANDROID_HOME = "C:\Android"
$env:PATH += ";C:\Android\cmdline-tools\latest\bin;C:\Android\platform-tools"
```

4. Accept licenses and install components:
```bash
sdkmanager --licenses
sdkmanager "platforms;android-35" "build-tools;35.0.0" "platform-tools"
```

### Step 3: Build the APK

```bash
cd android-app

# On Windows:
.\gradlew.bat assembleDebug

# The APK will be at:
# app/build/outputs/apk/debug/app-debug.apk
```

> **Note**: You need the Gradle wrapper. If `gradlew.bat` doesn't exist, generate it:
> ```bash
> gradle wrapper --gradle-version 8.11.1
> ```

---

## After Installation

1. **Open the app** — you'll see a login screen
2. **Sign in with Google** — use the same Google account as your Firebase owner UID
3. **Grant all permissions** — Location, Activity Recognition, Notifications
4. The app shows "Device Active" — it's now ready to respond to status requests
5. The FCM token is automatically uploaded to the backend

### Verifying It Works

1. Check that the FCM token appears on the home screen
2. In Firebase Console → Firestore → `owner_settings`, verify `fcm_device_token` is set
3. Open the web frontend, sign in as a whitelisted viewer
4. The backend should send an FCM to your phone → phone collects data → status appears on web

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Gradle sync fails | Ensure JDK 17 is installed and `JAVA_HOME` is set |
| `google-services.json` error | Ensure the file is at `app/google-services.json` |
| Build fails with SDK error | Run `sdkmanager "platforms;android-35" "build-tools;35.0.0"` |
| App crashes on launch | Check Logcat for errors. Common: missing `google-services.json` |
| Sign-in fails | Verify the Web Client ID in MainActivity matches Firebase |
| FCM not working | Ensure the phone has Google Play Services and is not in battery saver mode |
| Permissions denied | Go to Settings → Apps → Status App → Permissions → enable all |
