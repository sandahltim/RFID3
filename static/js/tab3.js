console.log('tab3.js version: 2025-06-26-v25 loaded');

/**
 * Tab3.js: Logic for Tab 3 (Items in Service).
 * Dependencies: common.js for formatDate.
 * Updated: 2025-06-26-v25
 * - Ensured sections start collapsed on load.
 * - Fixed collapse button functionality with proper CSS toggling.
 * - Added crew filter dropdown (Tent Crew, Linen Crew, Service Dept).
 * - Enhanced debouncing for remove-btn (15000ms).
 * - Increased debounce wait time to 15000ms for syncToPc and updateStatusBtn.
 * - Removed duplicate event listeners by checking existing ones.
 * - Aligned DOM IDs with tab3.html v3 (crewFilter, syncToPCBtn, syncedItems).
 * - Preserved all existing functionality per user instructions.
 */

/**
 * Debounce function with immediate lock
 */
function debounce(func, wait) {
    let timeout;
    let isProcessing = false;

    return function executedFunction(...args) {
        if (isProcessing) {
            console.log(`DEBUG: Request blocked - operation already in progress at ${new Date().toISOString()}`);
            return;
        }

        clearTimeout(timeout);
        isProcessing = true;
        console.log(`DEBUG: Setting isProcessing to true at ${new Date().toISOString()}`);

        timeout = setTimeout(() => {
            func(...args).finally(() => {
                isProcessing = false;
                console.log(`DEBUG: Setting isProcessing to false at ${new Date().toISOString()}`);
            });
        }, wait);
    };
}

/**
 * Retry function for handling 429 errors
 */
async function retryRequest(url, options, maxRetries = 3, baseDelay = 2000) {
    const syncMessage = document.getElementById('syncMessage');
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            const response = await fetch(url, options);
            if (response.status === 429) {
                console.log(`DEBUG: 429 Too Many Requests on attempt ${attempt} at ${new Date().toISOString()}`);
                if (attempt === maxRetries) {
                    throw new Error(`Request failed with status 429 after ${maxRetries} retries`);
                }
                const delay = baseDelay * Math.pow(2, attempt - 1);
                console.log(`DEBUG: Waiting ${delay}ms before retry ${attempt + 1} at ${new Date().toISOString()}`);
                if (syncMessage) {
                    syncMessage.innerHTML = `<div class="alert alert-warning">Operation in progress, retrying (${attempt}/${maxRetries})...</div>`;
                }
                await new Promise(resolve => setTimeout(resolve, delay));
                continue;
            }
            return response;
        } catch (error) {
            if (attempt === maxRetries) {
                throw error;
            }
            console.error(`Attempt ${attempt} failed: ${error} at ${new Date().toISOString()}`);
        }
    }
}

/**
 * Populate the common name dropdown
 */
function populateCommonNameDropdown() {
    const select = document.getElementById('commonNameSelect');
    if (!select) {
        console.warn(`Common name dropdown not found at ${new Date().toISOString()}`);
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
            console.error(`Error fetching common names for dropdown: ${error} at ${new Date().toISOString()}`);
            select.innerHTML = '<option value="">Error loading common names</option>';
        });
}

/**
 * Populate crew filter dropdown
 */
function populateCrewFilter() {
    const select = document.getElementById('crewFilter');
    if (!select) {
        console.warn(`Crew filter dropdown not found at ${new Date().toISOString()}`);
        return;
    }

    const crews = ['All', 'Tent Crew', 'Linen Crew', 'Service Dept'];
    select.innerHTML = crews.map(crew => `<option value="${crew === 'All' ? '' : crew}">${crew}</option>`).join('');
    const urlParams = new URLSearchParams(window.location.search);
    select.value = urlParams.get('crew') || '';
}

/**
 * Fetch and display CSV contents
 */
function fetchCsvContents() {
    const tbody = document.getElementById('syncedItems');
    const updateStatusBtn = document.getElementById('updateStatusToReady');
    if (!tbody || !updateStatusBtn) {
        console.warn(`CSV contents table or update status button not found at ${new Date().toISOString()}`);
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
            console.error(`Error fetching CSV contents: ${error} at ${new Date().toISOString()}`);
            tbody.innerHTML = `<tr><td colspan="5">Error loading CSV: ${error.message}</td></tr>`;
            updateStatusBtn.disabled = true;
        });
}

/**
 * Handle sync to PC and status update
 */
