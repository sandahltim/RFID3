console.log('tab1.js version: 2025-06-25-v2 loaded');

/**
 * Tab1.js: Logic for Tab 1.
 * Dependencies: common.js (for formatDate, showLoading, hideLoading, collapseSection, printTable, printFullItemList).
 * Updated: 2025-06-25-v2
 * - Added fetchAllSubcategories to populateSubcategories to fix dropdown truncation.
 * - Fixed collapse by hiding all related common-name-row <tr> elements.
 * - Added event.stopPropagation to handleClick to prevent tab.js warnings.
 * - Preserved all functionality (bulk updates, CSV export, pagination).
 */

function applyFilterToAllLevelsTab1() {
    console.log(`applyFilterToAllLevelsTab1: Starting at ${new Date().toISOString()}`);
    if (window.cachedTabNum === 3 || !window.location.pathname.match(/\/tab\/\d+/)) {
        console.log(`Skipping applyFilterToAllLevels for Tab 3 or non-tab page at ${new Date().toISOString()}`);
        return;
    }

    if (window.cachedTabNum === 1 || window.cachedTabNum === 5) {
        const categoryTable = document.getElementById('category-table');
        if (!categoryTable) {
            console.warn(`Category table not found, skipping filter application at ${new Date().toISOString()}`);
            return;
        }

        const categoryRows = categoryTable.querySelectorAll('.category-row') || [];
        if (!categoryRows.length) {
            console.warn(`No category rows found in table, skipping filter application at ${new Date().toISOString()}`);
            return;
        }

        let visibleCategoryRows = 0;

        categoryRows.forEach(categoryRow => {
            let showCategoryRow = true;
            const categoryCell = categoryRow.querySelector('td:nth-child(1)');
            const categoryValue = categoryCell ? categoryCell.textContent.toLowerCase() : '';
            const normalizedCategoryValue = categoryValue.toLowerCase().replace(/\s+/g, '_');
            const subcatSelect = categoryRow.querySelector('.subcategory-select');
            let hasMatchingItems = false;

            const options = subcatSelect ? subcatSelect.querySelectorAll('option:not([value=""])') : [];
            const selectedOption = subcatSelect ? subcatSelect.options[subcatSelect.selectedIndex] : null;
            const selectedValue = selectedOption ? selectedOption.value : '';

            if (selectedValue) {
                const commonTables = categoryRow.parentNode.querySelectorAll(`.common-name-row[data-target-id^="common-${normalizedCategoryValue}"] .common-table`);
                if (!commonTables.length) {
                    console.warn(`Common tables not found for category ${categoryValue} (normalized: ${normalizedCategoryValue}) at ${new Date().toISOString()}`);
                    return;
                }

                let visibleSubcategories = 0;
                commonTables.forEach(commonTable => {
                    const commonRows = commonTable.querySelectorAll('tbody tr:not(.common-name-row)') || [];
                    let visibleCommonRows = 0;

                    commonRows.forEach((commonRow, index) => {
                        if (index % 2 !== 0) return;

                        let showCommonRow = true;
                        const commonNameCell = commonRow.querySelector('td:nth-child(1)');
                        const commonNameValue = commonNameCell ? commonNameCell.textContent.toLowerCase() : '';

                        if (window.globalFilter.commonName && !commonNameValue.includes(window.globalFilter.commonName)) {
                            showCommonRow = false;
                        }

                        const commonExpandableRow = commonRow.nextElementSibling;
                        let visibleItemRows = 0;
                        if (commonExpandableRow && commonExpandableRow.classList.contains('common-name-row')) {
                            const itemsDiv = commonExpandableRow.querySelector('.expandable');
                            if (itemsDiv && itemsDiv.classList.contains('expanded')) {
                                const itemTable = itemsDiv.querySelector('.item-table');
                                if (itemTable) {
                                    const itemRows = itemTable.querySelectorAll('tbody tr') || [];
                                    itemRows.forEach(itemRow => {
                                        let showItemRow = true;
                                        const itemCommonNameCell = itemRow.querySelector('td:nth-child(2)');
                                        const itemContractCell = itemRow.querySelector('td:nth-child(5)');
                                        const itemCommonNameValue = itemCommonNameCell ? itemCommonNameCell.textContent.toLowerCase() : '';
                                        const itemContractValue = itemContractCell ? itemContractCell.textContent.toLowerCase() : '';

                                        if (window.globalFilter.commonName && !itemCommonNameValue.includes(window.globalFilter.commonName)) {
                                            showItemRow = false;
                                        }
                                        if (window.globalFilter.contractNumber && !itemContractValue.includes(window.globalFilter.contractNumber)) {
                                            showItemRow = false;
                                        }

                                        itemRow.style.display = showItemRow ? '' : 'none';
                                        if (showItemRow) {
                                            visibleItemRows++;
                                            showCommonRow = true;
                                            hasMatchingItems = true;
                                        }
                                    });

                                    let itemRowCountDiv = itemTable.nextElementSibling;
                                    if (itemRowCountDiv && !itemRowCountDiv.classList.contains('row-count')) {
                                        itemRowCountDiv = document.createElement('div');
                                        itemRowCountDiv.className = 'row-count mt-2';
                                        itemTable.insertAdjacentElement('afterend', itemRowCountDiv);
                                    }
                                    if (itemRowCountDiv) {
                                        itemRowCountDiv.textContent = `Showing ${visibleItemRows} of ${itemRows.length} rows`;
                                    }

                                    if (visibleItemRows > 0) {
                                        itemsDiv.classList.remove('collapsed');
                                        itemsDiv.classList.add('expanded');
                                        itemsDiv.style.display = 'block';
                                        itemsDiv.style.opacity = '1';
                                        const expandBtn = commonRow.querySelector('.expand-btn');
                                        const collapseBtn = commonRow.querySelector('.collapse-btn');
                                        if (expandBtn && collapseBtn) {
                                            expandBtn.style.display = 'none';
                                            collapseBtn.style.display = 'inline-block';
                                        }
                                    } else {
                                        itemsDiv.classList.remove('expanded');
                                        itemsDiv.classList.add('collapsed');
                                        itemsDiv.style.display = 'none';
                                        const expandBtn = commonRow.querySelector('.expand-btn');
                                        const collapseBtn = commonRow.querySelector('.collapse-btn');
                                        if (expandBtn && collapseBtn) {
                                            expandBtn.style.display = 'inline-block';
                                            collapseBtn.style.display = 'none';
                                        }
                                    }
                                }
                            }
                        }

                        commonRow.style.display = showCommonRow ? '' : 'none';
                        if (commonExpandableRow) {
                            commonExpandableRow.style.display = showCommonRow ? '' : 'none';
                        }
                        if (showCommonRow) visibleCommonRows++;
                    });

                    let commonRowCountDiv = commonTable.nextElementSibling;
                    if (commonRowCountDiv && !commonRowCountDiv.classList.contains('row-count')) {
                        commonRowCountDiv = document.createElement('div');
                        commonRowCountDiv.className = 'row-count mt-2';
                        commonTable.insertAdjacentElement('afterend', commonRowCountDiv);
                    }
                    if (commonRowCountDiv) {
                        commonRowCountDiv.textContent = `Showing ${visibleCommonRows} of ${commonRows.length / 2} rows`;
                    }

                    if (visibleCommonRows > 0 || hasMatchingItems) {
                        visibleSubcategories++;
                        showCategoryRow = true;
                    }
                });
            } else {
                if (window.globalFilter.commonName) {
                    if (categoryValue.includes(window.globalFilter.commonName)) {
                        showCategoryRow = true;
                    }
                } else {
                    showCategoryRow = true;
                }
            }

            if (!window.globalFilter.commonName && !window.globalFilter.contractNumber) {
                showCategoryRow = true;
                options.forEach(option => option.style.display = '');
            }

            categoryRow.style.display = showCategoryRow ? '' : 'none';
            if (showCategoryRow) {
                visibleCategoryRows++;
                const relatedRows = categoryRow.parentNode.querySelectorAll(`.common-name-row[data-target-id^="common-${normalizedCategoryValue}"]`);
                relatedRows.forEach(row => {
                    row.style.display = showCategoryRow ? '' : 'none';
                });
            }
        });

        let rowCountDiv = document.querySelector('.row-count');
        if (!rowCountDiv) {
            rowCountDiv = document.createElement('div');
            rowCountDiv.className = 'row-count mt-2';
            categoryTable.insertAdjacentElement('afterend', rowCountDiv);
        }
        rowCountDiv.textContent = `Showing ${visibleCategoryRows} of ${categoryRows.length} rows`;
    }
}

