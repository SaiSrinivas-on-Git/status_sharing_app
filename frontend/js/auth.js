/* ═══════════════════════════════════════════════════════════════
   auth.js — Firebase Authentication
   ═══════════════════════════════════════════════════════════════ */

// ── Firebase Config (replace with your project values) ──────────
const FIREBASE_CONFIG = {
    apiKey: "YOUR_API_KEY",
    authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
    projectId: "YOUR_PROJECT_ID",
    storageBucket: "YOUR_PROJECT_ID.firebasestorage.app",
    messagingSenderId: "YOUR_SENDER_ID",
    appId: "YOUR_APP_ID",
};

// Initialize Firebase
firebase.initializeApp(FIREBASE_CONFIG);
const auth = firebase.auth();

// ── State ───────────────────────────────────────────────────────
let currentUser = null;
let idToken = null;

/**
 * Get a fresh Firebase ID token.
 * @returns {Promise<string>}
 */
async function getIdToken() {
    if (!currentUser) throw new Error('Not authenticated');
    // Force refresh if token is older than 50 minutes
    idToken = await currentUser.getIdToken(/* forceRefresh */ false);
    return idToken;
}

/**
 * Handle Google Sign-In.
 */
async function handleGoogleLogin() {
    try {
        const provider = new firebase.auth.GoogleAuthProvider();
        provider.setCustomParameters({ prompt: 'select_account' });
        await auth.signInWithPopup(provider);
        // onAuthStateChanged will handle the rest
    } catch (error) {
        console.error('Login error:', error);
        if (error.code !== 'auth/popup-closed-by-user') {
            showToast('Login failed: ' + error.message, 'error');
        }
    }
}

/**
 * Handle Sign Out.
 */
async function handleLogout() {
    try {
        await auth.signOut();
        currentUser = null;
        idToken = null;
        showScreen('login-screen');
    } catch (error) {
        console.error('Logout error:', error);
        showToast('Logout error', 'error');
    }
}

/**
 * Set up auth state listener.
 * @param {Function} onAuthenticated — called with user object
 * @param {Function} onUnauthenticated — called when signed out
 */
function setupAuthListener(onAuthenticated, onUnauthenticated) {
    auth.onAuthStateChanged(async (user) => {
        if (user) {
            currentUser = user;
            idToken = await user.getIdToken();
            onAuthenticated(user);
        } else {
            currentUser = null;
            idToken = null;
            onUnauthenticated();
        }
    });
}