function setupPrintTagsSection() {
    const syncBtn = document.getElementById('syncToPCBtn');
    const updateStatusBtn = document.getElementById('updateStatusToReady');
    const syncMessage = document.getElementById('syncMessage');
    const csvContentsTable = document.getElementById('syncedItems'); // Adjusted to match v3
    const commonNameSelect = document.getElementById('commonNameSelect');
    const tagQuantity = document.getElementById('tagCount');

    if (!syncBtn || !updateStatusBtn || !syncMessage || !csvContentsTable || !commonNameSelect || !tagQuantity) {
        console.warn(`Print tags section elements not found at ${new Date().toISOString()}`);
        return;
    }

    const debouncedSync = debounce(async () => {
        const commonName = commonNameSelect.value;
        const quantity = parseInt(tagQuantity.value) || 0;

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
        console.log(`DEBUG: Sending sync request: commonName=${commonName}, quantity=${quantity} at ${new Date().toISOString()}`);

        try {
            const response = await retryRequest('/tab/3/sync_to_pc', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    common_name: commonName,
                    quantity: quantity
                })
            }, 3, 2000);

            if (!response.ok) {
                throw new Error(`Sync failed with status ${response.status}`);
            }

            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }

            syncMessage.innerHTML = `<div class="alert alert-success">Successfully synced ${data.synced_items} items to PC.</div>`;
            console.log(`DEBUG: Sync successful, ${data.synced_items} items added at ${new Date().toISOString()}`);
            fetchCsvContents();
            commonNameSelect.value = '';
            tagQuantity.value = '';
        } catch (error) {
            console.error(`Sync error: ${error} at ${new Date().toISOString()}`);
            syncMessage.innerHTML = `<div class="alert alert-danger">Error syncing to PC: ${error.message}</div>`;
        } finally {
            syncBtn.disabled = false;
        }
    }, 15000);

    const debouncedUpdateStatus = debounce(async () => {
        updateStatusBtn.disabled = true;
        syncMessage.innerHTML = '<div class="alert alert-info">Updating status...</div>';

        try {
            const response = await retryRequest('/tab/3/update_synced_status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            }, 3, 2000);

            if (!response.ok) {
                throw new Error(`Status update failed with status ${response.status}`);
            }

            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }

            let message = `Successfully updated status for ${data.updated_items} items.`;
            if (data.failed_items && data.failed_items.length > 0) {
                message += ` Failed to update ${data.failed_items.length} items.`;
            }
            syncMessage.innerHTML = `<div class="alert alert-success">${message}</div>`;
            console.log(`DEBUG: Status update successful, ${data.updated_items} items updated at ${new Date().toISOString()}`);
            fetchCsvContents();
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        } catch (error) {
            console.error(`Status update error: ${error} at ${new Date().toISOString()}`);
            syncMessage.innerHTML = `<div class="alert alert-danger">Error updating status: ${error.message}</div>`;
            updateStatusBtn.disabled = false;
        }
    }, 15000);

    const debouncedRemove = debounce(async (tagId, removeBtn) => {
        if (!confirm(`Are you sure you want to remove item with Tag ID ${tagId}?`)) {
            return;
        }

        try {
            const response = await retryRequest('/tab/3/remove_csv_item', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ tag_id: tagId })
            }, 3, 2000);

            if (!response.ok) {
                throw new Error(`Failed to remove item: ${response.status}`);
            }

            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }

            syncMessage.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
            console.log(`DEBUG: Removed item with tag_id ${tagId} at ${new Date().toISOString()}`);
            fetchCsvContents();
        } catch (error) {
            console.error(`Error removing item: ${error} at ${new Date().toISOString()}`);
            syncMessage.innerHTML = `<div class="alert alert-danger">Error removing item: ${error.message}</div>`;
        }
    }, 15000);

    // Remove existing listeners
    syncBtn.removeEventListener('click', syncBtn._clickHandler);
    syncBtn._clickHandler = () => {
        console.log(`DEBUG: Sync to PC button clicked at ${new Date().toISOString()}`);
        debouncedSync();
    };
    syncBtn.addEventListener('click', syncBtn._clickHandler, { once: true });

    updateStatusBtn.removeEventListener('click', updateStatusBtn._clickHandler);
    updateStatusBtn._clickHandler = () => {
        console.log(`DEBUG: Update Status button clicked at ${new Date().toISOString()}`);
        debouncedUpdateStatus();
    };
    updateStatusBtn.addEventListener('click', updateStatusBtn._clickHandler, { once: true });

    csvContentsTable.removeEventListener('click', csvContentsTable._clickHandler);
    csvContentsTable._clickHandler = (event) => {
        const removeBtn = event.target.closest('.remove-btn');
        if (!removeBtn) return;

        const tagId = removeBtn.getAttribute('data-tag-id');
        if (!tagId) {
            console.warn(`No tag_id found for remove button at ${new Date().toISOString()}`);
            return;
        }

        removeBtn.classList.add('processing');
        debouncedRemove(tagId, removeBtn).finally(() => {
            removeBtn.classList.remove('processing');
        });
    };
    csvContentsTable.addEventListener('click', csvContentsTable._clickHandler);
}

