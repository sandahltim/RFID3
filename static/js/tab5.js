console.log('tab5.js version: 2025-05-29-v6 loaded');

/**
 * Tab5.js: Logic for Tab 5 (Resale/Rental Packs).
 * Dependencies: common.js (for formatDate, showLoading, hideLoading, collapseSection, printTable, printFullItemList).
 * Updated: Removed duplicate functions, now using common.js utilities.
 */

/**
 * Apply filter to all levels for Tab 5
 * Specific to Tab 5, uses globalFilter
 */
function applyFilterToAllLevelsTab5() {
    console.log('applyFilterToAllLevelsTab5: Starting');
    // Skip filtering for Tab 3 and non-tab pages
    if (window.cachedTabNum === 3 || !window.location.pathname.match(/\/tab\/\d+/)) {
        console.log('Skipping applyFilterToAllLevels for Tab 3 or non-tab page');
        return;
    }

    // For Tabs 1 and 5
    if (window.cachedTabNum === 1 || window.cachedTabNum === 5) {
        const categoryTable = document.getElementById('category-table');
        if (!categoryTable) {
            console.warn('Category table not found, skipping filter application');
            return;
        }

        const categoryRows = categoryTable.querySelectorAll('.category-row') || [];
        if (!categoryRows.length) {
            console.warn('No category rows found in table, skipping filter application');
            return;
        }

        let visibleCategoryRows = 0;

        categoryRows.forEach(categoryRow => {
            let showCategoryRow = true;
            const categoryCell = categoryRow.querySelector('td:nth-child(1)'); // Category column
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
                    console.warn(`Common tables not found for category ${categoryValue} (normalized: ${normalizedCategoryValue})`);
                    return;
                }

                let visibleSubcategories = 0;
                commonTables.forEach(commonTable => {
                    const commonRows = commonTable.querySelectorAll('tbody tr:not(.common-name-row)') || [];
                    let visibleCommonRows = 0;

                    commonRows.forEach((commonRow, index) => {
                        if (index % 2 !== 0) return;

                        let showCommonRow = true;
                        const commonNameCell = commonRow.querySelector('td:nth-child(1)'); // Common Name column
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
                                        const colOffset = window.cachedTabNum == 5 ? 1 : 0;
                                        const itemCommonNameCell = itemRow.querySelector(`td:nth-child(${2 + colOffset})`);
                                        const itemContractCell = itemRow.querySelector(`td:nth-child(${5 + colOffset})`);
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
                                        itemsDiv.style.display = 'block';
                                        itemsDiv.style.opacity = '0';
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

/**
 * Populate subcategories for Tab 5
 */
function populateSubcategories() {
    const selects = document.querySelectorAll('.subcategory-select');
    const promises = Array.from(selects).map(select => {
        const category = select.getAttribute('data-category');
        console.log(`Populating subcategories for ${category}`);
        const url = `/tab/5/subcat_data?category=${encodeURIComponent(category)}`;
        return fetch(url)
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
                } else {
                    select.innerHTML += '<option value="">No subcategories</option>';
                }
            })
            .catch(error => console.error(`Subcategory error for ${category}: ${error.message}`));
    });

    Promise.all(promises).catch(error => console.error('Error populating subcategories:', error));
}

/**
 * Load common names for Tab 5
 */
function loadCommonNames(selectElement, page = 1) {
    const subcategory = selectElement.value;
    const category = selectElement.getAttribute('data-category');
    const targetId = `common-${category.toLowerCase().replace(/[^a-z0-9]/g, '_')}`;
    const categoryRow = selectElement.closest('tr');
    const tbody = categoryRow.closest('tbody');

    console.log('loadCommonNames:', { subcategory, category, targetId, page });

    if (!subcategory && page === 1) {
        console.log('No subcategory, collapsing');
        const url = `/tab/5/subcat_data?category=${encodeURIComponent(category)}`;
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

    const url = `/tab/5/common_names?category=${encodeURIComponent(category)}&subcategory=${encodeURIComponent(subcategory)}&page=${page}`;
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
                        <table class="table table-bordered table-hover common-table" id="common-table-${targetId}" style="color: #000000 !important;">
                            <thead class="thead-dark">
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

            sessionStorage.setItem(`expanded_${targetId}`, JSON.stringify({ category, subcategory, page }));
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
 * Bulk update common name for Tab 5
 */
function bulkUpdateCommonName(category, subcategory, targetId, key) {
    const binLocation = document.getElementById(`bulk-bin-location-${key}`)?.value;
    const status = document.getElementById(`bulk-status-${key}`)?.value;

    if (!binLocation && !status) {
        alert('Select a Bin Location or Status.');
        return;
    }

    const commonTable = document.getElementById(`common-table-${key}`);
    const commonName = commonTable?.querySelector('tbody tr td:first-child')?.textContent;
    if (!commonName) {
        console.error('Common name not found for bulk update');
        alert('Error: Common name not found.');
        return;
    }

    const url = '/tab/5/bulk_update_common_name';
    fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            category,
            subcategory,
            common_name: commonName,
            bin_location: binLocation || undefined,
            status: status || undefined
        })
    })
        .then(response => {
            console.log(`Bulk update status: ${response.status}`);
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`Bulk update failed: ${response.status} - ${text}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                console.error('Bulk update error:', data.error);
                alert('Failed to bulk update: ' + data.error);
            } else {
                console.log('Bulk update successful');
                alert('Bulk update successful!');
                loadItems(category, subcategory, commonName, targetId);
            }
        })
        .catch(error => {
            console.error('Bulk update error:', error.message);
            alert('Error: ' + error.message);
        });
}

/**
 * Bulk update selected items for Tab 5
 */
function bulkUpdateSelectedItems(key) {
    const itemTable = document.getElementById(`item-table-${key}`);
    if (!itemTable) {
        console.error(`Item table ${key} not found`);
        alert('Error: Item table not found.');
        return;
    }

    const selectedItems = Array.from(itemTable.querySelectorAll('tbody input[type="checkbox"]:checked'))
        .map(checkbox => checkbox.value);

    if (!selectedItems.length) {
        alert('Select at least one item.');
        return;
    }

    const binLocation = document.getElementById(`bulk-item-bin-location-${key}`)?.value;
    const status = document.getElementById(`bulk-item-status-${key}`)?.value;

    if (!binLocation && !status) {
        alert('Select a Bin Location or Status.');
        return;
    }

    const url = '/tab/5/bulk_update_items';
    fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            tag_ids: selectedItems,
            bin_location: binLocation || undefined,
            status: status || undefined
        })
    })
        .then(response => {
            console.log(`Bulk update selected status: ${response.status}`);
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`Bulk update failed: ${response.status} - ${text}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                console.error('Bulk update error:', data.error);
                alert('Failed to bulk update: ' + data.error);
            } else {
                console.log('Bulk update successful');
                alert('Bulk update successful!');
                const category = document.querySelector(`#item-table-${key}`)?.closest('.common-level')?.querySelector('button[data-category]')?.getAttribute('data-category') ||
                                 document.querySelector(`#item-table-${key}`)?.closest('tr')?.previousElementSibling?.querySelector('button[data-category]')?.getAttribute('data-category');
                const subcategory = document.querySelector(`#item-table-${key}`)?.closest('.common-level')?.querySelector('button[data-subcategory]')?.getAttribute('data-subcategory') ||
                                    document.querySelector(`#item-table-${key}`)?.closest('tr')?.previousElementSibling?.querySelector('button[data-subcategory]')?.getAttribute('data-subcategory');
                const commonName = document.querySelector(`#common-table-${key} tbody tr td:first-child`)?.textContent;
                const targetId = document.querySelector(`#item-table-${key}`)?.closest('.expandable')?.id;
                if (category && subcategory && commonName && targetId) {
                    loadItems(category, subcategory, commonName, targetId);
                } else {
                    console.warn('Missing parameters for reload:', { category, subcategory, commonName, targetId });
                    window.location.reload();
                }
            }
        })
        .catch(error => {
            console.error('Bulk update error:', error.message);
            alert('Error: ' + error.message);
        });
}

/**
 * Update bulk field for Tab 5
 */
function updateBulkField(key, field) {
    const select = document.getElementById(`bulk-${field}-${key}`);
    if (select && select.value) {
        const otherField = field === 'bin_location' ? 'status' : 'bin_location';
        const otherSelect = document.getElementById(`bulk-${otherField}-${key}`);
        if (otherSelect) otherSelect.value = '';
    }
}

/**
 * Update individual item for Tab 5
 */
function updateItem(tagId, key, category, subcategory, commonName, targetId) {
    const binLocation = document.getElementById(`bin-location-${tagId}`)?.value;
    const status = document.getElementById(`status-${tagId}`)?.value;

    if (!binLocation && !status) {
        alert('Select a Bin Location or Status.');
        return;
    }

    const promises = [];

    if (binLocation) {
        const url = '/tab/5/update_bin_location';
        promises.push(
            fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tag_id: tagId, bin_location: binLocation })
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
                if (data.error) throw new Error(`Bin location error: ${data.error}`);
                return { field: 'bin_location', data };
            })
        );
    }

    if (status) {
        const url = '/tab/5/update_status';
        promises.push(
            fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tag_id: tagId, status })
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
                if (data.error) throw new Error(`Status error: ${data.error}`);
                return { field: 'status', data };
            })
        );
    }

    Promise.all(promises)
        .then(results => {
            console.log('Update successful');
            alert('Update successful!');
            loadItems(category, subcategory, commonName, targetId);
        })
        .catch(error => {
            console.error('Update error:', error.message);
            alert('Error: ' + error.message);
        });
}

