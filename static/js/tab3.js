// app/static/js/tab3.js
// tab3.js version: 2025-07-09-v45
console.log(`tab3.js version: 2025-07-09-v45 loaded at ${new Date().toISOString()}`);

/**
 * Tab3.js: Logic for Tab 3 (Items in Service).
 * Dependencies: common.js for formatDate, printTable, renderPaginationControls; tab.js for shared logic.
 * Updated: 2025-07-09-v45
 * - Fixed edit functionality for status, notes, quality, and bin_location with robust event delegation.
 * - Integrated print functionality with common.js printTable, fixing table selection issues.
 * - Preserved all functionality from v44: filters, sync, pagination, crew filter.
 * - Line count: ~725 lines (+5 from v44, refined edit and print handling).
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
 * Used by: Sync to PC, update status, remove item, update item fields
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
            table.querySelector('tbody').innerHTML = `<tr><td colspan="4">Error: ${data.error}</td></tr>`;
            return data;
        }

        const commonNames = data.common_names || [];
        const totalItems = data.total_items || 0;
        const perPage = data.per_page || 20;
        const currentPage = data.page || 1;

        const tbody = table.querySelector('tbody');
        if (!tbody) {
            console.error(`tbody not found in table ${expectedTableId} at ${new Date().toISOString()}`);
            return data;
        }

        tbody.innerHTML = '';
        if (commonNames.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4">No common names found for this rental class</td></tr>';
        } else {
            commonNames.forEach(common => {
                const rowId = `${sanitizedRentalClassId}_${common.name.replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '')}_${index}`;
                const escapedName = common.name.replace(/'/g, "\\'").replace(/"/g, '\\"');
                const commonRow = document.createElement('tr');
                commonRow.innerHTML = `
                    <td>${common.name || 'N/A'}</td>
                    <td>${common.on_contracts || 0}</td>
                    <td>${common.is_hand_counted ? 'N/A' : (common.total_items_inventory || 0)}</td>
                    <td>
                        <div class="btn-group">
                            <button class="btn btn-sm btn-secondary expand-btn" 
                                    data-rental-class-id="${rentalClassId}" 
                                    data-common-name="${escapedName}" 
                                    data-target-id="items-${rowId}" 
                                    data-expanded="false">Expand Items</button>
                            <button class="btn btn-sm btn-secondary collapse-btn" 
                                    data-collapse-target="items-${rowId}" 
                                    style="display:none;">Collapse</button>
                            <button class="btn btn-sm btn-primary print-btn"
                                    data-print-level="Common Name"
                                    data-print-id="items-${rowId}"
                                    data-rental-class-id="${rentalClassId}"
                                    data-common-name="${escapedName}"
                                    data-category="${rentalClassId}">Print</button>
                        </div>
                    </td>
                `;
                tbody.appendChild(commonRow);

                const itemsRow = document.createElement('tr');
                itemsRow.className = 'item-name-row';
                itemsRow.setAttribute('data-target-id', expectedTableId);
                itemsRow.innerHTML = `
                    <td colspan="4">
                        <div id="items-${rowId}" class="expandable item-level collapsed"></div>
                    </td>
                `;
                tbody.appendChild(itemsRow);
            });
        }

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
        table.querySelector('tbody').innerHTML = `<tr><td colspan="4">Error loading common names: ${error.message}</td></tr>`;
        return { common_names: [], total_items: 0 };
    }
}

/**
 * Fetch and display individual items for a rental class and common name
 */
