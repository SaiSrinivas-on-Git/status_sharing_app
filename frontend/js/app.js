/* ═══════════════════════════════════════════════════════════════
   app.js — Main application controller
   ═══════════════════════════════════════════════════════════════ */

/**
 * Application entry point.
 * Sets up auth listener and handles navigation.
 */
(function initApp() {
    setupAuthListener(
        // ── Authenticated ───────────────────────────────────
        async (user) => {
            console.log('[App] Authenticated:', user.email);

            // Show viewer dashboard
            showScreen('viewer-screen');
            document.getElementById('viewer-user-email').textContent = user.email;

            // Check if user is owner (silently)
            checkOwnerAccess();

            // Auto-refresh status on login
            refreshStatus();
        },

        // ── Unauthenticated ─────────────────────────────────
        () => {
            console.log('[App] Not authenticated');
            showScreen('login-screen');
        }
    );
})();
