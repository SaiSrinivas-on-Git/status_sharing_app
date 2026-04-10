/* ═══════════════════════════════════════════════════════════════
   viewer.js — Viewer dashboard logic
   ═══════════════════════════════════════════════════════════════ */

// ── Polling Config ──────────────────────────────────────────────
const POLL_INTERVAL_MS = 2000;
const MAX_POLLS = 5; // 5 polls × 2s = 10 seconds max

let currentRequestId = null;
let pollCount = 0;
let pollTimer = null;

/**
 * Initiate a status refresh: call viewer/open, then start polling.
 */
async function refreshStatus() {
    const refreshBtn = document.getElementById('btn-refresh');
    refreshBtn.disabled = true;

    try {
        // Set cards to loading state
        setCardsLoading(true);
        showPollingIndicator(true);

        // Trigger refresh
        const result = await apiViewerOpen();
        currentRequestId = result.request_id;
        pollCount = 0;

        // Start polling
        startPolling();

    } catch (error) {
        if (error.status === 403) {
            showScreen('denied-screen');
            document.getElementById('denied-message').textContent =
                error.detail || 'You are not authorized to view this status.';
        } else {
            showToast('Failed to refresh status: ' + (error.detail || error.message), 'error');
            // Try to show cached status
            loadCachedStatus();
        }
        showPollingIndicator(false);
        refreshBtn.disabled = false;
    }
}

/**
 * Start the polling loop.
 */
function startPolling() {
    if (pollTimer) clearInterval(pollTimer);

    pollTimer = setInterval(async () => {
        pollCount++;

        try {
            const status = await apiGetLatestStatus(currentRequestId);

            if (status.request_status === 'completed') {
                // Fresh status received!
                stopPolling();
                renderStatus(status, false);
                showToast('Status updated', 'success');
            } else if (status.request_status === 'disabled') {
                stopPolling();
                renderDisabledState();
            } else if (pollCount >= MAX_POLLS) {
                // Timeout — show cached
                stopPolling();
                if (status.sound_status && status.sound_status !== 'Unknown') {
                    renderStatus(status, true);
                    showToast('Showing cached status (device did not respond)', 'info');
                } else {
                    loadCachedStatus();
                }
            }
            // else: still pending, keep polling
        } catch (error) {
            console.error('Polling error:', error);
            stopPolling();
            loadCachedStatus();
        }
    }, POLL_INTERVAL_MS);
}

/**
 * Stop the polling loop.
 */
function stopPolling() {
    if (pollTimer) {
        clearInterval(pollTimer);
        pollTimer = null;
    }
    showPollingIndicator(false);
    document.getElementById('btn-refresh').disabled = false;
}

/**
 * Load cached status (no request_id).
 */
async function loadCachedStatus() {
    try {
        const status = await apiGetLatestStatus(null);
        if (status.request_status !== 'no_data') {
            renderStatus(status, true);
        } else {
            renderNoDataState();
        }
    } catch (error) {
        if (error.status === 403) {
            showScreen('denied-screen');
        } else {
            renderNoDataState();
        }
    }
}

/**
 * Render status data onto the dashboard cards.
 * @param {object} status — StatusResponse
 * @param {boolean} isCached
 */
function renderStatus(status, isCached) {
    setCardsLoading(false);

    // Sound
    const soundEl = document.getElementById('status-sound');
    soundEl.textContent = status.sound_status || '—';
    setCardStatus('card-sound', classifySound(status.sound_status));

    // Movement
    const moveEl = document.getElementById('status-movement');
    moveEl.textContent = status.movement_status || '—';
    setCardStatus('card-movement', classifyMovement(status.movement_status));

    // Network
    const netEl = document.getElementById('status-network');
    netEl.textContent = status.network_status || '—';
    setCardStatus('card-network', classifyNetwork(status.network_status));

    // Location
    const locEl = document.getElementById('status-outdoor');
    locEl.textContent = status.outdoor_status || '—';
    setCardStatus('card-outdoor', classifyLocation(status.outdoor_status));

    // Battery
    const battEl = document.getElementById('status-battery');
    if (status.device_battery !== null && status.device_battery !== undefined) {
        battEl.textContent = `${status.device_battery}%`;
        setCardStatus('card-battery', status.device_battery > 20 ? 'good' : 'alert');
    } else {
        battEl.textContent = 'Unknown';
        setCardStatus('card-battery', 'unknown');
    }

    // Summary
    const sumEl = document.getElementById('status-summary');
    sumEl.textContent = status.summary || 'Status available';
    setCardStatus('card-summary', 'info');

    // Timestamp
    const tsEl = document.getElementById('last-updated-text');
    if (status.last_updated) {
        tsEl.textContent = `Last updated: ${formatTimestamp(status.last_updated)} (${status.last_updated_ago || timeAgo(status.last_updated)})`;
    }

    // Cache indicator
    const cacheBadge = document.getElementById('cache-indicator');
    if (isCached) {
        cacheBadge.classList.remove('hidden');
    } else {
        cacheBadge.classList.add('hidden');
    }

    // Contact section
    renderContactSection(status);
}