/**
 * Apply filters for Tab 3
 */
function applyTab3Filters() {
    const commonName = document.getElementById('commonNameFilter')?.value || '';
    const date = document.getElementById('lastScannedFilter')?.value || '';
    const sort = document.getElementById('sortFilter')?.value || 'date_last_scanned_desc';
    const crew = document.getElementById('crewFilter')?.value || '';

    const params = new URLSearchParams();
    if (commonName) params.append('common_name', commonName);
    if (date) params.append('date_last_scanned', date);
    if (sort) params.append('sort', sort);
    if (crew) params.append('crew', crew);

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
    const saveBtn = select?.closest('tr')?.querySelector('.tab3-save-status-btn');
    if (!select || !saveBtn) {
        console.warn(`Status select or save button not found for tag_id: ${tagId} at ${new Date().toISOString()}`);
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
        console.error(`Error updating status: ${error} at ${new Date().toISOString()}`);
        alert('Failed to update status');
    });
}

/**
 * Update notes button visibility
 */
function updateNotesVisibility(tagId) {
    const textarea = document.getElementById(`tab3-notes-${tagId}`);
    const saveBtn = textarea?.closest('tr')?.querySelector('.tab3-save-notes-btn');
    if (!textarea || !saveBtn) {
        console.warn(`Notes textarea or save button not found for tag_id: ${tagId} at ${new Date().toISOString()}`);
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
        console.error(`Error updating notes: ${error} at ${new Date().toISOString()}`);
        alert('Failed to update notes');
    });
}

/**
 * Handle expand/collapse functionality for summary table
 */
function setupExpandCollapse() {
    // Initialize all expandable sections as collapsed
    document.querySelectorAll('.expandable').forEach(section => {
        section.classList.remove('expanded');
        section.classList.add('collapsed');
        section.style.display = 'none';
        section.style.opacity = '0';
        const collapseBtn = section.closest('tr').querySelector('.collapse-btn');
        const expandBtn = section.closest('tr').querySelector('.expand-btn');
        if (collapseBtn && expandBtn) {
            collapseBtn.style.display = 'none';
            expandBtn.style.display = 'inline-block';
        }
    });

    document.addEventListener('click', (event) => {
        if (window.cachedTabNum !== 3) return; // Skip for non-Tab 3 pages

        const expandBtn = event.target.closest('.expand-btn');
        const collapseBtn = event.target.closest('.collapse-btn');

        if (expandBtn) {
            const targetId = expandBtn.getAttribute('data-target-id');
            const expandable = document.getElementById(targetId);
            if (!expandable) {
                console.warn(`Expandable section not found for target: ${targetId} at ${new Date().toISOString()}`);
                return;
            }

            expandable.classList.remove('collapsed');
            expandable.classList.add('expanded');
            expandable.style.display = 'block';
            expandable.style.opacity = '1';
            expandBtn.style.display = 'none';
            const siblingCollapseBtn = expandBtn.parentElement.querySelector('.collapse-btn');
            if (siblingCollapseBtn) {
                siblingCollapseBtn.style.display = 'inline-block';
            }
        } else if (collapseBtn) {
            const targetId = collapseBtn.getAttribute('data-target-id');
            const expandable = document.getElementById(targetId);
            if (!expandable) {
                console.warn(`Expandable section not found for target: ${targetId} at ${new Date().toISOString()}`);
                return;
            }

            expandable.classList.remove('expanded');
            expandable.classList.add('collapsed');
            expandable.style.display = 'none';
            expandable.style.opacity = '0';
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
    console.log(`tab3.js: DOMContentLoaded at ${new Date().toISOString()}`);
    if (window.cachedTabNum !== 3) {
        console.log(`Skipping Tab 3 initialization for non-Tab 3 page at ${new Date().toISOString()}`);
        return;
    }

    // Format timestamps
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

    // Initialize save button visibility
    document.querySelectorAll('.tab3-details-table select').forEach(select => {
        const tagId = select.id.replace('tab3-status-', '');
        updateStatusVisibility(tagId);
    });

    document.querySelectorAll('.tab3-details-table textarea').forEach(textarea => {
        const tagId = textarea.id.replace('tab3-notes-', '');
        updateNotesVisibility(tagId);
    });

    // Set up expand/collapse
    setupExpandCollapse();

    // Initialize print tags section
    populateCommonNameDropdown();
    populateCrewFilter();
    setupPrintTagsSection();
    fetchCsvContents();
});