function populateSubcategories() {
    console.log(`populateSubcategories: Starting at ${new Date().toISOString()}`);
    const selects = document.querySelectorAll('.subcategory-select');
    console.log(`populateSubcategories: Found ${selects.length} subcategory selects at ${new Date().toISOString()}`);
    const promises = Array.from(selects).map(select => {
        const category = select.getAttribute('data-category');
        console.log(`Populating subcategories for ${category} at ${new Date().toISOString()}`);
        if (!category) {
            console.error(`Missing data-category attribute for select element at ${new Date().toISOString()}`, select);
            return Promise.resolve();
        }

        async function fetchAllSubcategories(page = 1, accumulatedSubcats = []) {
            const url = `/tab/1/subcat_data?category=${encodeURIComponent(category)}&page=${page}`;
            try {
                const response = await fetch(url);
                console.log(`Subcategory fetch status for ${category}, page ${page}: ${response.status} at ${new Date().toISOString()}`);
                if (!response.ok) {
                    const text = await response.text();
                    throw new Error(`Subcategory fetch failed: ${response.status} - ${text}`);
                }
                const data = await response.json();
                console.log(`Subcategory data for ${category}, page ${page}:`, data, `at ${new Date().toISOString()}`);

                const subcategories = accumulatedSubcats.concat(data.subcategories || []);
                const totalSubcats = data.total_subcats || 0;
                const perPage = data.per_page || 10;
                const totalPages = Math.ceil(totalSubcats / perPage);

                if (page < totalPages) {
                    return fetchAllSubcategories(page + 1, subcategories);
                } else {
                    return subcategories;
                }
            } catch (error) {
                console.error(`Subcategory fetch error for ${category}, page ${page}: ${error.message} at ${new Date().toISOString()}`);
                return accumulatedSubcats;
            }
        }

        return fetchAllSubcategories().then(subcategories => {
            select.innerHTML = '<option value="">Select a subcategory</option>';
            if (subcategories.length > 0) {
                subcategories.forEach(subcat => {
                    const option = document.createElement('option');
                    option.value = subcat.subcategory;
                    option.textContent = subcat.subcategory;
                    select.appendChild(option);
                });
                console.log(`Populated ${subcategories.length} subcategories for ${category} at ${new Date().toISOString()}`);
            } else {
                select.innerHTML += '<option value="">No subcategories</option>';
                console.warn(`No subcategories returned for ${category} at ${new Date().toISOString()}`);
            }
        }).catch(error => {
            console.error(`Error populating subcategories for ${category}: ${error.message} at ${new Date().toISOString()}`);
            select.innerHTML = '<option value="">Error loading subcategories</option>';
        });
    });

    return Promise.all(promises).catch(error => console.error('Error populating subcategories:', error, `at ${new Date().toISOString()}`));
}

