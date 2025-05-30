// app/static/js/home.js
console.log('home.js version: 2025-05-29-v1 loaded');

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
        if (data.status === 'Full refresh triggered successfully') {
            alert('Full refresh completed successfully');
        } else {
            alert('Error: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error during full refresh:', error);
        alert('Failed to perform full refresh');
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
        if (data.status === 'Incremental refresh triggered successfully') {
            alert('Incremental refresh completed successfully');
        } else {
            alert('Error: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error during incremental refresh:', error);
        alert('Failed to perform incremental refresh');
    })
    .finally(() => {
        button.disabled = false;
        button.innerText = 'Incremental Refresh';
    });
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('#recent-scans-table td:nth-child(3)').forEach(cell => {
        const rawDate = cell.textContent.trim();
        cell.textContent = formatDate(rawDate);
    });
});