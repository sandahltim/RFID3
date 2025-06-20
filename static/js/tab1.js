console.log('tab1.js version: 2025-05-29-v11 loaded');

/**
 * Tab1.js: Logic for Tab 1 (Rental Inventory).
 * Dependencies: common.js (for formatDate, showLoading, hideLoading, collapseSection, printTable, printFullItemList).
 * Note: Split from tab1_5.js; removed Tab 5-specific functions (bulk updates).
 * Updated: Pre-populate subcategory dropdowns on load, show common names on selection.
 */

/**
 * Apply filter with retry mechanism
 */
function applyFilterWithRetryTab1(tableId, tableType, retries = 10, delay = 200) {
    console.log(`applyFilterWithRetryTab1: tableId=${tableId}, tableType=${tableType}, retries=${retries}`);
    const table = document.getElementById(tableId);
    if (table && typeof applyFilterToAllLevelsTab1 === 'function') {
        applyFilterToAllLevelsTab1();
        console.log(`Filter applied for ${tableId} (${tableType})`);
    } else if (retries > 0) {
        console.log(`Table ${tableId} (${tableType}) not ready, retrying (${retries} attempts left)`);
        setTimeout(() => applyFilterWithRetryTab1(tableId, tableType, retries - 1, delay), delay);
    } else {
        console.warn(`Failed to apply filter for ${tableId} (${tableType}): Table not found after retries`);
    }
}

/**
 * Apply filter to all levels (category, subcategory, common names, items)
 * Specific to Tab 1, does not use globalFilter
 */
function applyFilterToAllLevelsTab1() {
    console.log('applyFilterToAllLevelsTab1: Starting');
    try {
        const categoryFilter = document.getElementById('category-filter')?.value.toLowerCase() || '';
        const statusFilter = document.getElementById('statusFilter')?.value.toLowerCase() || '';
        const binFilter = document.getElementById('binFilter')?.value.toLowerCase() || '';
        console.log(`Filters: category=${categoryFilter}, status=${statusFilter}, bin=${binFilter}`);

        const categoryRows = document.querySelectorAll('#category-table tbody tr:not(.common-name-row)');
        console.log(`Found ${categoryRows.length} category rows`);

        let visibleRows = 0;
        categoryRows.forEach(row => {
            const category = row.cells[0]?.textContent.toLowerCase() || '';
            const matchesCategory = category.includes(categoryFilter);
            const matchesStatus = !statusFilter || row.cells[3]?.textContent.toLowerCase() !== '0' || row.cells[4]?.textContent.toLowerCase() !== '0';
            const matchesBin = !binFilter;

            if (matchesCategory && matchesStatus && matchesBin) {
                row.style.display = '';
                visibleRows++;
            } else {
                row.style.display = 'none';
                const targetId = `common-${category.toLowerCase().replace(/[^a-z0-9]/g, '_')}`;
                const container = document.getElementById(targetId);
                if (container) {
                    container.innerHTML = '';
                }
            }
        });

        const commonTables = document.querySelectorAll('.common-table');
        console.log(`Found ${commonTables.length} common tables`);
        commonTables.forEach(table => {
            const category = table.closest('tr.common-name-row')?.previousElementSibling?.cells[0]?.textContent.toLowerCase().replace(/[^a-z0-9]/g, '_') || '';
            if (!category) {
                console.warn('Category not found for common table');
                return;
            }
            const matchesCategory = category.includes(categoryFilter);
            if (!matchesCategory) {
                table.closest('tr.common-name-row').style.display = 'none';
            } else {
                table.closest('tr.common-name-row').style.display = '';
            }
        });

        const itemTables = document.querySelectorAll('.item-table');
        console.log(`Found ${itemTables.length} item tables`);
        itemTables.forEach(table => {
            const category = table.closest('tr.common-name-row')?.previousElementSibling?.cells[0]?.textContent.toLowerCase().replace(/[^a-z0-9]/g, '_') || '';
            if (!category) {
                console.warn('Category not found for item table');
                return;
            }
            const matchesCategory = category.includes(categoryFilter);
            if (!matchesCategory) {
                table.closest('tr.common-name-row').style.display = 'none';
            } else {
                table.closest('tr.common-name-row').style.display = '';
            }
        });

        const rowCountDiv = document.getElementById('row-count');
        if (rowCountDiv) {
            rowCountDiv.textContent = `Showing ${visibleRows} categories`;
        }
    } catch (error) {
        console.error('Error applying filters:', error.message);
    }
}

