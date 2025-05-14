console.log('tab3.js version: 2025-05-14-v1 loaded');

// Ensure formatDate is available (from common.js)
if (typeof formatDate !== 'function') {
    console.error('formatDate function is not defined. Ensure common.js is loaded.');
    function formatDate(isoDateString) {
        return 'N/A'; // Fallback
    }
}

// Populate the common name dropdown for printing tags
function populateCommonNameDropdown() {
    const select = document.getElementById('commonNameSelect');
    if (!select) {
        console.warn('Common name dropdown not found');
        return;
    }

    fetch('/tab/3/pack_resale_common_names')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to fetch common names: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            select.innerHTML = '<option value="">Select Common Name</option>';
            data.common_names.forEach(name => {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = name;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error fetching common names for dropdown:', error);
            select.innerHTML = '<option value="">Error loading common names</option>';
        });
}

// Handle sync to PC and status update for printing tags
function setupPrintTagsSection() {
    const syncBtn = document.getElementById('syncToPcBtn');
    const updateStatusBtn = document.getElementById('updateStatusBtn');
    const syncMessage = document.getElementById('syncMessage');

    if (!syncBtn || !updateStatusBtn || !syncMessage) {
        console.warn('Print tags section elements not found');
        return;
    }

    syncBtn.addEventListener('click', () => {
        const commonName = document.getElementById('commonNameSelect')?.value;
        const quantity = parseInt(document.getElementById('tagQuantity')?.value) || 0;

        if (!commonName) {
            alert('Please select a common name.');
            return;
        }
        if (quantity <= 0) {
            alert('Please enter a valid number of tags to print.');
            return;
        }

        syncBtn.disabled = true;
        syncMessage.textContent = 'Syncing to PC...';

        fetch('/tab/3/sync_to_pc', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                common_name: commonName,
                quantity: quantity
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Sync failed with status ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            syncMessage.textContent = `Successfully synced ${data.synced_items} items to PC.`;
            updateStatusBtn.disabled = false;
        })
        .catch(error => {
            console.error('Sync error:', error);
            syncMessage.textContent = `Error syncing to PC: ${error.message}`;
        })
        .finally(() => {
            syncBtn.disabled = false;
        });
    });

    updateStatusBtn.addEventListener('click', () => {
        updateStatusBtn.disabled = true;
        syncMessage.textContent = 'Updating status...';

        fetch('/tab/3/update_synced_status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Status update failed with status ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            syncMessage.textContent = `Successfully updated status for ${data.updated_items} items.`;
            // Delay page refresh to show the confirmation message for 2 seconds
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        })
        .catch(error => {
            console.error('Status update error:', error);
            syncMessage.textContent = `Error updating status: ${error.message}`;
            updateStatusBtn.disabled = false;
        });
    });
}

function applyTab3Filters() {
    const commonName = document.getElementById('commonNameFilterTab3').value;
    const date = document.getElementById('dateFilterTab3').value;
    const sort = document.getElementById('sortFilterTab3').value;

    const params = new URLSearchParams();
    if (commonName) params.append('common_name', commonName);
    if (date) params.append('date_last_scanned', date);
    if (sort) params.append('sort', sort);

    window.location.href = `/tab/3?${params.toString()}`;
}

function clearTab3Filters() {
    window.location.href = '/tab/3';
}

function updateStatusVisibility(tagId) {
    const select = document.getElementById(`status-${tagId}`);
    const saveBtn = select.closest('tr').querySelector('.save-btn');
    if (select.value !== select.options[0].value) {
        saveBtn.style.display = 'inline-block';
    } else {
        saveBtn.style.display = 'none';
    }
}

function updateStatus(tagId) {
    const newStatus = document.getElementById(`status-${tagId}`).value;

    fetch('/tab/3/update_status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            tag_id: tagId,
            status: newStatus
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            alert(data.message);
            window.location.reload();
        }
    })
    .catch(error => {
        console.error('Error updating status:', error);
        alert('Failed to update status');
    });
}

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    // Format timestamps in the crew tables
    document.querySelectorAll('.crew-table').forEach(table => {
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const dateCell = row.querySelector('.date-last-scanned');
            if (dateCell) {
                const rawDate = dateCell.textContent.trim();
                const formattedDate = formatDate(rawDate);
                dateCell.textContent = formattedDate;
            }
        });
    });

    // Initialize save button visibility for status updates
    document.querySelectorAll('.crew-table select').forEach(select => {
        const tagId = select.id.replace('status-', '');
        updateStatusVisibility(tagId);
    });

    // Initialize the print tags section
    populateCommonNameDropdown();
    setupPrintTagsSection();
});