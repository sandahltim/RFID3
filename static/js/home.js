// app/static/js/home.js version: 2025-06-19-v2
console.log('home.js version: 2025-06-19-v2 loaded');

function triggerFullRefresh() {
    const button = document.getElementById('full-refresh-btn');
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
            fetchRefreshStatus();
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error during full refresh:', error);
        alert('Failed to perform full refresh: ' + error.message);
    })
    .finally(() => {
        button.disabled = false;
        button.innerText = 'Full Refresh';
    });
}

function triggerIncrementalRefresh() {
    const button = document.getElementById('incremental-refresh-btn');
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
            fetchRefreshStatus();
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error during incremental refresh:', error);
        alert('Failed to perform incremental refresh: ' + error.message);
    })
    .finally(() => {
        button.disabled = false;
        button.innerText = 'Incremental Refresh';
    });
}

async function fetchRefreshStatus() {
    try {
        const response = await fetch('/refresh/status');
        const data = await response.json();
        if (data.status === 'success') {
            document.getElementById('refresh-status').innerText = 
                `Last Refresh: ${data.last_refresh} (${data.refresh_type})`;
        } else {
            console.error('Error fetching refresh status:', data.message);
        }
    } catch (error) {
        console.error('Error fetching refresh status:', error);
        document.getElementById('refresh-status').innerText = 'Last Refresh: Error fetching status';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (typeof formatDate === 'function') {
        document.querySelectorAll('#recent-scans-table td:nth-child(3)').forEach(cell => {
            const rawDate = cell.textContent.trim();
            cell.textContent = formatDate(rawDate);
        });
    } else {
        console.warn('formatDate function not found, skipping date formatting');
    }
    fetchRefreshStatus();
});