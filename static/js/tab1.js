console.log('tab1.js version: 2025-05-23-v8 loaded');

/**
 * Tab1.js: Logic for Tab 1 (Rental Inventory).
 * Dependencies: None (self-contained, uses common.js for printing).
 * Note: Split from tab1_5.js; removed Tab 5-specific functions (bulk updates).
 * Updated: Fixed tab detection to ensure initialization on /tab/1.
 */

/**
 * Show loading indicator
 */
function showLoadingTab1(targetId) {
    console.log(`showLoadingTab1: targetId=${targetId}`);
    const container = document.getElementById(targetId);
    if (!container) {
        console.warn(`Container ${targetId} not found for loading indicator`);
        return false;
    }
    const loadingDiv = document.createElement('div');
    loadingDiv.id = `loading-${targetId}`;
    loadingDiv.className = 'loading-indicator';
    loadingDiv.textContent = 'Loading...';
    loadingDiv.style.display = 'block';
    container.appendChild(loadingDiv);
    return true;
}

/**
 * Hide loading indicator
 */
function hideLoadingTab1(targetId) {
    console.log(`hideLoadingTab1: targetId=${targetId}`);
    const loadingDiv = document.getElementById(`loading-${targetId}`);
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

/**
 * Collapse section (category/subcategory level)
 */
function collapseSection(categoryRow, targetId) {
    console.log(`collapseSection: targetId=${targetId}`);
    if (!targetId || !categoryRow) {
        console.error('collapseSection: Invalid parameters', { targetId, categoryRow });
        return;
    }
    const existingRows = categoryRow.parentNode.querySelectorAll(`tr.common-name-row[data-target-id="${targetId}"]`);
    existingRows.forEach(row => row.remove());
    sessionStorage.removeItem(`expanded_${targetId}`);
}

/**
 * Collapse items (item level)
 */
function collapseItems(targetId) {
    console.log(`collapseItems: targetId=${targetId}`);
    const container = document.getElementById(targetId);
    if (!container) {
        console.error(`Container ${targetId} not found for collapsing items`);
        return;
    }
    container.classList.remove('expanded');
    container.classList.add('collapsed');
    container.style.opacity = '0';
    setTimeout(() => {
        container.style.display = 'none';
        container.innerHTML = ''; // Clear content
    }, 700);
    sessionStorage.removeItem(`expanded_items_${targetId}`);
}

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
                collapseSection(row, targetId);
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
            const category = table.closest('tr.common-name-row')?.previousElementSibling?.previousElementSibling?.cells[0]?.textContent.toLowerCase().replace(/[^a-z0-9]/g, '_') || '';
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
 * Populate subcategories
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
 * Load common names
 */
function loadCommonNames(selectElement, page = 1) {
    console.log('loadCommonNames: Starting', { page });
    const subcategory = selectElement.value;
    const category = selectElement.getAttribute('data-category');
    const targetId = `common-${category.toLowerCase().replace(/[^a-z0-9]/g, '_')}`;
    const categoryRow = selectElement.closest('tr');
    const tbody = categoryRow.closest('tbody');

    console.log('loadCommonNames:', { subcategory, category, targetId, page });

    if (!subcategory && page === 1) {
        console.log('No subcategory, collapsing');
        collapseSection(categoryRow, targetId);
        const url = `/tab/1/subcat_data?category=${encodeURIComponent(category)}`;
        fetch(url)
            .then(response => {
                console.log(`Subcat fetch status: ${response.status}`);
                if (!response.ok) {
                    return response.text().then(text => {
                        throw new Error(`Subcat fetch failed: ${response.status} - ${text}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                const totals = {
                    totalItems: data.subcategories.reduce((sum, subcat) => sum + (subcat.total_items || 0), 0),
                    itemsOnContracts: data.subcategories.reduce((sum, subcat) => sum + (subcat.items_on_contracts || 0), 0),
                    itemsInService: data.subcategories.reduce((sum, subcat) => sum + (subcat.items_in_service || 0), 0),
                    itemsAvailable: data.subcategories.reduce((sum, subcat) => sum + (subcat.items_available || 0), 0)
                };
                categoryRow.cells[2].textContent = totals.totalItems || '0';
                categoryRow.cells[3].textContent = totals.itemsOnContracts || '0';
                categoryRow.cells[4].textContent = totals.itemsInService || '0';
                categoryRow.cells[5].textContent = totals.itemsAvailable || '0';
                console.log('Category totals:', totals);
            })
            .catch(error => console.error('Error resetting totals:', error.message));
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

            let headerRow = categoryRow.parentNode.querySelector(`tr.common-name-row[data-target-id="${targetId}"] .common-table`);
            if (!headerRow) {
                headerRow = document.createElement('tr');
                headerRow.className = 'common-name-row';
                headerRow.setAttribute('data-target-id', targetId);
                headerRow.innerHTML = `
                    <td colspan="7">
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
                                <tr>
                                    <td style="color: #000000 !important;">Loading...</td>
                                    <td style="color: #000000 !important;">-</td>
                                    <td style="color: #000000 !important;">-</td>
                                    <td style="color: #000000 !important;">-</td>
                                    <td style="color: #000000 !important;">-</td>
                                    <td>-</td>
                                </tr>
                            </tbody>
                        </table>
                    </td>
                `;
                tbody.insertBefore(headerRow, categoryRow.nextSibling);
            }

            const tableBody = headerRow.querySelector('tbody');
            tableBody.innerHTML = '';

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

                data.common_names.forEach(item => {
                    const rowId = `${targetId}_${item.name.replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '')}`;
                    const escapedName = item.name.replace(/'/g, "\\'").replace(/"/g, '\\"');
                    const commonRow = document.createElement('tr');
                    commonRow.innerHTML = `
                        <td style="color: #000000 !important;">${item.name}</td>
                        <td style="color: #000000 !important;">${item.total_items || '0'}</td>
                        <td style="color: #000000 !important;">${item.items_on_contracts || '0'}</td>
                        <td style="color: #000000 !important;">${item.items_in_service || '0'}</td>
                        <td style="color: #000000 !important;">${item.items_available || '0'}</td>
                        <td>
                            <div class="btn-group">
                                <button class="btn btn-sm btn-secondary expand-btn" 
                                        data-category="${category}" 
                                        data-subcategory="${subcategory}" 
                                        data-common-name="${escapedName}" 
                                        data-target-id="items-${rowId}" 
                                        data-expanded="false">Expand Items</button>
                                <button class="btn btn-sm btn-secondary collapse-btn" 
                                        data-collapse-target="items-${rowId}" 
                                        style="display:none;">Collapse</button>
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
                    `;
                    tableBody.appendChild(commonRow);

                    const itemsRow = document.createElement('tr');
                    itemsRow.className = 'common-name-row';
                    itemsRow.setAttribute('data-target-id', targetId);
                    itemsRow.innerHTML = `
                        <td colspan="7">
                            <div id="items-${rowId}" class="expandable collapsed item-level"></div>
                        </td>
                    `;
                    tableBody.appendChild(itemsRow);
                });

                if (data.total_common_names > data.per_page) {
                    const totalPages = Math.ceil(data.total_common_names / data.per_page);
                    const paginationRow = document.createElement('tr');
                    paginationRow.className = 'common-name-row';
                    paginationRow.setAttribute('data-target-id', targetId);
                    paginationRow.innerHTML = `
                        <td colspan="7">
                            <div class="pagination-controls">
                                <button class="btn btn-sm btn-secondary" 
                                        onclick="loadCommonNames(document.querySelector('select[data-category=\"${category}\"]'), ${data.page - 1})" 
                                        ${data.page === 1 ? 'disabled' : ''}>Previous</button>
                                <span>Page ${data.page} of ${totalPages}</span>
                                <button class="btn btn-sm btn-secondary" 
                                        onclick="loadCommonNames(document.querySelector('select[data-category=\"${category}\"]'), ${data.page + 1})" 
                                        ${data.page === totalPages ? 'disabled' : ''}>Next</button>
                            </div>
                        </td>
                    `;
                    tableBody.appendChild(paginationRow);
                }

                const commonTable = document.getElementById(`common-table-${targetId}`);
                if (commonTable) {
                    console.log('Common table styles:', {
                        display: commonTable.style.display,
                        visibility: window.getComputedStyle(commonTable).visibility
                    });
                }
            } else {
                tableBody.innerHTML = `<tr><td colspan="7">No common names found.</td></tr>`;
            }

            applyFilterWithRetryTab1(`common-table-${targetId}`, 'common');
        })
        .catch(error => {
            console.error('Common names error:', error.message);
            tableBody.innerHTML = `<tr><td colspan="7">Error: ${error.message}</td></tr>`;
        })
        .finally(() => {
            setTimeout(() => {
                if (loadingDiv) loadingDiv.style.display = 'none';
            }, 700);
        });
}

/**
 * Load items
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
    const loadingSuccess = showLoadingTab1(key);

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
            } else {
                tbody.innerHTML = `<tr><td colspan="8">No items found.</td></tr>`;
            }

            const parentRow = container.closest('tr.common-name-row').previousElementSibling;
            if (parentRow) {
                const expandBtn = parentRow.querySelector(`.expand-btn[data-target-id="${targetId}"]`);
                const collapseBtn = parentRow.querySelector(`.collapse-btn[data-collapse-target="${targetId}"]`);
                if (expandBtn && collapseBtn) {
                    expandBtn.style.display = 'none';
                    collapseBtn.style.display = 'inline-block';
                } else {
                    console.warn(`Expand/Collapse buttons not found for ${targetId}`);
                }
            } else {
                console.warn(`Parent row not found for ${targetId}`);
            }

            container.classList.remove('collapsed');
            container.classList.add('expanded');
            container.style.display = 'block';
            container.style.opacity = '1';
            container.style.visibility = 'visible';

            console.log('Container styles:', {
                classList: container.classList.toString(),
                display: container.style.display,
                opacity: container.style.opacity,
                visibility: window.getComputedStyle(container).visibility
            });

            if (itemTable) {
                console.log('Item table styles:', {
                    display: itemTable.style.display,
                    visibility: window.getComputedStyle(itemTable).visibility
                });
            }

            applyFilterWithRetryTab1(`item-table-${key}`, 'item');
        })
        .catch(error => {
            console.error('Items error:', error.message);
            const tbody = itemTable.querySelector('tbody');
            tbody.innerHTML = `<tr><td colspan="8">Error: ${error.message}</td></tr>`;
            container.classList.remove('collapsed');
            container.classList.add('expanded');
            container.style.display = 'block';
            container.style.opacity = '1';
            container.style.visibility = 'visible';
        })
        .finally(() => {
            setTimeout(() => {
                if (loadingSuccess) hideLoadingTab1(key);
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
 * Load subcategories
 */
function loadSubcategories(category, targetId, page = 1) {
    console.log('loadSubcategories:', { category, targetId, page });

    const container = document.getElementById(targetId);
    if (!container) {
        console.error(`Container ${targetId} not found`);
        return;
    }

    const loadingSuccess = showLoadingTab1(targetId);

    const url = `/tab/1/subcat_data?category=${encodeURIComponent(category)}&page=${page}`;
    console.log(`Fetching subcategories: ${url}`);

    fetch(url)
        .then(response => {
            console.log(`Subcategory fetch status: ${response.status}`);
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`Subcategory fetch failed: ${response.status} - ${text}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Subcategory data:', data);
            if (data.error) {
                console.error('Subcategories error:', data.error);
                container.innerHTML = `<p>Error: ${data.error}</p>`;
                return;
            }

            let html = `
                <select class="subcategory-select form-control" data-category="${category}" onchange="loadCommonNames(this)">
                    <option value="">Select a subcategory</option>
            `;
            if (data.subcategories && data.subcategories.length > 0) {
                data.subcategories.forEach(subcat => {
                    const escapedSubcategory = subcat.subcategory.replace(/'/g, "\\'").replace(/"/g, '\\"');
                    html += `<option value="${escapedSubcategory}">${subcat.subcategory}</option>`;
                });
            } else {
                html += `<option value="">No subcategories available</option>`;
            }
            html += '</select>';

            if (data.total_subcats > data.per_page) {
                const totalPages = Math.ceil(data.total_subcats / data.per_page);
                const escapedCategory = category.replace(/'/g, "\\'").replace(/"/g, '\\"');
                html += `
                    <div class="pagination-controls mt-2">
                        <button class="btn btn-sm btn-secondary" onclick="loadSubcategories('${escapedCategory}', '${targetId}', ${data.page - 1})" ${data.page === 1 ? 'disabled' : ''}>Previous</button>
                        <span class="mx-2">Page ${data.page} of ${totalPages}</span>
                        <button class="btn btn-sm btn-secondary" onclick="loadSubcategories('${escapedCategory}', '${targetId}', ${data.page + 1})" ${data.page === totalPages ? 'disabled' : ''}>Next</button>
                    </div>
                `;
            }

            container.innerHTML = html;
            container.classList.remove('collapsed');
            container.classList.add('expanded');
            container.style.display = 'block';
            container.style.opacity = '1';
            container.style.visibility = 'visible';

            console.log('Subcategory container styles:', {
                classList: container.classList.toString(),
                display: container.style.display,
                opacity: container.style.opacity,
                visibility: window.getComputedStyle(container).visibility
            });

            sessionStorage.setItem(`expanded_${targetId}`, JSON.stringify({ category, page }));
        })
        .catch(error => {
            console.error('Subcategories error:', error.message);
            container.innerHTML = `<p>Error: ${error.message}</p>`;
            container.classList.remove('collapsed');
            container.classList.add('expanded');
            container.style.display = 'block';
            container.style.opacity = '1';
            container.style.visibility = 'visible';
        })
        .finally(() => {
            if (loadingSuccess) hideLoadingTab1(targetId);
        });
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
        const expandBtn = event.target.closest('.expand-btn');
        if (expandBtn) {
            event.preventDefault();
            event.stopPropagation();
            console.log('Expand button clicked:', {
                category: expandBtn.getAttribute('data-category'),
                subcategory: expandBtn.getAttribute('data-subcategory'),
                commonName: expandBtn.getAttribute('data-common-name'),
                targetId: expandBtn.getAttribute('data-target-id'),
                isExpanded: expandBtn.getAttribute('data-expanded')
            });

            const category = expandBtn.getAttribute('data-category');
            const subcategory = expandBtn.getAttribute('data-subcategory');
            const commonName = expandBtn.getAttribute('data-common-name');
            const targetId = expandBtn.getAttribute('data-target-id');
            const isExpanded = expandBtn.getAttribute('data-expanded') === 'true';

            if (!targetId || !category) {
                console.error('Missing attributes on expand button');
                return;
            }

            const container = document.getElementById(targetId);
            if (!container) {
                console.error(`Container ${targetId} not found`);
                return;
            }

            const collapseBtn = expandBtn.parentElement.querySelector(`.collapse-btn[data-collapse-target="${targetId}"]`);

            if (isExpanded) {
                console.log(`Collapsing ${targetId}`);
                if (commonName) {
                    collapseItems(targetId);
                } else {
                    collapseSection(expandBtn.closest('tr'), targetId);
                }
                if (expandBtn && collapseBtn) {
                    expandBtn.style.display = 'inline-block';
                    collapseBtn.style.display = 'none';
                    expandBtn.setAttribute('data-expanded', 'false');
                    expandBtn.textContent = commonName ? 'Expand Items' : 'Expand';
                }
            } else {
                if (commonName && subcategory) {
                    console.log(`Loading items for ${commonName}`);
                    loadItems(category, subcategory, commonName, targetId);
                    if (expandBtn && collapseBtn) {
                        expandBtn.style.display = 'none';
                        collapseBtn.style.display = 'inline-block';
                        expandBtn.setAttribute('data-expanded', 'true');
                    }
                } else {
                    console.log(`Loading subcategories for ${category}`);
                    loadSubcategories(category, targetId);
                    if (expandBtn && collapseBtn) {
                        expandBtn.style.display = 'none';
                        collapseBtn.style.display = 'inline-block';
                        expandBtn.setAttribute('data-expanded', 'true');
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
            console.log(`Collapsing ${targetId}`);
            const container = document.getElementById(targetId);
            if (!container) {
                console.error(`Container ${targetId} not found`);
                return;
            }
            const expandBtn = collapseBtn.parentElement.querySelector(`.expand-btn[data-target-id="${targetId}"]`);
            if (container.classList.contains('item-level')) {
                collapseItems(targetId);
            } else {
                collapseSection(collapseBtn.closest('tr'), targetId);
            }
            if (expandBtn && collapseBtn) {
                expandBtn.style.display = 'inline-block';
                collapseBtn.style.display = 'none';
                expandBtn.setAttribute('data-expanded', 'false');
                expandBtn.textContent = expandBtn.getAttribute('data-common-name') ? 'Expand Items' : 'Expand';
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