/**
 * Populate subcategories for all dropdowns
 */
function populateSubcategories() {
    console.log('populateSubcategories: Starting');
    const selects = document.querySelectorAll('.subcategory-select');
    console.log(`Found ${selects.length} subcategory selects`);
    selects.forEach(select => {
        const category = select.getAttribute('data-category');
        console.log(`Populating subcategories for category: ${category}`);
        const url = `/tab/1/subcat_data?category=${encodeURIComponent(category)}`;
        fetch(url)
            .then(response => {
                console.log(`Subcategory fetch status for ${category}: ${response.status}`);
                if (!response.ok) {
                    return response.text().then(text => {
                        throw new Error(`Subcategory fetch failed: ${response.status} - ${text}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                console.log(`Subcategory data for ${category}:`, data);
                select.innerHTML = '<option value="">Select a subcategory</option>';
                if (data.subcategories && data.subcategories.length > 0) {
                    data.subcategories.forEach(subcat => {
                        const option = document.createElement('option');
                        option.value = subcat.subcategory;
                        option.textContent = subcat.subcategory;
                        select.appendChild(option);
                    });
                    // Ensure "Concession Resale" is included if present
                    if (!Array.from(select.options).some(opt => opt.value === "Concession Resale") && data.subcategories.some(subcat => subcat.subcategory === "Concession Resale")) {
                        const option = document.createElement('option');
                        option.value = "Concession Resale";
                        option.textContent = "Concession Resale";
                        select.appendChild(option);
                    }
                } else {
                    select.innerHTML += '<option value="">No subcategories</option>';
                }
            })
            .catch(error => {
                console.error(`Subcategory error for ${category}:`, error.message);
                select.innerHTML = '<option value="">Error loading subcategories</option>';
            });
    });
}

/**
 * Load common names when a subcategory is selected
 */
function loadCommonNames(selectElement, page = 1) {
    console.log('loadCommonNames: Starting', { page });
    const subcategory = selectElement.value;
    const category = selectElement.getAttribute('data-category');
    const targetId = `common-${category.toLowerCase().replace(/[^a-z0-9]/g, '_')}`;
    const categoryRow = selectElement.closest('tr');
    const tbody = categoryRow.closest('tbody');

    console.log('loadCommonNames:', { subcategory, category, targetId, page });

    // Clear the common names section if no subcategory is selected
    const container = document.getElementById(targetId);
    if (!subcategory) {
        console.log('No subcategory, clearing common names');
        if (container) {
            container.innerHTML = '';
        }
        return;
    }

    if (!category || !subcategory || !targetId) {
        console.error('loadCommonNames: Invalid parameters', { category, subcategory, targetId });
        return;
    }

    const loadingId = `loading-subcat-${targetId}`;
    const loadingDiv = document.getElementById(loadingId);
    if (loadingDiv) loadingDiv.style.display = 'block';

    const url = `/tab/1/common_names?category=${encodeURIComponent(category)}&subcategory=${encodeURIComponent(subcategory)}&page=${page}`;
    console.log(`Fetching common names: ${url}`);

    fetch(url)
        .then(response => {
            console.log(`Common names fetch status: ${response.status}`);
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`Common names fetch failed: ${response.status} - ${text}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Common names data:', data);

            // Create or update the common names section
            let commonRow = categoryRow.parentNode.querySelector(`tr.common-name-row[data-target-id="${targetId}"]`);
            if (!commonRow) {
                commonRow = document.createElement('tr');
                commonRow.className = 'common-name-row';
                commonRow.setAttribute('data-target-id', targetId);
                commonRow.innerHTML = `
                    <td colspan="7">
                        <div id="${targetId}" class="common-level"></div>
                    </td>
                `;
                tbody.insertBefore(commonRow, categoryRow.nextSibling);
            }

            const container = document.getElementById(targetId);
            container.innerHTML = `
                <table class="common-table" id="common-table-${targetId}" style="color: #000000 !important;">
                    <thead>
                        <tr>
                            <th style="color: #000000 !important;">Common Name</th>
                            <th style="color: #000000 !important;">Total Items</th>
                            <th style="color: #000000 !important;">Items on Contracts</th>
                            <th style="color: #000000 !important;">Items in Service</th>
                            <th style="color: #000000 !important;">Items Available</th>
                            <th style="color: #000000 !important;">Actions</th>
                        </tr>
                    </thead>
                    <tbody style="min-height: 50px;">
                        ${data.common_names && data.common_names.length > 0 ? 
                            data.common_names.map(item => {
                                const rowId = `${targetId}_${item.name.replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '')}`;
                                const escapedName = item.name.replace(/'/g, "\\'").replace(/"/g, '\\"');
                                return `
                                    <tr>
                                        <td style="color: #000000 !important;">${item.name}</td>
                                        <td style="color: #000000 !important;">${item.total_items || '0'}</td>
                                        <td style="color: #000000 !important;">${item.items_on_contracts || '0'}</td>
                                        <td style="color: #000000 !important;">${item.items_in_service || '0'}</td>
                                        <td style="color: #000000 !important;">${item.items_available || '0'}</td>
                                        <td>
                                            <div class="btn-group">
                                                <button class="btn btn-sm btn-secondary expand-items-btn" 
                                                        data-category="${category}" 
                                                        data-subcategory="${subcategory}" 
                                                        data-common-name="${escapedName}" 
                                                        data-target-id="items-${rowId}">Expand Items</button>
                                                <button class="btn btn-sm btn-secondary collapse-items-btn" 
                                                        data-collapse-target="items-${rowId}" 
                                                        style="display:none;">Collapse Items</button>
                                                <button class="btn btn-sm btn-info print-btn" 
                                                        data-print-level="Common Name" 
                                                        data-print-id="common-table-${targetId}" 
                                                        data-common-name="${escapedName}" 
                                                        data-category="${category}" 
                                                        data-subcategory="${subcategory}">Print Aggregate</button>
                                                <button class="btn btn-sm btn-info print-full-btn" 
                                                        data-common-name="${escapedName}" 
                                                        data-category="${category}" 
                                                        data-subcategory="${subcategory}">Print Full List</button>
                                            </div>
                                        </td>
                                    </tr>
                                    <tr class="common-name-row" data-target-id="${targetId}">
                                        <td colspan="7">
                                            <div id="items-${rowId}" class="item-level"></div>
                                        </td>
                                    </tr>
                                `;
                            }).join('') : 
                            '<tr><td colspan="7">No common names found.</td></tr>'}
                    </tbody>
                </table>
            `;

            // Add pagination if needed
            if (data.total_common_names > data.per_page) {
                const totalPages = Math.ceil(data.total_common_names / data.per_page);
                const paginationDiv = document.createElement('div');
                paginationDiv.className = 'pagination-controls';
                paginationDiv.innerHTML = `
                    <button class="btn btn-sm btn-secondary" 
                            onclick="loadCommonNames(document.querySelector('select[data-category=\"${category}\"]'), ${data.page - 1})" 
                            ${data.page === 1 ? 'disabled' : ''}>Previous</button>
                    <span>Page ${data.page} of ${totalPages}</span>
                    <button class="btn btn-sm btn-secondary" 
                            onclick="loadCommonNames(document.querySelector('select[data-category=\"${category}\"]'), ${data.page + 1})" 
                            ${data.page === totalPages ? 'disabled' : ''}>Next</button>
                `;
                container.appendChild(paginationDiv);
            }

            // Update category totals
            if (data.common_names && data.common_names.length > 0) {
                const totals = {
                    totalItems: data.common_names.reduce((sum, item) => sum + (item.total_items || 0), 0),
                    itemsOnContracts: data.common_names.reduce((sum, item) => sum + (item.items_on_contracts || 0), 0),
                    itemsInService: data.common_names.reduce((sum, item) => sum + (item.items_in_service || 0), 0),
                    itemsAvailable: data.common_names.reduce((sum, item) => sum + (item.items_available || 0), 0)
                };
                console.log('Common name totals:', totals);
                categoryRow.cells[2].textContent = totals.totalItems || '0';
                categoryRow.cells[3].textContent = totals.itemsOnContracts || '0';
                categoryRow.cells[4].textContent = totals.itemsInService || '0';
                categoryRow.cells[5].textContent = totals.itemsAvailable || '0';
            }

            applyFilterWithRetryTab1(`common-table-${targetId}`, 'common');
        })
        .catch(error => {
            console.error('Common names error:', error.message);
            container.innerHTML = `<p>Error: ${error.message}</p>`;
        })
        .finally(() => {
            setTimeout(() => {
                if (loadingDiv) loadingDiv.style.display = 'none';
            }, 700);
        });
}

/**
 * Load items when "Expand Items" is clicked
 */
function loadItems(category, subcategory, commonName, targetId, page = 1) {
    console.log('loadItems:', { category, subcategory, commonName, targetId, page });

    if (!category || !subcategory || !commonName || !targetId) {
        console.error('loadItems: Invalid parameters', { category, subcategory, commonName, targetId });
        return;
    }

    const container = document.getElementById(targetId);
    if (!container) {
        console.error(`Container ${targetId} not found`);
        return;
    }

    if (container.classList.contains('loading')) {
        console.log(`Container ${targetId} already loading`);
        return;
    }
    container.classList.add('loading');

    const key = targetId;
    const loadingSuccess = showLoading(key);

    // Clear existing content to prevent duplicates
    container.innerHTML = '';

    const wrapper = document.createElement('div');
    wrapper.className = 'item-level-wrapper';
    container.appendChild(wrapper);

    const itemTable = document.createElement('table');
    itemTable.className = 'item-table';
    itemTable.id = `item-table-${key}`;
    itemTable.style.color = '#000000 !important';
    itemTable.innerHTML = `
        <thead>
            <tr>
                <th style="color: #000000 !important;">Tag ID</th>
                <th style="color: #000000 !important;">Common Name</th>
                <th style="color: #000000 !important;">Bin Location</th>
                <th style="color: #000000 !important;">Status</th>
                <th style="color: #000000 !important;">Last Contract</th>
                <th style="color: #000000 !important;">Last Scanned Date</th>
                <th style="color: #000000 !important;">Quality</th>
                <th style="color: #000000 !important;">Notes</th>
            </tr>
        </thead>
        <tbody style="min-height: 50px;">
            <tr>
                <td style="color: #000000 !important;">Loading...</td>
                <td style="color: #000000 !important;">-</td>
                <td>-</td>
                <td>-</td>
                <td style="color: #000000 !important;">-</td>
                <td style="color: #000000 !important;">-</td>
                <td style="color: #000000 !important;">-</td>
                <td style="color: #000000 !important;">-</td>
            </tr>
        </tbody>
    `;
    wrapper.appendChild(itemTable);

    const url = `/tab/1/data?common_name=${encodeURIComponent(commonName)}&page=${page}&subcategory=${encodeURIComponent(subcategory)}&category=${encodeURIComponent(category)}`;
    console.log(`Fetching items: ${url}`);

    fetch(url)
        .then(response => {
            console.log(`Items fetch status: ${response.status}`);
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`Items fetch failed: ${response.status} - ${text}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Items data:', data);
            const tbody = itemTable.querySelector('tbody');
            tbody.innerHTML = '';

            if (data.items && data.items.length > 0) {
                data.items.forEach(item => {
                    const lastScanned = formatDate(item.last_scanned_date);
                    const row = document.createElement('tr');
                    row.setAttribute('data-item-id', item.tag_id);
                    row.innerHTML = `
                        <td style="color: #000000 !important;">${item.tag_id}</td>
                        <td style="color: #000000 !important;">${item.common_name}</td>
                        <td class="editable" onclick="showDropdown(event, this, 'bin-location', '${item.tag_id}', '${item.bin_location || ''}')">${item.bin_location || 'N/A'}</td>
                        <td class="editable" onclick="showDropdown(event, this, 'status', '${item.tag_id}', '${item.status}')">${item.status}</td>
                        <td style="color: #000000 !important;">${item.last_contract_num || 'N/A'}</td>
                        <td style="color: #000000 !important;">${lastScanned}</td>
                        <td style="color: #000000 !important;">${item.quality || 'N/A'}</td>
                        <td style="color: #000000 !important;">${item.notes || 'N/A'}</td>
                        <div id="dropdown-bin-location-${item.tag_id}" class="dropdown-menu">
                            <a class="dropdown-item" href="#" onclick="selectOption(event, this, 'bin-location', '${item.tag_id}', 'resale')">resale</a>
                            <a class="dropdown-item" href="#" onclick="selectOption(event, this, 'bin-location', '${item.tag_id}', 'sold')">sold</a>
                            <a class="dropdown-item" href="#" onclick="selectOption(event, this, 'bin-location', '${item.tag_id}', 'pack')">pack</a>
                            <a class="dropdown-item" href="#" onclick="selectOption(event, this, 'bin-location', '${item.tag_id}', 'burst')">burst</a>
                        </div>
                        <div id="dropdown-status-${item.tag_id}" class="dropdown-menu">
                            <a class="dropdown-item" href="#" onclick="selectOption(event, this, 'status', '${item.tag_id}', 'Ready to Rent')" ${item.status !== 'On Rent' && item.status !== 'Delivered' ? 'style="pointer-events: none; color: #ccc;"' : ''}>Ready to Rent</a>
                        </div>
                    `;
                    tbody.appendChild(row);
                });

                const paginationDiv = document.createElement('div');
                paginationDiv.className = 'pagination-controls';
                if (data.total_items > data.per_page) {
                    const totalPages = Math.ceil(data.total_items / data.per_page);
                    const escapedCommonName = commonName.replace(/'/g, "\\'").replace(/"/g, '\\"');
                    paginationDiv.innerHTML = `
                        <button class="btn btn-sm btn-secondary" 
                                onclick="loadItems('${category}', '${subcategory}', '${escapedCommonName}', '${targetId}', ${data.page - 1})" 
                                ${data.page === 1 ? 'disabled' : ''}>Previous</button>
                        <span>Page ${data.page} of ${totalPages}</span>
                        <button class="btn btn-sm btn-secondary" 
                                onclick="loadItems('${category}', '${subcategory}', '${escapedCommonName}', '${targetId}', ${data.page + 1})" 
                                ${data.page === totalPages ? 'disabled' : ''}>Next</button>
                    `;
                }
                wrapper.appendChild(paginationDiv);

                // Add print buttons
                const printDiv = document.createElement('div');
                printDiv.className = 'btn-group mt-2';
                const escapedCommonName = commonName.replace(/'/g, "\\'").replace(/"/g, '\\"');
                printDiv.innerHTML = `
                    <button class="btn btn-sm btn-info print-btn" 
                            data-print-level="Common Name" 
                            data-print-id="item-table-${key}" 
                            data-common-name="${escapedCommonName}" 
                            data-category="${category}" 
                            data-subcategory="${subcategory}">Print Aggregate</button>
                    <button class="btn btn-sm btn-info print-full-btn" 
                            data-common-name="${escapedCommonName}" 
                            data-category="${category}" 
                            data-subcategory="${subcategory}">Print Full List</button>
                `;
                wrapper.appendChild(printDiv);
            } else {
                tbody.innerHTML = `<tr><td colspan="8">No items found.</td></tr>`;
            }

            const parentRow = container.closest('tr.common-name-row').previousElementSibling;
            if (parentRow) {
                const expandBtn = parentRow.querySelector(`.expand-items-btn[data-target-id="${targetId}"]`);
                const collapseBtn = parentRow.querySelector(`.collapse-items-btn[data-collapse-target="${targetId}"]`);
                if (expandBtn && collapseBtn) {
                    expandBtn.style.display = 'none';
                    collapseBtn.style.display = 'inline-block';
                }
            }

            container.style.display = 'block';
            container.style.opacity = '1';
            container.style.visibility = 'visible';
            wrapper.classList.remove('collapsed'); // Ensure wrapper is visible on expand

            applyFilterWithRetryTab1(`item-table-${key}`, 'item');
        })
        .catch(error => {
            console.error('Items error:', error.message);
            const tbody = itemTable.querySelector('tbody');
            tbody.innerHTML = `<tr><td colspan="8">Error: ${error.message}</td></tr>`;
            container.style.display = 'block';
            container.style.opacity = '1';
            container.style.visibility = 'visible';
        })
        .finally(() => {
            setTimeout(() => {
                if (loadingSuccess) hideLoading(key);
                container.classList.remove('loading');
            }, 700);
        });
}

/**
 * Show dropdown for editable cells
 */
function showDropdown(event, cell, type, tagId, currentValue) {
    console.log('showDropdown:', { type, tagId, currentValue });
    event.stopPropagation();
    const dropdown = document.getElementById(`dropdown-${type}-${tagId}`);
    if (dropdown) {
        document.querySelectorAll('.dropdown-menu').forEach(d => {
            if (d !== dropdown) {
                d.classList.remove('show');
                d.style.display = 'none';
            }
        });
        dropdown.classList.add('show');
        dropdown.style.display = 'block';
        const rect = cell.getBoundingClientRect();
        dropdown.style.position = 'absolute';
        dropdown.style.left = `${rect.left + window.scrollX}px`;
        dropdown.style.top = `${rect.bottom + window.scrollY}px`;
        dropdown.style.zIndex = '1000';
        cell.setAttribute(`data-${type}`, currentValue);
    } else {
        console.error(`Dropdown not found for ${type}, tagId ${tagId}`);
    }
}

/**
 * Select option from dropdown
 */
function selectOption(event, element, type, tagId, value) {
    console.log('selectOption:', { type, tagId, value });
    event.preventDefault();
    event.stopPropagation();
    const cell = document.querySelector(`tr[data-item-id="${tagId}"] td.editable[onclick*="showDropdown(event, this, '${type}', '${tagId}'"]`);
    if (cell) {
        cell.textContent = value;
        cell.setAttribute(`data-${type}`, value);
        const dropdown = document.getElementById(`dropdown-${type}-${tagId}`);
        if (dropdown) {
            dropdown.classList.remove('show');
            dropdown.style.display = 'none';
        }
    }
}

/**
 * Save changes for editable cells
 */
function saveChanges(tagId) {
    console.log('saveChanges:', tagId);
    const binLocationCell = document.querySelector(`tr[data-item-id="${tagId}"] td.editable[onclick*="showDropdown(event, this, 'bin-location', '${tagId}'"]`);
    const statusCell = document.querySelector(`tr[data-item-id="${tagId}"] td.editable[onclick*="showDropdown(event, this, 'status', '${tagId}'"]`);

    const newBinLocation = binLocationCell?.getAttribute('data-bin-location');
    const newStatus = statusCell?.getAttribute('data-status');

    if (newBinLocation) {
        const url = '/tab/1/update_bin_location';
        fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tag_id: tagId, bin_location: newBinLocation })
        })
            .then(response => {
                console.log(`Bin location update status for ${tagId}: ${response.status}`);
                if (!response.ok) {
                    return response.text().then(text => {
                        throw new Error(`Bin location update failed: ${response.status} - ${text}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    console.error('Bin location error:', data.error);
                    alert('Failed to update bin location: ' + data.error);
                } else {
                    console.log('Bin location updated');
                    alert('Bin location updated!');
                }
            })
            .catch(error => {
                console.error('Bin location error:', error.message);
                alert('Error: ' + error.message);
            });
    }

    if (newStatus) {
        const url = '/tab/1/update_status';
        fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tag_id: tagId, status: newStatus })
        })
            .then(response => {
                console.log(`Status update status for ${tagId}: ${response.status}`);
                if (!response.ok) {
                    return response.text().then(text => {
                        throw new Error(`Status update failed: ${response.status} - ${text}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    console.error('Status error:', data.error);
                    alert('Failed to update status: ' + data.error);
                } else {
                    console.log('Status updated');
                    alert('Status updated!');
                    const itemsContainer = document.getElementById(`items-${tagId.split('-')[0]}`);
                    if (itemsContainer) {
                        const category = itemsContainer.closest('.common-level')?.querySelector('button[data-category]')?.getAttribute('data-category') ||
                                         itemsContainer.closest('tr')?.previousElementSibling?.querySelector('button[data-category]')?.getAttribute('data-category');
                        const subcategory = itemsContainer.closest('.common-level')?.querySelector('button[data-subcategory]')?.getAttribute('data-subcategory') ||
                                            itemsContainer.closest('tr')?.previousElementSibling?.querySelector('button[data-subcategory]')?.getAttribute('data-subcategory');
                        const commonName = itemsContainer.closest('tr')?.querySelector('td:first-child')?.textContent;
                        loadItems(category, subcategory, commonName, `items-${tagId.split('-')[0]}`);
                    }
                }
            })
            .catch(error => {
                console.error('Status error:', error.message);
                alert('Error: ' + error.message);
            });
    }
}

/**
 * Event listener for Tab 1
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('tab1.js: DOMContentLoaded');

    // Check if the current URL is /tab/1
    const isTab1 = window.location.pathname.match(/\/tab\/1\b/);
    console.log(`isTab1: ${isTab1}, window.cachedTabNum: ${window.cachedTabNum}, pathname: ${window.location.pathname}`);

    if (!isTab1 && window.cachedTabNum !== 1) {
        console.log('Not Tab 1, skipping');
        return;
    }

    console.log('Initializing Tab 1');
    populateSubcategories();

    document.removeEventListener('click', handleClick);
    document.addEventListener('click', handleClick);

    function handleClick(event) {
        console.log('handleClick: Event triggered');
        const expandBtn = event.target.closest('.expand-items-btn');
        if (expandBtn) {
            event.preventDefault();
            event.stopPropagation();
            console.log('Expand Items button clicked:', {
                category: expandBtn.getAttribute('data-category'),
                subcategory: expandBtn.getAttribute('data-subcategory'),
                commonName: expandBtn.getAttribute('data-common-name'),
                targetId: expandBtn.getAttribute('data-target-id')
            });

            const category = expandBtn.getAttribute('data-category');
            const subcategory = expandBtn.getAttribute('data-subcategory');
            const commonName = expandBtn.getAttribute('data-common-name');
            const targetId = expandBtn.getAttribute('data-target-id');

            if (!targetId || !category || !subcategory || !commonName) {
                console.error('Missing attributes on expand button');
                return;
            }

            const container = document.getElementById(targetId);
            if (!container) {
                console.error(`Container ${targetId} not found`);
                return;
            }

            const collapseBtn = expandBtn.parentElement.querySelector(`.collapse-items-btn[data-collapse-target="${targetId}"]`);
            loadItems(category, subcategory, commonName, targetId);
            if (expandBtn && collapseBtn) {
                expandBtn.style.display = 'none';
                collapseBtn.style.display = 'inline-block';
            }
            return;
        }

        const collapseBtn = event.target.closest('.collapse-items-btn');
        if (collapseBtn) {
            event.preventDefault();
            event.stopPropagation();
            const targetId = collapseBtn.getAttribute('data-collapse-target');
            console.log(`Collapsing items ${targetId}`);
            const container = document.getElementById(targetId);
            if (!container) {
                console.error(`Container ${targetId} not found`);
                return;
            }
            const expandBtn = collapseBtn.parentElement.querySelector(`.expand-items-btn[data-target-id="${targetId}"]`);
            const wrapper = container.querySelector('.item-level-wrapper');
            collapseSection(targetId);
            if (wrapper) {
                wrapper.classList.add('collapsed');
            }
            container.style.minHeight = '0';
            container.style.padding = '0';
            if (expandBtn && collapseBtn) {
                expandBtn.style.display = 'inline-block';
                collapseBtn.style.display = 'none';
            }
            return;
        }

        const saveBtn = event.target.closest('.save-btn');
        if (saveBtn) {
            event.preventDefault();
            event.stopPropagation();
            const tagId = saveBtn.closest('tr').getAttribute('data-item-id');
            console.log('Save button clicked:', tagId);
            saveChanges(tagId);
            return;
        }

        const printBtn = event.target.closest('.print-btn');
        if (printBtn) {
            event.preventDefault();
            event.stopPropagation();
            const level = printBtn.getAttribute('data-print-level');
            const id = printBtn.getAttribute('data-print-id');
            const commonName = printBtn.getAttribute('data-common-name');
            const category = printBtn.getAttribute('data-category');
            const subcategory = printBtn.getAttribute('data-subcategory');
            printTable(level, id, commonName, category, subcategory);
            return;
        }

        const printFullBtn = event.target.closest('.print-full-btn');
        if (printFullBtn) {
            event.preventDefault();
            event.stopPropagation();
            const commonName = printFullBtn.getAttribute('data-common-name');
            const category = printFullBtn.getAttribute('data-category');
            const subcategory = printFullBtn.getAttribute('data-subcategory');
            printFullItemList(category, subcategory, commonName);
            return;
        }
    }

    document.removeEventListener('click', handleDropdownClick);
    document.addEventListener('click', handleDropdownClick);

    function handleDropdownClick(event) {
        console.log('handleDropdownClick: Event triggered');
        if (!event.target.closest('.editable') && !event.target.closest('.dropdown-menu')) {
            document.querySelectorAll('.dropdown-menu').forEach(dropdown => {
                dropdown.classList.remove('show');
                dropdown.style.display = 'none';
            });
        }
    }
});