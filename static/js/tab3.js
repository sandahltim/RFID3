console.log('tab3.js version: 2025-05-28-v16 loaded');

/**
 * Tab3.js: Logic for Tab 3 (Items in Service).
 * Dependencies: common.js for formatDate.
 * Updated 2025-05-28: Updated setupExpandCollapse for summary table expand/collapse.
 * No code removed from v15 to preserve all functionality (debounce, print tags, etc.).
 */

/**
 * Debounce function with immediate lock to prevent multiple rapid executions
 * Used by: setupPrintTagsSection for syncToPc
 */
function debounce(func, wait) {
    let timeout;
    let isProcessing = false;

    return function executedFunction(...args) {
        if (isProcessing) {
            console.log('DEBUG: Request blocked - sync already in progress');
            return;
        }

        clearTimeout(timeout);
        isProcessing = true;
        console.log('DEBUG: Setting isProcessing to true');

        timeout = setTimeout(() => {
            func(...args).finally(() => {
                isProcessing = false;
                console.log('DEBUG: Setting isProcessing to false');
            });
        }, wait);
    };
}

/**
 * Populate the common name dropdown for printing tags
 * Called on: DOMContentLoaded
 */
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

/**
 * Fetch and display CSV contents
 * Called on: DOMContentLoaded, syncToPc, removeCsvItem, updateStatusBtn
 */
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

/**
 * Handle sync to PC and status update for printing tags
 */
function setupPrintTagsSection() {
    const syncBtn = document.getElementById('syncToPcBtn');
    const updateStatusBtn = document.getElementById('updateStatusBtn');
    const syncMessage = document.getElementById('syncMessage');
    const csvContentsTable = document.getElementById('csvContentsTable');

    if (!syncBtn || !updateStatusBtn || !syncMessage || !csvContentsTable) {
        console.warn('Print tags section elements not found');
        return;
    }

    const debouncedSync = debounce(async () => {
        const commonName = document.getElementById('commonNameSelect')?.value;
        const quantity = parseInt(document.getElementById('tagQuantity')?.value) || 0;

        if (!commonName) {
            syncMessage.innerHTML = '<div class="alert alert-danger">Please select a common name.</div>';
            return;
        }
        if (quantity <= 0) {
            syncMessage.innerHTML = '<div class="alert alert-danger">Please enter a valid number of tags to print.</div>';
            return;
        }

        syncBtn.disabled = true;
        syncMessage.innerHTML = '<div class="alert alert-info">Syncing to PC...</div>';
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

            syncMessage.innerHTML = `<div class="alert alert-success">Successfully synced ${data.synced_items} items to PC.</div>`;
            console.log(`DEBUG: Sync successful, ${data.synced_items} items added`);
            fetchCsvContents();
        } catch (error) {
            console.error('Sync error:', error);
            syncMessage.innerHTML = `<div class="alert alert-danger">Error syncing to PC: ${error.message}</div>`;
        } finally {
            syncBtn.disabled = false;
        }
    }, 500);

    syncBtn.removeEventListener('click', debouncedSync);
    syncBtn.addEventListener('click', () => {
        console.log('DEBUG: Sync to PC button clicked');
        debouncedSync();
    }, { once: true });

    updateStatusBtn.addEventListener('click', async () => {
        updateStatusBtn.disabled = true;
        syncMessage.innerHTML = '<div class="alert alert-info">Updating status...</div>';

        try {
            const response = await fetch('/tab/3/update_synced_status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Status update failed with status ${response.status}`);
            }

            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }

            syncMessage.innerHTML = `<div class="alert alert-success">Successfully updated status for ${data.updated_items} items.</div>`;
            fetchCsvContents();
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        } catch (error) {
            console.error('Status update error:', error);
            syncMessage.innerHTML = `<div class="alert alert-danger">Error updating status: ${error.message}</div>`;
            updateStatusBtn.disabled = false;
        }
    }, { once: true });

    csvContentsTable.addEventListener('click', (event) => {
        const removeBtn = event.target.closest('.remove-btn');
        if (!removeBtn) return;

        const tagId = removeBtn.getAttribute('data-tag-id');
        if (!tagId) {
            console.warn('No tag_id found for remove button');
            return;
        }

        if (removeBtn.classList.contains('processing')) {
            console.log('DEBUG: Remove button already processing for tag_id:', tagId);
            return;
        }
        removeBtn.classList.add('processing');

        if (!confirm(`Are you sure you want to remove item with Tag ID ${tagId}?`)) {
            removeBtn.classList.remove('processing');
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
            syncMessage.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
            fetchCsvContents();
        })
        .catch(error => {
            console.error('Error removing item:', error);
            syncMessage.innerHTML = `<div class="alert alert-danger">Error removing item: ${error.message}</div>`;
        })
        .finally(() => {
            removeBtn.classList.remove('processing');
        });
    }, { once: false });
}

