console.log('tab3.js version: 2025-05-21-v11 loaded');

// Debounce function with locking mechanism to prevent multiple rapid clicks
function debounce(func, wait) {
    let timeout;
    let isProcessing = false; // Lock to prevent concurrent requests

    return function executedFunction(...args) {
        if (isProcessing) {
            console.log('DEBUG: Request blocked - sync already in progress');
            return;
        }

        isProcessing = true;
        console.log('DEBUG: Setting isProcessing to true');

        const later = () => {
            clearTimeout(timeout);
            func(...args).finally(() => {
                isProcessing = false;
                console.log('DEBUG: Setting isProcessing to false');
            });
        };

        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
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

// Fetch and display CSV contents
function fetchCsvContents() {
    const tbody = document.getElementById('csvContentsBody');
    const updateStatusBtn = document.getElementById('updateStatusBtn');
    if (!tbody || !updateStatusBtn) {
        console.warn('CSV contents table or update status button not found');
        return;
    }

    fetch('/tab/3/csv_contents')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to fetch CSV contents: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            tbody.innerHTML = '';
            if (data.error) {
                tbody.innerHTML = `<tr><td colspan="5">${data.error}</td></tr>`;
                updateStatusBtn.disabled = true;
                return;
            }

            if (data.items.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5">No items in CSV</td></tr>';
                updateStatusBtn.disabled = true;
            } else {
                data.items.forEach(item => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${item.tag_id}</td>
                        <td>${item.common_name}</td>
                        <td>${item.status}</td>
                        <td>${item.bin_location}</td>
                        <td>
                            <button class="btn btn-sm btn-danger remove-btn" data-tag-id="${item.tag_id}">Remove</button>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
                updateStatusBtn.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error fetching CSV contents:', error);
            tbody.innerHTML = `<tr><td colspan="5">Error loading CSV: ${error.message}</td></tr>`;
            updateStatusBtn.disabled = true;
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

    // Debounced sync function to prevent multiple requests
    const debouncedSync = debounce(async () => {
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
        console.log(`DEBUG: Sending sync request: commonName=${commonName}, quantity=${quantity}`);

        try {
            const response = await fetch('/tab/3/sync_to_pc', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    common_name: commonName,
                    quantity: quantity
                })
            });

            if (!response.ok) {
                throw new Error(`Sync failed with status ${response.status}`);
            }

            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }

            syncMessage.textContent = `Successfully synced ${data.synced_items} items to PC.`;
            console.log(`DEBUG: Sync successful, ${data.synced_items} items added`);
            fetchCsvContents();
        } catch (error) {
            console.error('Sync error:', error);
            syncMessage.textContent = `Error syncing to PC: ${error.message}`;
        } finally {
            syncBtn.disabled = false;
        }
    }, 500);

    syncBtn.addEventListener('click', () => {
        console.log('DEBUG: Sync to PC button clicked');
        debouncedSync();
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
            fetchCsvContents();
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

    // Handle remove buttons
    document.getElementById('csvContentsTable').addEventListener('click', (event) => {
        const removeBtn = event.target.closest('.remove-btn');
        if (!removeBtn) return;

        const tagId = removeBtn.getAttribute('data-tag-id');
        if (!tagId) {
            console.warn('No tag_id found for remove button');
            return;
        }

        if (!confirm(`Are you sure you want to remove item with Tag ID ${tagId}?`)) {
            return;
        }

        fetch('/tab/3/remove_csv_item', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ tag_id: tagId })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to remove item: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            syncMessage.textContent = data.message;
            fetchCsvContents();
        })
        .catch(error => {
            console.error('Error removing item:', error);
            syncMessage.textContent = `Error removing item: ${error.message}`;
        });
    });
}

// Apply filters for Tab 3
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

// Clear filters for Tab 3
function clearTab3Filters() {
    window.location.href = '/tab/3';
}

// Update status button visibility
function updateStatusVisibility(tagId) {
    const select = document.getElementById(`status-${tagId}`);
    const saveBtn = select.closest('tr').querySelector('.save-status-btn');
    if (!select || !saveBtn) {
        console.warn(`Status select or save button not found for tag_id: ${tagId}`);
        return;
    }
    const originalStatus = select.options[0].value;
    saveBtn.style.display = select.value !== originalStatus ? 'inline-block' : 'none';
}

// Update item status
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

// Update notes button visibility
function updateNotesVisibility(tagId) {
    const textarea = document.getElementById(`notes-${tagId}`);
    const saveBtn = textarea.closest('tr').querySelector('.save-notes-btn');
    if (!textarea || !saveBtn) {
        console.warn(`Notes textarea or save button not found for tag_id: ${tagId}`);
        return;
    }
    const originalNotes = textarea.dataset.originalNotes || '';
    saveBtn.style.display = textarea.value !== originalNotes ? 'inline-block' : 'none';
}

// Update item notes
function updateNotes(tagId) {
    const newNotes = document.getElementById(`notes-${tagId}`).value;

    fetch('/tab/3/update_notes', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            tag_id: tagId,
            notes: newNotes
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
        console.error('Error updating notes:', error);
        alert('Failed to update notes');
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

    // Initialize save button visibility for status and notes
    document.querySelectorAll('.crew-table select').forEach(select => {
        const tagId = select.id.replace('status-', '');
        updateStatusVisibility(tagId);
    });

    document.querySelectorAll('.crew-table textarea').forEach(textarea => {
        const tagId = textarea.id.replace('notes-', '');
        updateNotesVisibility(tagId);
    });

    // Initialize the print tags section
    populateCommonNameDropdown();
    setupPrintTagsSection();
    fetchCsvContents();
});