/**
 * Load items for Tab 5
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

    container.innerHTML = '';

    const wrapper = document.createElement('div');
    wrapper.className = 'item-level-wrapper';
    container.appendChild(wrapper);

    const itemTable = document.createElement('table');
    itemTable.className = 'table table-bordered table-hover item-table';
    itemTable.id = `item-table-${key}`;
    itemTable.style.color = '#000000 !important';
    itemTable.innerHTML = `
        <thead class="thead-dark">
            <tr>
                <th style="color: #000000 !important;">Select</th>
                <th style="color: #000000 !important;">Tag ID</th>
                <th style="color: #000000 !important;">Common Name</th>
                <th style="color: #000000 !important;">Bin Location</th>
                <th style="color: #000000 !important;">Status</th>
                <th style="color: #000000 !important;">Last Contract</th>
                <th style="color: #000000 !important;">Last Scanned Date</th>
                <th style="color: #000000 !important;">Quality</th>
                <th style="color: #000000 !important;">Notes</th>
                <th style="color: #000000 !important;">Actions</th>
            </tr>
        </thead>
        <tbody style="min-height: 50px;">
            <tr>
                <td>-</td>
                <td style="color: #000000 !important;">Loading...</td>
                <td style="color: #000000 !important;">-</td>
                <td>-</td>
                <td>-</td>
                <td style="color: #000000 !important;">-</td>
                <td style="color: #000000 !important;">-</td>
                <td style="color: #000000 !important;">-</td>
                <td style="color: #000000 !important;">-</td>
                <td>-</td>
            </tr>
        </tbody>
    `;
    wrapper.appendChild(itemTable);

    const url = `/tab/5/data?common_name=${encodeURIComponent(commonName)}&page=${page}&subcategory=${encodeURIComponent(subcategory)}&category=${encodeURIComponent(category)}`;
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
                    const currentStatus = item.status || 'N/A';
                    const canSetReadyToRent = currentStatus === 'On Rent' || currentStatus === 'Delivered';
                    // Make bin_location comparison case-insensitive
                    const binLocationLower = item.bin_location ? item.bin_location.toLowerCase() : '';
                    const row = document.createElement('tr');
                    row.setAttribute('data-item-id', item.tag_id);
                    row.innerHTML = `
                        <td><input type="checkbox" value="${item.tag_id}" class="item-select"></td>
                        <td style="color: #000000 !important;">${item.tag_id}</td>
                        <td style="color: #000000 !important;">${item.common_name}</td>
                        <td>
                            <select id="bin-location-${item.tag_id}">
                                <option value="" ${!item.bin_location ? 'selected' : ''}>Select Bin Location</option>
                                <option value="resale" ${binLocationLower === 'resale' ? 'selected' : ''}>Resale</option>
                                <option value="sold" ${binLocationLower === 'sold' ? 'selected' : ''}>Sold</option>
                                <option value="pack" ${binLocationLower === 'pack' ? 'selected' : ''}>Pack</option>
                                <option value="burst" ${binLocationLower === 'burst' ? 'selected' : ''}>Burst</option>
                            </select>
                        </td>
                        <td>
                            <select id="status-${item.tag_id}">
                                <option value="${currentStatus}" selected>${currentStatus}</option>
                                <option value="Ready to Rent" ${canSetReadyToRent ? '' : 'disabled'}>Ready to Rent</option>
                                <option value="Sold">Sold</option>
                            </select>
                        </td>
                        <td style="color: #000000 !important;">${item.last_contract_num || 'N/A'}</td>
                        <td style="color: #000000 !important;">${lastScanned}</td>
                        <td style="color: #000000 !important;">${item.quality || 'N/A'}</td>
                        <td style="color: #000000 !important;">${item.notes || 'N/A'}</td>
                        <td>
                            <button class="btn btn-sm btn-primary save-btn" 
                                    onclick="updateItem('${item.tag_id}', '${key}', '${category}', '${subcategory}', '${item.common_name}', '${targetId}')">Save</button>
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

                const bulkDiv = document.createElement('div');
                bulkDiv.className = 'bulk-update-controls mt-3';
                bulkDiv.innerHTML = `
                    <h5>Bulk Update All Items</h5>
                    <div class="form-group">
                        <label for="bulk-bin-location-${key}">Bin Location:</label>
                        <select id="bulk-bin-location-${key}" onchange="updateBulkField('${key}', 'bin_location')">
                            <option value="">Select Bin Location</option>
                            <option value="resale">Resale</option>
                            <option value="sold">Sold</option>
                            <option value="pack">Pack</option>
                            <option value="burst">Burst</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="bulk-status-${key}">Status:</label>
                        <select id="bulk-status-${key}" onchange="updateBulkField('${key}', 'status')">
                            <option value="">Select Status</option>
                            <option value="Ready to Rent">Ready to Rent</option>
                            <option value="Sold">Sold</option>
                        </select>
                    </div>
                    <button class="btn btn-primary" onclick="bulkUpdateCommonName('${category}', '${subcategory}', '${targetId}', '${key}')">Update All</button>
                    <h5 class="mt-3">Bulk Update Selected Items</h5>
                    <div class="form-group">
                        <label for="bulk-item-bin-location-${key}">Bin Location:</label>
                        <select id="bulk-item-bin-location-${key}">
                            <option value="">Select Bin Location</option>
                            <option value="resale">Resale</option>
                            <option value="sold">Sold</option>
                            <option value="pack">Pack</option>
                            <option value="burst">Burst</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="bulk-item-status-${key}">Status:</label>
                        <select id="bulk-item-status-${key}">
                            <option value="">Select Status</option>
                            <option value="Ready to Rent">Ready to Rent</option>
                            <option value="Sold">Sold</option>
                        </select>
                    </div>
                    <button class="btn btn-primary" onclick="bulkUpdateSelectedItems('${key}')">Update Selected</button>
                `;
                wrapper.appendChild(bulkDiv);
            } else {
                tbody.innerHTML = `<tr><td colspan="10">No items found.</td></tr>`;
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
        })
        .catch(error => {
            console.error('Items error:', error.message);
            const tbody = itemTable.querySelector('tbody');
            tbody.innerHTML = `<tr><td colspan="10">Error: ${error.message}</td></tr>`;
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

/**
 * Update resale/pack items to sold status for Tab 5
 */