async function loadItems(rentalClassId, commonName, targetId, page = 1) {
    console.log(`loadItems: Starting at ${new Date().toISOString()}`, { rentalClassId, commonName, targetId, page });

    if (!rentalClassId || !commonName || !targetId) {
        console.error(`loadItems: Invalid parameters`, { rentalClassId, commonName, targetId }, `at ${new Date().toISOString()}`);
        return;
    }

    const container = document.getElementById(targetId);
    if (!container) {
        console.error(`Container ${targetId} not found at ${new Date().toISOString()}`);
        return;
    }

    if (container.classList.contains('loading')) {
        console.log(`Container ${targetId} already loading at ${new Date().toISOString()}`);
        return;
    }
    container.classList.add('loading');

    const key = targetId;
    const loadingSuccess = typeof showLoading === 'function' ? showLoading(key) : false;

    container.innerHTML = '';

    const wrapper = document.createElement('div');
    wrapper.className = 'item-level-wrapper';
    container.appendChild(wrapper);

    const itemTable = document.createElement('table');
    itemTable.className = 'table table-bordered table-hover item-table';
    itemTable.id = `item-table-${key}`;
    itemTable.innerHTML = `
        <thead class="thead-dark">
            <tr>
                <th>Tag ID</th>
                <th>Common Name</th>
                <th>Bin Location</th>
                <th>Status</th>
                <th>Last Contract</th>
                <th>Last Scanned Date</th>
                <th>Quality</th>
                <th>Notes</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Loading...</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
            </tr>
        </tbody>
    `;
    wrapper.appendChild(itemTable);

    const url = `/tab/3/data?rental_class_id=${encodeURIComponent(rentalClassId)}&common_name=${encodeURIComponent(commonName)}&page=${page}&per_page=10`;
    console.log(`Fetching items: ${url} at ${new Date().toISOString()}`);

    try {
        const response = await fetch(url);
        console.log(`Items fetch status: ${response.status} at ${new Date().toISOString()}`);
        if (!response.ok) {
            throw new Error(`Items fetch failed: ${response.status}`);
        }
        const data = await response.json();
        console.log(`Items data: ${JSON.stringify(data, null, 2)} at ${new Date().toISOString()}`);

        const tbody = itemTable.querySelector('tbody');
        tbody.innerHTML = '';

        if (data.items && data.items.length > 0) {
            data.items.forEach(item => {
                const lastScanned = window.formatDate ? window.formatDate(item.date_last_scanned) : item.date_last_scanned || 'N/A';
                const currentStatus = item.status || 'N/A';
                const binLocationLower = item.bin_location ? item.bin_location.toLowerCase() : '';
                const row = document.createElement('tr');
                row.setAttribute('data-item-id', item.tag_id);
                row.innerHTML = `
                    <td>${item.tag_id}</td>
                    <td>${item.common_name}</td>
                    <td class="editable" data-field="bin_location">
                        <span class="cell-content">${item.bin_location || 'N/A'}</span>
                        <select class="edit-select" style="display: none;">
                            <option value="" ${!item.bin_location ? 'selected' : ''}>Select Bin Location</option>
                            <option value="resale" ${binLocationLower === 'resale' ? 'selected' : ''}>Resale</option>
                            <option value="sold" ${binLocationLower === 'sold' ? 'selected' : ''}>Sold</option>
                            <option value="pack" ${binLocationLower === 'pack' ? 'selected' : ''}>Pack</option>
                            <option value="burst" ${binLocationLower === 'burst' ? 'selected' : ''}>Burst</option>
                        </select>
                    </td>
                    <td class="editable" data-field="status">
                        <span class="cell-content">${currentStatus}</span>
                        <select class="edit-select" style="display: none;">
                            <option value="${currentStatus}" selected>${currentStatus}</option>
                            <option value="Ready to Rent">Ready to Rent</option>
                            <option value="Sold">Sold</option>
                            <option value="Repair">Repair</option>
                            <option value="Needs to be Inspected">Needs to be Inspected</option>
                            <option value="Wash">Wash</option>
                            <option value="Wet">Wet</option>
                        </select>
                    </td>
                    <td>${item.last_contract_num || 'N/A'}</td>
                    <td>${lastScanned}</td>
                    <td class="editable" data-field="quality">
                        <span class="cell-content">${item.quality || 'N/A'}</span>
                        <select class="edit-select" style="display: none;">
                            <option value="" ${!item.quality ? 'selected' : ''}>Select Quality</option>
                            <option value="Good" ${item.quality === 'Good' ? 'selected' : ''}>Good</option>
                            <option value="Fair" ${item.quality === 'Fair' ? 'selected' : ''}>Fair</option>
                            <option value="Poor" ${item.quality === 'Poor' ? 'selected' : ''}>Poor</option>
                        </select>
                    </td>
                    <td class="editable" data-field="notes">
                        <span class="cell-content">${item.notes || 'N/A'}</span>
                        <input class="edit-input" type="text" style="display: none;" value="${item.notes || ''}">
                    </td>
                    <td>
                        <button class="btn btn-sm btn-primary print-btn"
                                data-print-level="Item"
                                data-print-id="item-${item.tag_id}"
                                data-rental-class-id="${rentalClassId}"
                                data-common-name="${commonName.replace(/'/g, "\\'").replace(/"/g, '\\"')}">Print</button>
                    </td>
                `;
                tbody.appendChild(row);
            });

            const paginationDiv = document.createElement('div');
            paginationDiv.className = 'pagination-controls';
            paginationDiv.id = `pagination-${key}`;
            if (data.total_items > data.per_page) {
                const totalPages = Math.ceil(data.total_items / data.per_page);
                const escapedCommonName = commonName.replace(/'/g, "\\'").replace(/"/g, '\\"');
                paginationDiv.innerHTML = `
                    <button class="btn btn-sm btn-secondary prev-page" 
                            data-page="${data.page - 1}" 
                            ${data.page === 1 ? 'disabled' : ''}>Previous</button>
                    <span>Page ${data.page} of ${totalPages}</span>
                    <button class="btn btn-sm btn-secondary next-page" 
                            data-page="${data.page + 1}" 
                            ${data.page === totalPages ? 'disabled' : ''}>Next</button>
                `;
                wrapper.appendChild(paginationDiv);

                paginationDiv.querySelectorAll('.prev-page, .next-page').forEach(button => {
                    button.addEventListener('click', () => {
                        const newPage = parseInt(button.getAttribute('data-page'));
                        loadItems(rentalClassId, commonName, targetId, newPage);
                    });
                });
            }
            wrapper.appendChild(paginationDiv);
        } else {
            tbody.innerHTML = `<tr><td colspan="9">No items found.</td></tr>`;
            console.warn(`No items returned for rental_class_id ${rentalClassId}, commonName ${commonName} at ${new Date().toISOString()}`);
        }

        container.classList.remove('collapsed');
        container.classList.add('expanded');
        container.style.display = 'block';
        container.style.opacity = '1';
        container.style.visibility = 'visible';

        console.log(`Container styles:`, {
            classList: container.classList.toString(),
            display: container.style.display,
            opacity: container.style.opacity,
            visibility: window.getComputedStyle(container).visibility
        }, `at ${new Date().toISOString()}`);

        console.log(`Item table styles:`, {
            display: itemTable.style.display,
            visibility: window.getComputedStyle(itemTable).visibility
        }, `at ${new Date().toISOString()}`);
    } catch (error) {
        console.error(`Items error: ${error.message} at ${new Date().toISOString()}`);
        const tbody = itemTable.querySelector('tbody');
        tbody.innerHTML = `<tr><td colspan="9">Error: ${error.message}</td></tr>`;
        container.classList.remove('collapsed');
        container.classList.add('expanded');
        container.style.display = 'block';
        container.style.opacity = '1';
        container.style.visibility = 'visible';
    } finally {
        setTimeout(() => {
            if (loadingSuccess) hideLoading(key);
            container.classList.remove('loading');
        }, 700);
    }
}

