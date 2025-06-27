// app/static/js/home.js
// home.js version: 2025-06-27-v4
console.log('home.js version: 2025-06-27-v4 loaded');

/**
 * Home.js: Logic for the home page.
 * Dependencies: common.js for formatDate.
 * Updated: 2025-06-27-v4
 * - Removed fetchRefreshStatus since home.html renders last_refresh statically.
 * - Preserved all existing functionality (full/incremental refresh buttons, date formatting).
 */

/**
 * Trigger a full refresh
 */
function triggerFullRefresh() {
    const button = document.getElementById('full-refresh-btn');
    if (!button) {
        console.warn('Full refresh button not found at ${new Date().toISOString()}');
        return;
    }
    button.disabled = true;
    button.innerText = 'Refreshing...';
    
    fetch('/refresh/full', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('Full refresh completed successfully');
            window.location.reload(); // Refresh page to update static data
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error during full refresh:', error, `at ${new Date().toISOString()}`);
        alert('Failed to perform full refresh: ' + error.message);
    })
    .finally(() => {
        button.disabled = false;
        button.innerText = 'Full Refresh';
    });
}

/**
 * Trigger an incremental refresh
 */
function triggerIncrementalRefresh() {
    const button = document.getElementById('incremental-refresh-btn');
    if (!button) {
        console.warn('Incremental refresh button not found at ${new Date().toISOString()}');
        return;
    }
    button.disabled = true;
    button.innerText = 'Refreshing...';
    
    fetch('/refresh/incremental', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('Incremental refresh completed successfully');
            window.location.reload(); // Refresh page to update static data
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error during incremental refresh:', error, `at ${new Date().toISOString()}`);
        alert('Failed to perform incremental refresh: ' + error.message);
    })
    .finally(() => {
        button.disabled = false;
        button.innerText = 'Incremental Refresh';
    });
}

/**
 * Initialize the page
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log(`home.js: DOMContentLoaded at ${new Date().toISOString()}`);
    if (typeof formatDate !== 'function') {
        console.warn('formatDate function not found, skipping date formatting at ${new Date().toISOString()}');
        return;
    }

    document.querySelectorAll('#recent-scans-table td:nth-child(3)').forEach(cell => {
        const rawDate = cell.textContent.trim();
        cell.textContent = formatDate(rawDate);
    });
});