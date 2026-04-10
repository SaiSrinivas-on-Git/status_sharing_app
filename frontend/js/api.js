/* ═══════════════════════════════════════════════════════════════
   api.js — Backend API client
   ═══════════════════════════════════════════════════════════════ */

// Backend URL — change for production
const API_BASE_URL = 'http://localhost:8080';

/**
 * Make an authenticated API request.
 * @param {string} endpoint — e.g. '/viewer/open'
 * @param {object} options — fetch options
 * @returns {Promise<object>} — parsed JSON response
 */
async function apiRequest(endpoint, options = {}) {
    const token = await getIdToken();

    const config = {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            ...(options.headers || {}),
        },
    };

    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

    if (response.status === 403) {
        const data = await response.json().catch(() => ({}));
        throw { status: 403, detail: data.detail || 'Access denied' };
    }

    if (response.status === 401) {
        // Token expired — try refreshing
        const newToken = await currentUser.getIdToken(true);
        config.headers['Authorization'] = `Bearer ${newToken}`;
        const retry = await fetch(`${API_BASE_URL}${endpoint}`, config);
        if (!retry.ok) {
            throw { status: retry.status, detail: 'Authentication failed' };
        }
        return retry.json();
    }

    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw { status: response.status, detail: data.detail || 'Request failed' };
    }

    return response.json();
}

// ── Viewer API ──────────────────────────────────────────────────

/**
 * Open a viewer session — triggers FCM to the device.
 * @returns {Promise<{request_id: string}>}
 */
async function apiViewerOpen() {
    return apiRequest('/viewer/open', { method: 'POST' });
}

/**
 * Poll for latest status.
 * @param {string} requestId
 * @returns {Promise<object>} — StatusResponse
 */
async function apiGetLatestStatus(requestId) {
    const params = requestId ? `?request_id=${requestId}` : '';
    return apiRequest(`/status/latest${params}`);
}

// ── Owner API ───────────────────────────────────────────────────

async function apiGetOwnerLogs(limit = 50) {
    return apiRequest(`/owner/logs?limit=${limit}`);
}

async function apiGetOwnerSettings() {
    return apiRequest('/owner/settings');
}

async function apiUpdateOwnerSettings(updates) {
    return apiRequest('/owner/settings', {
        method: 'PUT',
        body: JSON.stringify(updates),
    });
}

async function apiGetWhitelist() {
    return apiRequest('/owner/whitelist');
}

async function apiAddToWhitelist(email, displayName = null) {
    return apiRequest('/owner/whitelist/add', {
        method: 'POST',
        body: JSON.stringify({ email, display_name: displayName }),
    });
}

async function apiRemoveFromWhitelist(email) {
    return apiRequest('/owner/whitelist/remove', {
        method: 'POST',
        body: JSON.stringify({ email }),
    });
}
