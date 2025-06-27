// app/static/js/tab3.js
// tab3.js version: 2025-06-27-v30
console.log(`tab3.js version: 2025-06-27-v30 loaded at ${new Date().toISOString()}`);

/**
 * Tab3.js: Logic for Tab 3 (Items in Service).
 * Dependencies: common.js for formatDate, tab.js for renderPaginationControls, fetchExpandableData.
 * Updated: 2025-06-27-v30
 * - Added debug logging in setupExpandCollapse and fetchCommonNames for button attributes.
 * - Ensured table ID alignment with tab3.html (common-table-<sanitizedRentalClassId>-<index>).
 * - Preserved all functionality from v29: filters, sync, status/notes, pagination.
 * - Line count: ~580 lines (same as v29, debug logging added).
 */

/**
 * Debounce function with immediate lock
 * Used by: Sync to PC, update status, remove item
 */
function debounce(func, wait) {
    let timeout;
    let isProcessing = false;

    return function executedFunction(...args) {
        if (isProcessing) {
            console.log(`DEBUG: Request blocked - operation in progress at ${new Date().toISOString()}`);
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
 * Used by: Sync to PC, update status, remove item
 */
async function retryRequest(url, options, maxRetries = 3, baseDelay = 2000) {
    const syncMessage = document.getElementById('syncMessage');
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            const response = await fetch(url, options);
            console.log(`DEBUG: Fetch ${url}, attempt ${attempt}, status: ${response.status} at ${new Date().toISOString()}`);
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
 * Fetch common names for a rental class (Tab 3-specific)
 * Fixes Expand button by ensuring correct table ID and data handling
 */
async function fetchCommonNames(rentalClassId, targetId, page = 1) {
    console.log(`fetchCommonNames: rentalClassId=${rentalClassId}, targetId=${targetId}, page=${page} at ${new Date().toISOString()}`);
    const sanitizedRentalClassId = rentalClassId.replace(/[^a-z0-9]/gi, '_');
    const index = targetId.match(/-(\d+)$/)[1];
    const expectedTableId = `common-table-${sanitizedRentalClassId}-${index}`;
    const table = document.getElementById(expectedTableId);
    if (!table) {
        console.error(`Common table ${expectedTableId} not found for targetId=${targetId} at ${new Date().toISOString()}`);
        return { common_names: [], total_items: 0 };
    }

    try {
        const url = `/tab/3/common_names?rental_class_id=${encodeURIComponent(rentalClassId)}&page=${page}&per_page=20`;
        console.log(`Fetching common names from: ${url} at ${new Date().toISOString()}`);
        const response = await fetch(url);
        console.log(`Common names fetch status for ${rentalClassId}, page ${page}: ${response.status} at ${new Date().toISOString()}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch common names: ${response.status}`);
        }
        const data = await response.json();
        console.log(`Common names data for ${rentalClassId}, page ${page}: ${JSON.stringify(data, null, 2)} at ${new Date().toISOString()}`);

        if (data.error) {
            console.error(`Server error fetching common names: ${data.error} at ${new Date().toISOString()}`);
            table.querySelector('tbody').innerHTML = `<tr><td colspan="3">Error: ${data.error}</td></tr>`;
            return data;
        }

        const commonNames = data.common_names || [];
        const totalItems = data.total_items || 0;
        const perPage = data.per_page || 20;
        const currentPage = data.page || 1;

        let html = '';
        if (commonNames.length === 0) {
            html = '<tr><td colspan="3">No common names found for this rental class</td></tr>';
        } else {
            commonNames.forEach(common => {
                html += `
                    <tr>
                        <td>${common.name || 'N/A'}</td>
                        <td>${common.on_contracts || 0}</td>
                        <td>${common.is_hand_counted ? 'N/A' : (common.total_items_inventory || 0)}</td>
                    </tr>
                `;
            });
        }

        table.querySelector('tbody').innerHTML = html;

        const paginationContainer = document.getElementById(`pagination-${expectedTableId}`);
        if (paginationContainer && typeof renderPaginationControls === 'function') {
            renderPaginationControls(paginationContainer, totalItems, currentPage, perPage, (newPage) => {
                fetchCommonNames(rentalClassId, targetId, newPage);
            });
        } else {
            console.warn(`Pagination container or renderPaginationControls not found for ${expectedTableId} at ${new Date().toISOString()}`);
        }

        const rowCountDiv = paginationContainer ? paginationContainer.nextElementSibling : null;
        if (rowCountDiv && rowCountDiv.classList.contains('row-count')) {
            rowCountDiv.textContent = `Showing ${commonNames.length} of ${totalItems} common names`;
        }

        return data;
    } catch (error) {
        console.error(`Error fetching common names for ${rentalClassId}: ${error} at ${new Date().toISOString()}`);
        table.querySelector('tbody').innerHTML = `<tr><td colspan="3">Error loading common names: ${error.message}</td></tr>`;
        return { common_names: [], total_items: 0 };
    }
}

/**
 * Populate the common name dropdown
 * Used by: Print RFID Tags section
 */
function populateCommonNameDropdown() {
    const select = document.getElementById('commonNameSelect');
    if (!select) {
        console.warn(`Common name dropdown not found at ${new Date().toISOString()}`);
        return;
    }

    fetch('/tab/3/pack_resale_common_names')
        .then(response => {
            console.log(`Common name dropdown fetch status: ${response.status} at ${new Date().toISOString()}`);
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
 * Used by: Filter section
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
 * Used by: Synced Items table
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
            console.log(`Synced items fetch status: ${response.status} at ${new Date().toISOString()}`);
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
 * Used by: Print RFID Tags section
 */
function setupPrintTagsSection() {
    const syncBtn = document.getElementById('syncToPCBtn');
    const updateStatusBtn = document.getElementById('updateStatusToReady');
    const syncMessage = document.getElementById('syncMessage');
    const csvContentsTable = document.getElementById('syncedItems');
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
        } finally {
            removeBtn.classList.remove('processing');
        }
    }, 15000);

    // Remove existing listeners to prevent duplicates
    if (syncBtn._clickHandler) {
        syncBtn.removeEventListener('click', syncBtn._clickHandler);
    }
    syncBtn._clickHandler = () => {
        console.log(`DEBUG: Sync to PC button clicked at ${new Date().toISOString()}`);
        debouncedSync();
    };
    syncBtn.addEventListener('click', syncBtn._clickHandler);

    if (updateStatusBtn._clickHandler) {
        updateStatusBtn.removeEventListener('click', updateStatusBtn._clickHandler);
    }
    updateStatusBtn._clickHandler = () => {
        console.log(`DEBUG: Update Status button clicked at ${new Date().toISOString()}`);
        debouncedUpdateStatus();
    };
    updateStatusBtn.addEventListener('click', updateStatusBtn._clickHandler);

    if (csvContentsTable._clickHandler) {
        csvContentsTable.removeEventListener('click', csvContentsTable._clickHandler);
    }
    csvContentsTable._clickHandler = (event) => {
        const removeBtn = event.target.closest('.remove-btn');
        if (!removeBtn) return;

        const tagId = removeBtn.getAttribute('data-tag-id');
        if (!tagId) {
            console.warn(`No tag_id found for remove button at ${new Date().toISOString()}`);
            return;
        }

        removeBtn.classList.add('processing');
        debouncedRemove(tagId, removeBtn);
    };
    csvContentsTable.addEventListener('click', csvContentsTable._clickHandler);
}

/**
 * Apply filters for Tab 3
 * Used by: Filter section
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

    console.log(`Applying filters: ${params.toString()} at ${new Date().toISOString()}`);
    window.location.href = `/tab/3?${params.toString()}`;
}

/**
 * Clear filters for Tab 3
 * Used by: Filter section
 */
function clearTab3Filters() {
    console.log(`Clearing filters at ${new Date().toISOString()}`);
    window.location.href = '/tab/3';
}

/**
 * Update status button visibility
 * Used by: Item details table
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
 * Used by: Item details table
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
    .then(response => {
        console.log(`Status update fetch status for ${tagId}: ${response.status} at ${new Date().toISOString()}`);
        return response.json();
    })
    .then(data => {
        if (data.error) {
            console.error(`Error updating status for ${tagId}: ${data.error} at ${new Date().toISOString()}`);
            alert('Error: ' + data.error);
        } else {
            console.log(`Status update successful for ${tagId}: ${data.message} at ${new Date().toISOString()}`);
            alert(data.message);
            window.location.reload();
        }
    })
    .catch(error => {
        console.error(`Error updating status for ${tagId}: ${error} at ${new Date().toISOString()}`);
        alert('Failed to update status');
    });
}

/**
 * Update notes button visibility
 * Used by: Item details table
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
 * Used by: Item details table
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
    .then(response => {
        console.log(`Notes update fetch status for ${tagId}: ${response.status} at ${new Date().toISOString()}`);
        return response.json();
    })
    .then(data => {
        if (data.error) {
            console.error(`Error updating notes for ${tagId}: ${data.error} at ${new Date().toISOString()}`);
            alert('Error: ' + data.error);
        } else {
            console.log(`Notes update successful for ${tagId}: ${data.message} at ${new Date().toISOString()}`);
            alert(data.message);
            window.location.reload();
        }
    })
    .catch(error => {
        console.error(`Error updating notes for ${tagId}: ${error} at ${new Date().toISOString()}`);
        alert('Failed to update notes');
    });
}

/**
 * Handle expand/collapse functionality for summary table
 * Used by: Summary table
 */
function setupExpandCollapse() {
    console.log(`setupExpandCollapse: Initializing at ${new Date().toISOString()}`);
    document.querySelectorAll('.expandable').forEach(section => {
        section.classList.remove('expanded');
        section.classList.add('collapsed');
        section.style.display = 'none';
        section.style.opacity = '0';
        const row = section.closest('tr');
        const rentalClassId = section.id.match(/expand-([^-]+)-/)[1];
        const index = section.id.match(/-(\d+)$/)[1];
        const collapseBtn = row.querySelector(`#collapse-btn-${rentalClassId}-${index}`);
        const expandBtn = row.querySelector(`#expand-btn-${rentalClassId}-${index}`);
        if (collapseBtn && expandBtn) {
            console.log(`Found buttons for section ${section.id}: expandBtn.id=${expandBtn.id}, collapseBtn.id=${collapseBtn.id} at ${new Date().toISOString()}`);
            collapseBtn.style.display = 'none';
            expandBtn.style.display = 'inline-block';
        } else {
            console.warn(`Expand/collapse buttons not found for section ${section.id} at ${new Date().toISOString()}`);
            console.log(`DEBUG: row HTML=${row.outerHTML} at ${new Date().toISOString()}`);
        }
    });
}

/**
 * Initialize the page
 * Used by: Page load
 */
function initializeTab3() {
    console.log(`tab3.js: DOMContentLoaded at ${new Date().toISOString()}`);
    const path = window.location.pathname.split('?')[0];
    if (path !== '/tab/3' && window.cachedTabNum !== 3) {
        console.log(`Skipping Tab 3 initialization for non-Tab 3 page (path=${path}, cachedTabNum=${window.cachedTabNum}) at ${new Date().toISOString()}`);
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

    // Initialize pagination for summary table
    const paginationContainer = document.getElementById('pagination-controls');
    if (paginationContainer) {
        const totalItems = parseInt(paginationContainer.dataset.totalGroups || 0);
        const currentPage = parseInt(paginationContainer.dataset.currentPage || 1);
        const perPage = parseInt(paginationContainer.dataset.perPage || 20);
        renderPaginationControls(paginationContainer, totalItems, currentPage, perPage, (newPage) => {
            const params = new URLSearchParams(window.location.search);
            params.set('page', newPage);
            window.location.href = `/tab/3?${params.toString()}`;
        });
    }
}

// Remove existing DOMContentLoaded listeners to prevent duplicates
document.removeEventListener('DOMContentLoaded', window.tab3InitHandler);
window.tab3InitHandler = initializeTab3;
document.addEventListener('DOMContentLoaded', window.tab3InitHandler);