/**
 * Render contact suggestion and buttons.
 */
function renderContactSection(status) {
    const section = document.getElementById('contact-section');
    const suggText = document.getElementById('contact-suggestion-text');
    const buttonsEl = document.getElementById('contact-buttons');

    buttonsEl.innerHTML = '';

    const hasContactInfo = status.whatsapp_link || status.meet_link || status.emergency_contact;

    if (status.contact_suggestion || hasContactInfo) {
        section.classList.remove('hidden');

        if (status.contact_suggestion) {
            suggText.textContent = status.contact_suggestion;
            suggText.style.display = '';
        } else {
            suggText.style.display = 'none';
        }

        // Contact buttons
        if (status.whatsapp_link) {
            buttonsEl.innerHTML += `
                <a href="${status.whatsapp_link}" target="_blank" class="contact-btn contact-btn-whatsapp">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.116.547 4.107 1.511 5.84L0 24l6.335-1.652A11.95 11.95 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 21.75c-1.98 0-3.82-.58-5.37-1.58l-.385-.23-3.76.98.99-3.63-.25-.4A9.69 9.69 0 012.25 12 9.75 9.75 0 0112 2.25 9.75 9.75 0 0121.75 12 9.75 9.75 0 0112 21.75z"/></svg>
                    WhatsApp
                </a>`;
        }

        if (status.meet_link) {
            buttonsEl.innerHTML += `
                <a href="${status.meet_link}" target="_blank" class="contact-btn contact-btn-meet">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                    Google Meet
                </a>`;
        }

        if (status.emergency_contact) {
            const name = status.emergency_contact_name || 'Emergency';
            buttonsEl.innerHTML += `
                <a href="${status.emergency_contact}" class="contact-btn contact-btn-emergency">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z"/></svg>
                    ${name}
                </a>`;
        }
    } else {
        section.classList.add('hidden');
    }
}

/**
 * Set all status cards to loading state.
 */
function setCardsLoading(loading) {
    document.querySelectorAll('.status-card').forEach(card => {
        if (loading) {
            card.classList.add('loading');
        } else {
            card.classList.remove('loading');
        }
    });
}

/**
 * Set the visual status of a card.
 */
function setCardStatus(cardId, status) {
    const card = document.getElementById(cardId);
    if (card) card.dataset.status = status;
}

/**
 * Show/hide the polling indicator.
 */
function showPollingIndicator(show) {
    const el = document.getElementById('polling-indicator');
    if (show) {
        el.classList.remove('hidden');
    } else {
        el.classList.add('hidden');
    }
}

// ── Status Classification Helpers ───────────────────────────────

function classifySound(status) {
    if (!status) return 'unknown';
    const s = status.toLowerCase();
    if (s.includes('reachable')) return 'good';
    if (s.includes('vibrate')) return 'warning';
    if (s.includes('silent')) return 'alert';
    return 'unknown';
}

function classifyMovement(status) {
    if (!status) return 'unknown';
    const s = status.toLowerCase();
    if (s.includes('stationary')) return 'good';
    if (s.includes('on the move') || s.includes('possibly')) return 'warning';
    if (s.includes('travelling')) return 'info';
    return 'unknown';
}

function classifyNetwork(status) {
    if (!status) return 'unknown';
    const s = status.toLowerCase();
    if (s.includes('good')) return 'good';
    if (s.includes('weak') && s.includes('wifi')) return 'warning';
    if (s.includes('weak')) return 'alert';
    return 'unknown';
}

function classifyLocation(status) {
    if (!status) return 'unknown';
    const s = status.toLowerCase();
    if (s.includes('indoors')) return 'good';
    if (s.includes('outdoors')) return 'info';
    if (s.includes('uncertain')) return 'warning';
    return 'unknown';
}

/**
 * Render "no data" state.
 */
function renderNoDataState() {
    setCardsLoading(false);
    document.getElementById('status-sound').textContent = 'No status yet';
    document.getElementById('status-movement').textContent = 'Waiting for device...';
    document.getElementById('status-network').textContent = '—';
    document.getElementById('status-outdoor').textContent = '—';
    document.getElementById('status-battery').textContent = '—';
    document.getElementById('status-summary').textContent = 'No status data available. The device has not reported yet.';

    document.querySelectorAll('.status-card').forEach(c => c.dataset.status = 'unknown');
}

/**
 * Render "disabled" state.
 */
function renderDisabledState() {
    setCardsLoading(false);
    document.getElementById('status-summary').textContent = 'Status sharing is currently disabled by the owner.';
    document.querySelectorAll('.status-card:not(#card-summary)').forEach(c => {
        c.classList.add('hidden');
    });
    document.getElementById('contact-section').classList.add('hidden');
}
