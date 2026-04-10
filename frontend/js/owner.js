/* ═══════════════════════════════════════════════════════════════
   owner.js — Owner panel logic
   ═══════════════════════════════════════════════════════════════ */

let isOwner = false;

/**
 * Check if the current user is the owner and show the panel button.
 */
async function checkOwnerAccess() {
    try {
        await apiGetOwnerSettings();
        isOwner = true;
        document.getElementById('btn-owner-panel').classList.remove('hidden');
    } catch (e) {
        isOwner = false;
    }
}

/**
 * Show the owner panel.
 */
function showOwnerPanel() {
    showScreen('owner-screen');
    document.getElementById('owner-user-email').textContent = currentUser?.email || '';
    switchOwnerTab('settings');
    loadOwnerSettings();
}

/**
 * Show the viewer dashboard.
 */
function showViewerDashboard() {
    showScreen('viewer-screen');
}

/**
 * Switch between owner tabs.
 */
function switchOwnerTab(tabName) {
    // Deactivate all tabs
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => {
        c.classList.add('hidden');
        c.classList.remove('active');
    });

    // Activate selected tab
    document.querySelector(`[data-tab="${tabName}"]`)?.classList.add('active');
    const content = document.getElementById(`tab-${tabName}`);
    if (content) {
        content.classList.remove('hidden');
        content.classList.add('active');
    }

    // Load data for tab
    if (tabName === 'whitelist') loadWhitelist();
    if (tabName === 'logs') loadLogs();
}

// ── Settings ────────────────────────────────────────────────────

async function loadOwnerSettings() {
    try {
        const settings = await apiGetOwnerSettings();
        document.getElementById('sharing-toggle').checked = settings.sharing_enabled !== false;
        document.getElementById('whatsapp-link').value = settings.whatsapp_link || '';
        document.getElementById('meet-link').value = settings.meet_link || '';
        document.getElementById('emergency-name').value = settings.emergency_contact_name || '';
        document.getElementById('emergency-contact').value = settings.emergency_contact || '';
    } catch (e) {
        showToast('Failed to load settings', 'error');
    }
}

async function saveSettings() {
    try {
        const updates = {
            whatsapp_link: document.getElementById('whatsapp-link').value || null,
            meet_link: document.getElementById('meet-link').value || null,
            emergency_contact_name: document.getElementById('emergency-name').value || null,
            emergency_contact: document.getElementById('emergency-contact').value || null,
        };

        await apiUpdateOwnerSettings(updates);
        showToast('Settings saved', 'success');
    } catch (e) {
        showToast('Failed to save settings: ' + (e.detail || e.message), 'error');
    }
}

async function updateSetting(key, value) {
    try {
        const updates = {};
        updates[key] = value;
        await apiUpdateOwnerSettings(updates);
        showToast(`${key.replace('_', ' ')} updated`, 'success');
    } catch (e) {
        showToast('Failed to update setting', 'error');
    }
}

// ── Whitelist ───────────────────────────────────────────────────

async function loadWhitelist() {
    const container = document.getElementById('whitelist-list');
    container.innerHTML = '<p class="empty-state">Loading...</p>';

    try {
        const data = await apiGetWhitelist();
        if (!data.users || data.users.length === 0) {
            container.innerHTML = '<p class="empty-state">No whitelisted users yet</p>';
            return;
        }

        container.innerHTML = data.users.map(user => `
            <div class="whitelist-item">
                <div class="whitelist-item-info">
                    <span class="whitelist-item-email">${user.email}</span>
                    <span class="whitelist-item-name">${user.display_name || '—'}</span>
                </div>
                <div style="display:flex;align-items:center;gap:8px;">
                    <span class="whitelist-status ${user.approved ? 'approved' : 'revoked'}">
                        ${user.approved ? 'Active' : 'Revoked'}
                    </span>
                    <button class="btn btn-danger" onclick="removeFromWhitelist('${user.email}')">
                        Remove
                    </button>
                </div>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = '<p class="empty-state">Failed to load whitelist</p>';
    }
}

async function addToWhitelist() {
    const emailInput = document.getElementById('whitelist-email');
    const nameInput = document.getElementById('whitelist-name');
    const email = emailInput.value.trim();

    if (!email) {
        showToast('Please enter an email address', 'error');
        return;
    }

    try {
        await apiAddToWhitelist(email, nameInput.value.trim() || null);
        showToast(`Added ${email}`, 'success');
        emailInput.value = '';
        nameInput.value = '';
        loadWhitelist();
    } catch (e) {
        showToast('Failed to add user: ' + (e.detail || e.message), 'error');
    }
}

async function removeFromWhitelist(email) {
    if (!confirm(`Remove ${email} from whitelist?`)) return;

    try {
        await apiRemoveFromWhitelist(email);
        showToast(`Removed ${email}`, 'success');
        loadWhitelist();
    } catch (e) {
        showToast('Failed to remove user', 'error');
    }
}

// ── Logs ────────────────────────────────────────────────────────

async function loadLogs() {
    const container = document.getElementById('logs-table-container');
    container.innerHTML = '<p class="empty-state">Loading...</p>';

    try {
        const data = await apiGetOwnerLogs();
        if (!data.logs || data.logs.length === 0) {
            container.innerHTML = '<p class="empty-state">No access logs yet</p>';
            return;
        }

        let html = `
            <table class="logs-table">
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>User</th>
                        <th>Result</th>
                        <th>IP</th>
                    </tr>
                </thead>
                <tbody>
        `;

        data.logs.forEach(log => {
            const resultClass = log.result === 'success' ? 'success' : 'denied';
            html += `
                <tr>
                    <td>${log.timestamp ? formatTimestamp(log.timestamp) : '—'}</td>
                    <td>${log.viewer_email || log.viewer_uid || '—'}</td>
                    <td><span class="log-result ${resultClass}">${log.result}</span></td>
                    <td>${log.ip_address || '—'}</td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = '<p class="empty-state">Failed to load logs</p>';
    }
}