function updateResalePackToSold() {
    if (confirm('Are you sure you want to update all items with bin_location "resale" or "pack", status "On Rent" or "Delivered", and last scanned more than 4 days ago to status "Sold"?')) {
        console.log('Updating resale/pack items to sold status');
        fetch('/tab/5/update_resale_pack_to_sold', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            console.log(`Update resale/pack to sold status: ${response.status}`);
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`Update failed: ${response.status} - ${text}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                console.log('Update successful:', data.message);
                alert(data.message);
                // Since updates are asynchronous, we can't immediately refresh the table
                // Notify the user to check back later or manually refresh
                setTimeout(() => {
                    if (confirm('Updates are processing in the background. Would you like to refresh the page now to check the status?')) {
                        window.location.reload();
                    }
                }, 2000);
            } else {
                console.error('Update failed:', data.message);
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error updating items:', error.message);
            alert('Failed to update items: ' + error.message);
        });
    }
}

/**
 * Event listener for Tab 5
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('tab5.js: DOMContentLoaded');

    if (window.cachedTabNum !== 5) {
        console.log('Not Tab 5, skipping');
        return;
    }

    populateSubcategories();

    document.removeEventListener('click', handleClick);
    document.addEventListener('click', handleClick);

    function handleClick(event) {
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
                    collapseSection(targetId);
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
                collapseSection(targetId);
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
            const category = printBtn.getAttribute('data-category');
            const subcategory = printBtn.getAttribute('data-subcategory');
            const commonName = printBtn.getAttribute('data-common-name');
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
    }
});