/**
 * Apply filters for Tab 3
 */
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

/**
 * Clear filters for Tab 3
 */
function clearTab3Filters() {
    window.location.href = '/tab/3';
}

/**
 * Update status button visibility
 */
function updateStatusVisibility(tagId) {
    const select = document.getElementById(`tab3-status-${tagId}`);
    const saveBtn = select.closest('tr').querySelector('.tab3-save-status-btn');
    if (!select || !saveBtn) {
        console.warn(`Status select or save button not found for tag_id: ${tagId}`);
        return;
    }
    const originalStatus = select.options[0].value;
    saveBtn.style.display = select.value !== originalStatus ? 'inline-block' : 'none';
}

/**
 * Update item status
 */
function updateStatus(tagId) {
    const newStatus = document.getElementById(`tab3-status-${tagId}`).value;

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

/**
 * Update notes button visibility
 */
function updateNotesVisibility(tagId) {
    const textarea = document.getElementById(`tab3-notes-${tagId}`);
    const saveBtn = textarea.closest('tr').querySelector('.tab3-save-notes-btn');
    if (!textarea || !saveBtn) {
        console.warn(`Notes textarea or save button not found for tag_id: ${tagId}`);
        return;
    }
    const originalNotes = textarea.dataset.originalNotes || '';
    saveBtn.style.display = textarea.value !== originalNotes ? 'inline-block' : 'none';
}

/**
 * Update item notes
 */
function updateNotes(tagId) {
    const newNotes = document.getElementById(`tab3-notes-${tagId}`).value;

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

/**
 * Handle expand/collapse functionality for summary table
 * Updated 2025-05-28: Handles expand-btn and collapse-btn for tab3-details sections
 */
function setupExpandCollapse() {
    document.addEventListener('click', (event) => {
        const expandBtn = event.target.closest('.expand-btn');
        const collapseBtn = event.target.closest('.collapse-btn');

        if (expandBtn) {
            const targetId = expandBtn.getAttribute('data-target');
            const expandable = document.getElementById(targetId);
            if (!expandable) {
                console.warn(`Expandable section not found for target: ${targetId}`);
                return;
            }

            expandable.classList.remove('collapsed');
            expandable.classList.add('expanded');
            expandBtn.style.display = 'none';
            const siblingCollapseBtn = expandBtn.parentElement.querySelector('.collapse-btn');
            if (siblingCollapseBtn) {
                siblingCollapseBtn.style.display = 'inline-block';
            }
        } else if (collapseBtn) {
            const targetId = collapseBtn.getAttribute('data-target');
            const expandable = document.getElementById(targetId);
            if (!expandable) {
                console.warn(`Expandable section not found for target: ${targetId}`);
                return;
            }

            expandable.classList.remove('expanded');
            expandable.classList.add('collapsed');
            collapseBtn.style.display = 'none';
            const siblingExpandBtn = collapseBtn.parentElement.querySelector('.expand-btn');
            if (siblingExpandBtn) {
                siblingExpandBtn.style.display = 'inline-block';
            }
        }
    });
}

/**
 * Initialize the page
 */
document.addEventListener('DOMContentLoaded', function() {
    // Format timestamps in the details tables
    document.querySelectorAll('.tab3-details-table').forEach(table => {
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const dateCell = row.querySelector('.tab3-date-last-scanned');
            if (dateCell) {
                const rawDate = dateCell.textContent.trim();
                const formattedDate = window.formatDate ? window.formatDate(rawDate) : rawDate;
                dateCell.textContent = formattedDate;
            }
        });
    });

    // Initialize save button visibility for status and notes
    document.querySelectorAll('.tab3-details-table select').forEach(select => {
        const tagId = select.id.replace('tab3-status-', '');
        updateStatusVisibility(tagId);
    });

    document.querySelectorAll('.tab3-details-table textarea').forEach(textarea => {
        const tagId = textarea.id.replace('tab3-notes-', '');
        updateNotesVisibility(tagId);
    });

    // Set up expand/collapse functionality
    setupExpandCollapse();

    // Initialize the print tags section
    populateCommonNameDropdown();
    setupPrintTagsSection();
    fetchCsvContents();
});