function loadCommonNames(selectElement, page = 1) {
    console.log(`loadCommonNames: Starting at ${new Date().toISOString()}`, { selectElement, page });
    const subcategory = selectElement.value;
    const category = selectElement.getAttribute('data-category');
    const targetId = `common-${category.toLowerCase().replace(/[^a-z0-9]/g, '_')}`;
    const categoryRow = selectElement.closest('tr');
    const tbody = categoryRow.closest('tbody');

    console.log(`loadCommonNames: Parameters`, { subcategory, category, targetId, page }, `at ${new Date().toISOString()}`);

    if (!subcategory && page === 1) {
        console.log(`No subcategory, collapsing at ${new Date().toISOString()}`);
        const url = `/tab/1/subcat_data?category=${encodeURIComponent(category)}`;
        fetch(url)
            .then(response => {
                console.log(`Subcat fetch status: ${response.status} at ${new Date().toISOString()}`);
                if (!response.ok) {
                    return response.text().then(text => {
                        throw new Error(`Subcat fetch failed: ${response.status} - ${text}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                console.log(`Subcat data for ${category}:`, data, `at ${new Date().toISOString()}`);
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
                console.log(`Category totals:`, totals, `at ${new Date().toISOString()}`);
            })
            .catch(error => console.error(`Error resetting totals: ${error.message} at ${new Date().toISOString()}`));
        return;
    }

    if (!category || !subcategory || !targetId) {
        console.error(`loadCommonNames: Invalid parameters`, { category, subcategory, targetId }, `at ${new Date().toISOString()}`);
        return;
    }

    const loadingId = `loading-subcat-${targetId}`;
    const loadingDiv = document.getElementById(loadingId);
    if (loadingDiv) loadingDiv.style.display = 'block';

    const url = `/tab/1/common_names?category=${encodeURIComponent(category)}&subcategory=${encodeURIComponent(subcategory)}&page=${page}`;
    console.log(`Fetching common names: ${url} at ${new Date().toISOString()}`);

    fetch(url)
        .then(response => {
            console.log(`Common names fetch status: ${response.status} at ${new Date().toISOString()}`);
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`Common names fetch failed: ${response.status} - ${text}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log(`Common names data:`, data, `at ${new Date().toISOString()}`);

            let headerRow = categoryRow.parentNode.querySelector(`tr.common-name-row[data-target-id="${targetId}"] .common-table`);
            if (!headerRow) {
                headerRow = document.createElement('tr');
                headerRow.className = 'common-name-row';
                headerRow.setAttribute('data-target-id', targetId);
                headerRow.innerHTML = `
                    <td colspan="7">
                        <table class="table table-bordered table-hover common-table" id="common-table-${targetId}">
                            <thead class="thead-dark">
                                <tr>
                                    <th>Common Name</th>
                                    <th>Total Items</th>
                                    <th>Items on Contracts</th>
                                    <th>Items in Service</th>
                                    <th>Items Available</th>
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
                console.log(`Common name totals:`, totals, `at ${new Date().toISOString()}`);
                categoryRow.cells[2].textContent = totals.totalItems || '0';
                categoryRow.cells[3].textContent = totals.itemsOnContracts || '0';
                categoryRow.cells[4].textContent = totals.itemsInService || '0';
                categoryRow.cells[5].textContent = totals.itemsAvailable || '0';

                data.common_names.forEach(item => {
                    const rowId = `${targetId}_${item.name.replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '')}`;
                    const escapedName = item.name.replace(/'/g, "\\'").replace(/"/g, '\\"');
                    const commonRow = document.createElement('tr');
                    commonRow.innerHTML = `
                        <td>${item.name}</td>
                        <td>${item.total_items || '0'}</td>
                        <td>${item.items_on_contracts || '0'}</td>
                        <td>${item.items_in_service || '0'}</td>
                        <td>${item.items_available || '0'}</td>
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
                                <button class="btn btn-sm btn-secondary prev-page" 
                                        data-page="${data.page - 1}" 
                                        data-category="${category}" 
                                        ${data.page === 1 ? 'disabled' : ''}>Previous</button>
                                <span>Page ${data.page} of ${totalPages}</span>
                                <button class="btn btn-sm btn-secondary next-page" 
                                        data-page="${data.page + 1}" 
                                        data-category="${category}" 
                                        ${data.page === totalPages ? 'disabled' : ''}>Next</button>
                            </div>
                        </td>
                    `;
                    tableBody.appendChild(paginationRow);

                    paginationRow.querySelectorAll('.prev-page, .next-page').forEach(button => {
                        button.addEventListener('click', () => {
                            const newPage = parseInt(button.getAttribute('data-page'));
                            const select = document.querySelector(`select[data-category="${category}"]`);
                            if (select) {
                                loadCommonNames(select, newPage);
                            }
                        });
                    });
                }

                const commonTable = document.getElementById(`common-table-${targetId}`);
                if (commonTable) {
                    console.log(`Common table styles:`, {
                        display: commonTable.style.display,
                        visibility: window.getComputedStyle(commonTable).visibility
                    }, `at ${new Date().toISOString()}`);
                }
            } else {
                tableBody.innerHTML = `<tr><td colspan="7">No common names found.</td></tr>`;
                console.warn(`No common names returned for category ${category}, subcategory ${subcategory} at ${new Date().toISOString()}`);
            }

            sessionStorage.setItem(`expanded_${targetId}`, JSON.stringify({ category, subcategory, page }));
        })
        .catch(error => {
            console.error(`Common names error: ${error.message} at ${new Date().toISOString()}`);
            tableBody.innerHTML = `<tr><td colspan="7">Error: ${error.message}</td></tr>`;
        })
        .finally(() => {
            setTimeout(() => {
                if (loadingDiv) loadingDiv.style.display = 'none';
            }, 700);
        });
}

function loadItems(category, subcategory, commonName, targetId, page = 1) {
    console.log(`loadItems: Starting at ${new Date().toISOString()}`, { category, subcategory, commonName, targetId, page });

    if (!category || !subcategory || !commonName || !targetId) {
        console.error(`loadItems: Invalid parameters`, { category, subcategory, commonName, targetId }, `at ${new Date().toISOString()}`);
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
    const loadingSuccess = showLoading(key);

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
            </tr>
        </tbody>
    `;
    wrapper.appendChild(itemTable);

    const url = `/tab/1/data?common_name=${encodeURIComponent(commonName)}&page=${page}&subcategory=${encodeURIComponent(subcategory)}&category=${encodeURIComponent(category)}`;
    console.log(`Fetching items: ${url} at ${new Date().toISOString()}`);

    fetch(url)
        .then(response => {
            console.log(`Items fetch status: ${response.status} at ${new Date().toISOString()}`);
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`Items fetch failed: ${response.status} - ${text}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log(`Items data:`, data, `at ${new Date().toISOString()}`);
            const tbody = itemTable.querySelector('tbody');
            tbody.innerHTML = '';

            if (data.items && data.items.length > 0) {
                data.items.forEach(item => {
                    const lastScanned = formatDate(item.last_scanned_date);
                    const currentStatus = item.status || 'N/A';
                    const binLocationLower = item.bin_location ? item.bin_location.toLowerCase() : '';
                    const row = document.createElement('tr');
                    row.setAttribute('data-item-id', item.tag_id);
                    row.innerHTML = `
                        <td class="editable" data-field="tag_id">${item.tag_id}</td>
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
                                <option value="Ready to Rent" ${currentStatus === 'On Rent' || currentStatus === 'Delivered' ? '' : 'disabled'}>Ready to Rent</option>
                                <option value="Sold">Sold</option>
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
                            <input class="edit-input" style="display: none;" value="${item.notes || ''}">
                        </td>
                    `;
                    tbody.appendChild(row);
                });

                const paginationDiv = document.createElement('div');
                paginationDiv.className = 'pagination-controls';
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
                            loadItems(category, subcategory, commonName, targetId, newPage);
                        });
                    });
                }
                wrapper.appendChild(paginationDiv);
            } else {
                tbody.innerHTML = `<tr><td colspan="8">No items found.</td></tr>`;
                console.warn(`No items returned for category ${category}, subcategory ${subcategory}, commonName ${commonName} at ${new Date().toISOString()}`);
            }

            const parentRow = container.closest('tr.common-name-row').previousElementSibling;
            if (parentRow) {
                const expandBtn = parentRow.querySelector(`.expand-btn[data-target-id="${targetId}"]`);
                const collapseBtn = parentRow.querySelector(`.collapse-btn[data-collapse-target="${targetId}"]`);
                if (expandBtn && collapseBtn) {
                    expandBtn.style.display = 'none';
                    collapseBtn.style.display = 'inline-block';
                } else {
                    console.warn(`Expand/Collapse buttons not found for ${targetId} at ${new Date().toISOString()}`);
                }
            } else {
                console.warn(`Parent row not found for ${targetId} at ${new Date().toISOString()}`);
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

            if (itemTable) {
                console.log(`Item table styles:`, {
                    display: itemTable.style.display,
                    visibility: window.getComputedStyle(itemTable).visibility
                }, `at ${new Date().toISOString()}`);
            }
        })
        .catch(error => {
            console.error(`Items error: ${error.message} at ${new Date().toISOString()}`);
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
                if (loadingSuccess) hideLoading(key);
                container.classList.remove('loading');
            }, 700);
        });
}

function saveEdit(cell, tagId, field, key, category, subcategory, commonName, targetId) {
    console.log(`saveEdit: Starting at ${new Date().toISOString()}`, { tagId, field, key, category, subcategory, commonName, targetId });
    const select = cell.querySelector('.edit-select');
    const input = cell.querySelector('.edit-input');
    const value = select ? select.value : input ? input.value : '';

    if (!value && field !== 'notes') {
        alert(`Please select a value for ${field}.`);
        return;
    }

    const url = `/tab/1/update_${field}`;
    fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tag_id: tagId, [field]: value })
    })
        .then(response => {
            console.log(`Update ${field} status for ${tagId}: ${response.status} at ${new Date().toISOString()}`);
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`Update ${field} failed: ${response.status} - ${text}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                console.error(`Update ${field} error: ${data.error} at ${new Date().toISOString()}`);
                alert(`Failed to update ${field}: ${data.error}`);
            } else {
                console.log(`Update ${field} successful at ${new Date().toISOString()}`);
                loadItems(category, subcategory, commonName, targetId);
            }
        })
        .catch(error => {
            console.error(`Update ${field} error: ${error.message} at ${new Date().toISOString()}`);
            alert(`Error: ${error.message}`);
        });
}

document.addEventListener('DOMContentLoaded', function() {
    console.log(`tab1.js: DOMContentLoaded at ${new Date().toISOString()}`);
    const isTab1 = window.location.pathname.match(/\/tab\/1\b/);
    console.log(`isTab1: ${isTab1}, window.cachedTabNum: ${window.cachedTabNum}, pathname: ${window.location.pathname} at ${new Date().toISOString()}`);

    if (!isTab1 && window.cachedTabNum !== 1) {
        console.log(`Not Tab 1, skipping at ${new Date().toISOString()}`);
        return;
    }

    console.log(`Initializing Tab 1 at ${new Date().toISOString()}`);
    populateSubcategories().then(() => {
        console.log(`Subcategories populated successfully at ${new Date().toISOString()}`);
        document.removeEventListener('click', handleClick);
        document.addEventListener('click', handleClick);
    }).catch(error => {
        console.error(`Error during subcategory population: ${error.message} at ${new Date().toISOString()}`);
    });

    function handleClick(event) {
        console.log(`handleClick: Event triggered at ${new Date().toISOString()}`);
        const expandBtn = event.target.closest('.expand-btn');
        if (expandBtn) {
            event.preventDefault();
            event.stopPropagation();
            console.log(`Expand button clicked:`, {
                category: expandBtn.getAttribute('data-category'),
                subcategory: expandBtn.getAttribute('data-subcategory'),
                commonName: expandBtn.getAttribute('data-common-name'),
                targetId: expandBtn.getAttribute('data-target-id'),
                isExpanded: expandBtn.getAttribute('data-expanded')
            }, `at ${new Date().toISOString()}`);

            const category = expandBtn.getAttribute('data-category');
            const subcategory = expandBtn.getAttribute('data-subcategory');
            const commonName = expandBtn.getAttribute('data-common-name');
            const targetId = expandBtn.getAttribute('data-target-id');
            const isExpanded = expandBtn.getAttribute('data-expanded') === 'true';

            if (!targetId || !category) {
                console.error(`Missing attributes on expand button at ${new Date().toISOString()}`);
                return;
            }

            const container = document.getElementById(targetId);
            if (!container) {
                console.error(`Container ${targetId} not found at ${new Date().toISOString()}`);
                return;
            }

            const collapseBtn = expandBtn.parentElement.querySelector(`.collapse-btn[data-collapse-target="${targetId}"]`);
            const relatedRows = document.querySelectorAll(`tr.common-name-row[data-target-id="${targetId}"]`);

            if (isExpanded) {
                console.log(`Collapsing ${targetId} at ${new Date().toISOString()}`);
                if (commonName) {
                    collapseSection(targetId);
                    relatedRows.forEach(row => {
                        row.classList.add('collapsed');
                        row.style.display = 'none';
                        row.style.minHeight = '0';
                        row.style.padding = '0';
                    });
                    console.log(`Collapsed ${relatedRows.length} related rows for ${targetId} at ${new Date().toISOString()}`);
                }
                if (expandBtn && collapseBtn) {
                    expandBtn.style.display = 'inline-block';
                    collapseBtn.style.display = 'none';
                    expandBtn.setAttribute('data-expanded', 'false');
                    expandBtn.textContent = commonName ? 'Expand Items' : 'Expand';
                }
            } else {
                if (commonName && subcategory) {
                    console.log(`Loading items for ${commonName} at ${new Date().toISOString()}`);
                    loadItems(category, subcategory, commonName, targetId);
                    relatedRows.forEach(row => {
                        row.classList.remove('collapsed');
                        row.style.display = '';
                    });
                    console.log(`Expanded ${relatedRows.length} related rows for ${targetId} at ${new Date().toISOString()}`);
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
            console.log(`Collapsing ${targetId} at ${new Date().toISOString()}`);
            const container = document.getElementById(targetId);
            if (!container) {
                console.error(`Container ${targetId} not found at ${new Date().toISOString()}`);
                return;
            }
            const expandBtn = collapseBtn.parentElement.querySelector(`.expand-btn[data-target-id="${targetId}"]`);
            const relatedRows = document.querySelectorAll(`tr.common-name-row[data-target-id="${targetId}"]`);
            if (container.classList.contains('item-level')) {
                collapseSection(targetId);
                relatedRows.forEach(row => {
                    row.classList.add('collapsed');
                    row.style.display = 'none';
                    row.style.minHeight = '0';
                    row.style.padding = '0';
                });
                console.log(`Collapsed ${relatedRows.length} related rows for ${targetId} at ${new Date().toISOString()}`);
            }
            if (expandBtn && collapseBtn) {
                expandBtn.style.display = 'inline-block';
                collapseBtn.style.display = 'none';
                expandBtn.setAttribute('data-expanded', 'false');
                expandBtn.textContent = expandBtn.getAttribute('data-common-name') ? 'Expand Items' : 'Expand';
            }
            return;
        }

        const printBtn = event.target.closest('.print-btn');
        if (printBtn) {
            event.preventDefault();
            event.stopPropagation();
            const printLevel = printBtn.getAttribute('data-print-level');
            const printId = printBtn.getAttribute('data-print-id');
            const commonName = printBtn.getAttribute('data-common-name');
            const category = printBtn.getAttribute('data-category');
            const subcategory = printBtn.getAttribute('data-subcategory');
            printTable(printLevel, printId, commonName, category, subcategory);
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

        const editableCell = event.target.closest('.editable');
        if (editableCell) {
            const field = editableCell.getAttribute('data-field');
            const row = editableCell.closest('tr');
            const tagId = row.getAttribute('data-item-id');
            const commonName = row.querySelector('td:nth-child(2)').textContent;
            const category = row.closest('.common-level')?.querySelector('button[data-category]')?.getAttribute('data-category') ||
                             row.closest('tr').previousElementSibling?.querySelector('button[data-category]')?.getAttribute('data-category');
            const subcategory = row.closest('.common-level')?.querySelector('button[data-subcategory]')?.getAttribute('data-subcategory') ||
                                row.closest('tr').previousElementSibling?.querySelector('button[data-subcategory]')?.getAttribute('data-subcategory');
            const targetId = row.closest('.expandable').id;

            const cellContent = editableCell.querySelector('.cell-content');
            const select = editableCell.querySelector('.edit-select');
            const input = editableCell.querySelector('.edit-input');

            if (select) {
                cellContent.style.display = 'none';
                select.style.display = 'block';
                select.focus();

                const saveChanges = () => {
                    saveEdit(editableCell, tagId, field, targetId, category, subcategory, commonName, targetId);
                    select.removeEventListener('change', saveChanges);
                    select.removeEventListener('blur', revert);
                };

                const revert = () => {
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

                const saveChanges = () => {
                    saveEdit(editableCell, tagId, field, targetId, category, subcategory, commonName, targetId);
                    input.removeEventListener('blur', saveChanges);
                    input.removeEventListener('keypress', handleKeypress);
                };

                const handleKeypress = (e) => {
                    if (e.key === 'Enter') {
                        saveEdit(editableCell, tagId, field, targetId, category, subcategory, commonName, targetId);
                        input.removeEventListener('blur', saveChanges);
                        input.removeEventListener('keypress', handleKeypress);
                    }
                };

                input.addEventListener('blur', saveChanges);
                input.addEventListener('keypress', handleKeypress);
            }
        }
    }
});