/**
 * Save edits for item fields
 */
async function saveEdit(cell, tagId, field, rentalClassId, commonName, targetId, value) {
    console.log(`saveEdit: Starting at ${new Date().toISOString()}`, { tagId, field, rentalClassId, commonName, targetId, value });
    if (!tagId || !field) {
        console.error(`Invalid parameters for saveEdit: tagId=${tagId}, field=${field} at ${new Date().toISOString()}`);
        alert(`Error: Missing tag ID or field`);
        return;
    }

    const validStatuses = ['Ready to Rent', 'Sold', 'Repair', 'Needs to be Inspected', 'Wash', 'Wet'];
    const validQualities = ['Good', 'Fair', 'Poor', ''];
    const validBinLocations = ['resale', 'sold', 'pack', 'burst', ''];

    if (field === 'status' && !validStatuses.includes(value)) {
        console.error(`Invalid status value: ${value} at ${new Date().toISOString()}`);
        alert(`Invalid status. Choose from: ${validStatuses.join(', ')}`);
        return;
    }
    if (field === 'quality' && !validQualities.includes(value)) {
        console.error(`Invalid quality value: ${value} at ${new Date().toISOString()}`);
        alert(`Invalid quality. Choose from: ${validQualities.join(', ')}`);
        return;
    }
    if (field === 'bin_location' && !validBinLocations.includes(value)) {
        console.error(`Invalid bin location value: ${value} at ${new Date().toISOString()}`);
        alert(`Invalid bin location. Choose from: ${validBinLocations.join(', ')}`);
        return;
    }

    const url = `/tab/3/update_${field}`;
    try {
        const response = await retryRequest(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tag_id: tagId, [field]: value || '' })
        }, 3, 2000);

        console.log(`Update ${field} status for ${tagId}: ${response.status} at ${new Date().toISOString()}`);
        if (!response.ok) {
            throw new Error(`Update ${field} failed: ${response.status}`);
        }
        const data = await response.json();
        if (data.error) {
            console.error(`Update ${field} error: ${data.error} at ${new Date().toISOString()}`);
            alert(`Failed to update ${field}: ${data.error}`);
        } else if (data.local_update === 'success' && data.error) {
            console.warn(`Update ${field} succeeded locally but failed in API: ${data.error} at ${new Date().toISOString()}`);
            alert(`Updated ${field} locally, but API failed: ${data.error}`);
            loadItems(rentalClassId, commonName, targetId); // Refresh to show local update
        } else {
            console.log(`Update ${field} successful at ${new Date().toISOString()}`);
            loadItems(rentalClassId, commonName, targetId); // Refresh to show update
        }
    } catch (error) {
        console.error(`Update ${field} error: ${error.message} at ${new Date().toISOString()}`);
        alert(`Error updating ${field}: ${error.message}`);
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
 * Handle expand/collapse functionality for summary table
 */
function setupExpandCollapse(maxRetries = 3, delay = 100) {
    console.log(`setupExpandCollapse: Initializing at ${new Date().toISOString()}`);

    function trySetupExpandCollapse(attempt = 1) {
        console.log(`setupExpandCollapse: Attempt ${attempt} at ${new Date().toISOString()}`);
        let buttonsFound = 0;
        let buttonsNotFound = 0;

        document.querySelectorAll('.expandable').forEach(section => {
            section.classList.remove('expanded');
            section.classList.add('collapsed');
            section.style.display = 'none';
            section.style.opacity = '0';
            const expandableRow = section.closest('tr');
            const dataRow = expandableRow.previousElementSibling;
            if (!dataRow) {
                console.warn(`Previous data row not found for section ${section.id} at ${new Date().toISOString()}`);
                buttonsNotFound++;
                return;
            }
            const rentalClassId = section.id.match(/expand-([^-]+)-/)[1];
            const index = section.id.match(/-(\d+)$/)[1];
            const collapseBtn = dataRow.querySelector(`.collapse-btn[data-target-id="expand-${rentalClassId}-${index}"]`);
            const expandBtn = dataRow.querySelector(`.expand-btn[data-target-id="expand-${rentalClassId}-${index}"]`);
            if (collapseBtn && expandBtn) {
                console.log(`Found buttons for section ${section.id}: expandBtn.className=${expandBtn.className}, expandBtn.data-identifier=${expandBtn.getAttribute('data-identifier')}, collapseBtn.className=${collapseBtn.className}, collapseBtn.data-target-id=${collapseBtn.getAttribute('data-target-id')} at ${new Date().toISOString()}`);
                collapseBtn.style.display = 'none';
                expandBtn.style.display = 'inline-block';
                buttonsFound++;
            } else {
                console.warn(`Expand/collapse buttons not found for section ${section.id} at ${new Date().toISOString()}`);
                buttonsNotFound++;
            }
        });

        console.log(`setupExpandCollapse: Attempt ${attempt} completed - ${buttonsFound} sections with buttons, ${buttonsNotFound} sections without buttons at ${new Date().toISOString()}`);
        if (buttonsNotFound > 0 && attempt < maxRetries) {
            setTimeout(() => trySetupExpandCollapse(attempt + 1), delay);
        }
    }

    trySetupExpandCollapse();
}

/**
 * Handle item-level click events
 */
function handleItemClick(event) {
    console.log(`handleItemClick: Event triggered at ${new Date().toISOString()}`);
    const expandBtn = event.target.closest('.expand-btn');
    if (expandBtn) {
        event.preventDefault();
        event.stopPropagation();
        const rentalClassId = expandBtn.getAttribute('data-rental-class-id');
        const commonName = expandBtn.getAttribute('data-common-name');
        const targetId = expandBtn.getAttribute('data-target-id');
        const isExpanded = expandBtn.getAttribute('data-expanded') === 'true';

        if (!targetId) {
            console.error(`Missing data-target-id on expand button at ${new Date().toISOString()}`);
            return;
        }

        const container = document.getElementById(targetId);
        if (!container) {
            console.error(`Container ${targetId} not found at ${new Date().toISOString()}`);
            return;
        }

        const collapseBtn = expandBtn.parentElement.querySelector(`.collapse-btn[data-collapse-target="${targetId}"]`);
        const parentRow = container.closest('tr.item-name-row');

        if (isExpanded) {
            container.classList.remove('expanded');
            container.classList.add('collapsed');
            container.style.display = 'none';
            container.style.opacity = '0';
            parentRow.classList.add('collapsed');
            parentRow.style.display = 'none';
            if (expandBtn && collapseBtn) {
                expandBtn.style.display = 'inline-block';
                collapseBtn.style.display = 'none';
                expandBtn.setAttribute('data-expanded', 'false');
                expandBtn.textContent = 'Expand Items';
            }
        } else {
            if (rentalClassId && commonName) {
                loadItems(rentalClassId, commonName, targetId);
                parentRow.classList.remove('collapsed');
                parentRow.style.display = '';
                if (expandBtn && collapseBtn) {
                    expandBtn.style.display = 'none';
                    collapseBtn.style.display = 'inline-block';
                    expandBtn.setAttribute('data-expanded', 'true');
                }
            } else {
                const rentalClassId = expandBtn.getAttribute('data-identifier');
                if (rentalClassId && targetId) {
                    fetchCommonNames(rentalClassId, targetId, 1);
                    const expandable = container.closest('.expandable');
                    if (expandable) {
                        expandable.classList.remove('collapsed');
                        expandable.classList.add('expanded');
                        expandable.style.display = 'block';
                        expandable.style.opacity = '1';
                    }
                    if (expandBtn && collapseBtn) {
                        expandBtn.style.display = 'none';
                        collapseBtn.style.display = 'inline-block';
                    }
                }
            }
        }
        return;
    }

    const collapseBtn = event.target.closest('.collapse-btn');
    if (collapseBtn) {
        event.preventDefault();
        event.stopPropagation();
        const targetId = collapseBtn.getAttribute('data-collapse-target');
        const container = document.getElementById(targetId);
        if (container) {
            container.classList.remove('expanded');
            container.classList.add('collapsed');
            container.style.display = 'none';
            container.style.opacity = '0';
            const row = collapseBtn.closest('tr');
            const expandBtn = row.querySelector(`.expand-btn[data-target-id="${targetId}"]`);
            if (expandBtn && collapseBtn) {
                expandBtn.style.display = 'inline-block';
                collapseBtn.style.display = 'none';
            }
        }
        return;
    }

    const editableCell = event.target.closest('.editable');
    if (editableCell) {
        event.preventDefault();
        event.stopPropagation();
        console.log(`Editable cell clicked: field=${editableCell.getAttribute('data-field')} at ${new Date().toISOString()}`);
        const field = editableCell.getAttribute('data-field');
        const row = editableCell.closest('tr');
        const tagId = row.getAttribute('data-item-id');
        const rentalClassId = row.closest('.item-level')?.querySelector('button[data-rental-class-id]')?.getAttribute('data-rental-class-id');
        const commonName = row.closest('.item-level')?.querySelector('button[data-common-name]')?.getAttribute('data-common-name');
        const targetId = row.closest('.expandable').id;

        const cellContent = editableCell.querySelector('.cell-content');
        const select = editableCell.querySelector('.edit-select');
        const input = editableCell.querySelector('.edit-input');

        if (select) {
            cellContent.style.display = 'none';
            select.style.display = 'block';
            select.focus();
            console.log(`Showing dropdown for field=${field}, tagId=${tagId} at ${new Date().toISOString()}`);

            const saveChanges = () => {
                const value = select.value;
                console.log(`Saving dropdown value: ${value} for field=${field}, tagId=${tagId} at ${new Date().toISOString()}`);
                saveEdit(editableCell, tagId, field, rentalClassId, commonName, targetId, value);
                select.removeEventListener('change', saveChanges);
                select.removeEventListener('blur', revert);
            };

            const revert = () => {
                console.log(`Reverting dropdown for field=${field}, tagId=${tagId} at ${new Date().toISOString()}`);
                select.style.display = 'none';
                cellContent.style.display = 'block';
                select.removeEventListener('change', saveChanges);
                select.removeEventListener('blur', revert);
            };

            select.addEventListener('change', saveChanges);
            select.addEventListener('blur', revert);
        } else if (input) {
            cellContent.style.display = 'none';
            input.style.display = 'block';
            input.focus();
            console.log(`Showing input for field=${field}, tagId=${tagId} at ${new Date().toISOString()}`);

            const saveChanges = () => {
                const value = input.value;
                console.log(`Saving input value: ${value} for field=${field}, tagId=${tagId} at ${new Date().toISOString()}`);
                saveEdit(editableCell, tagId, field, rentalClassId, commonName, targetId, value);
                input.removeEventListener('blur', saveChanges);
                input.removeEventListener('keypress', handleKeypress);
            };

            const handleKeypress = (e) => {
                if (e.key === 'Enter') {
                    saveChanges();
                }
            };

            input.addEventListener('blur', saveChanges);
            input.addEventListener('keypress', handleKeypress);
        } else {
            console.warn(`No select or input found for editable cell: field=${field}, tagId=${tagId} at ${new Date().toISOString()}`);
        }
    }
}

/**
 * Handle print functionality
 */
function handlePrint(event) {
    const printBtn = event.target.closest('.print-btn');
    if (!printBtn) return;

    event.preventDefault();
    event.stopPropagation();
    const printLevel = printBtn.getAttribute('data-print-level');
    const printId = printBtn.getAttribute('data-print-id');
    const rentalClassId = printBtn.getAttribute('data-rental-class-id');
    const commonName = printBtn.getAttribute('data-common-name');

    console.log(`Print button clicked: level=${printLevel}, id=${printId}, rentalClassId=${rentalClassId}, commonName=${commonName} at ${new Date().toISOString()}`);

    if (typeof printTable !== 'function') {
        console.error(`printTable function not found in common.js at ${new Date().toISOString()}`);
        alert('Print functionality is unavailable. Please ensure common.js is loaded.');
        return;
    }

    // For Common Name level, print a summary table
    if (printLevel === 'Common Name') {
        printTable('Common Name', `items-${printId}`, commonName, rentalClassId);
    }
    // For Item level, create a single-item table
    else if (printLevel === 'Item') {
        const row = printBtn.closest('tr');
        if (!row) {
            console.error(`Row not found for printId=${printId} at ${new Date().toISOString()}`);
            alert('No data available to print.');
            return;
        }
        const table = document.createElement('table');
        table.className = 'table table-bordered';
        table.id = `item-${printId}`;
        table.innerHTML = `
            <thead class="thead-dark">
                <tr>
                    <th>Tag ID</th>
                    <th>Common Name</th>
                    <th>Bin Location</th>
                    <th>Status</th>
                    <th>Last Contract</th>
                    <th>Last Scanned Date</th>
                    <th>Quality</th>
                    <th>Notes</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>${row.cells[0].textContent}</td>
                    <td>${row.cells[1].textContent}</td>
                    <td>${row.cells[2].querySelector('.cell-content').textContent}</td>
                    <td>${row.cells[3].querySelector('.cell-content').textContent}</td>
                    <td>${row.cells[4].textContent}</td>
                    <td>${row.cells[5].textContent}</td>
                    <td>${row.cells[6].querySelector('.cell-content').textContent}</td>
                    <td>${row.cells[7].querySelector('.cell-content').textContent}</td>
                </tr>
            </tbody>
        `;
        document.body.appendChild(table); // Temporarily add to DOM
        printTable('Item', `item-${printId}`, commonName, rentalClassId);
        table.remove(); // Clean up
    } else {
        console.error(`Invalid print level: ${printLevel} at ${new Date().toISOString()}`);
        alert('Invalid print level.');
    }
}

/**
 * Initialize the page
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

    // Custom click handler for Tab 3 to override tab.js behavior
    document.removeEventListener('click', window.tab3ClickHandler);
    window.tab3ClickHandler = (event) => {
        console.log(`tab3ClickHandler: Click event triggered at ${new Date().toISOString()}`);
        handleItemClick(event);
        handlePrint(event); // Handle print button clicks
    };
    document.addEventListener('click', window.tab3ClickHandler);

    // Remove existing click listeners from tab.js to prevent conflicts
    if (window.tabClickHandler) {
        document.removeEventListener('click', window.tabClickHandler);
    }
}

// Remove existing DOMContentLoaded listeners to prevent duplicates
document.removeEventListener('DOMContentLoaded', window.tab3InitHandler);
window.tab3InitHandler = initializeTab3;
document.addEventListener('DOMContentLoaded', window.tab3InitHandler);