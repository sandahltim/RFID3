import { formatDate } from './utils.js';
import { getCachedTabNum } from './state.js';
// app/static/js/tab1.js
// tab1.js version: 2025-09-25-v12-table-repopulation-fix
console.log('tab1.js version: 2025-09-25-v12-table-repopulation-fix loaded');

/**
 * Tab1.js: Logic for Tab 1 (Rental Inventory) - BEDROCK VERSION WITH GLOBALFILTERS INTEGRATION.
 * Dependencies: common.js (for formatDate, showLoading, hideLoading, collapseSection, printTable, printFullItemList).
 * Updated: 2025-09-25-v12-table-repopulation-fix
 *
 * CRITICAL FIX IN v12:
 * - FIXED: Table clearing but not repopulating with filtered data
 * - PROBLEM: After refreshDashboardData() cleared rows, loadMainCategoriesTable() wrongly assumed server-rendered data
 * - SOLUTION: Always rebuild table rows when category data is available, removed faulty else condition
 *
 * PREVIOUS FIXES IN v11:
 * - FIXED: 'tableBody is not defined' error in loadCommonNames catch block (scope issue)
 * - FIXED: 'Cannot read properties of undefined (reading replace)' error with null item names
 * - ADDED: Debugging for refreshDashboardData function detection in GlobalFilters
 *
 * PREVIOUS FIX IN v10:
 * - FIXED: Duplicate getCurrentFilters function causing syntax error and preventing script load
 * - RESULT: Store filtering should now work as GlobalFilters can call refreshDashboardData()
 *
 * MAJOR CHANGES IN v9:
 * - FIXED: Proper GlobalFilters integration - store filtering now works correctly
 * - ADDED: refreshDashboardData() function that GlobalFilters system calls when filters change
 * - ADDED: getCurrentFilters() with GlobalFilters integration and legacy fallback
 * - REMOVED: Incorrect event listeners looking for non-existent select[name="store"] elements
 * - ARCHITECTURE: Now properly integrated with global_filters.html GlobalFilters system
 * - BUG FIX: Store filtering dropdown changes now trigger table reload with new data
 *
 * PREVIOUS CHANGES IN v8:
 * - FIXED: Updated to use new /tab/1/categories bedrock endpoint instead of old endpoints
 * - FIXED: Store filtering now properly passes store/type parameters to API
 * - FIXED: Common names expansion JavaScript errors (tableBody undefined at line 516)
 * - FIXED: Store filtering synchronization with backend bedrock service
 * - ARCHITECTURE: Now compatible with bedrock transformation service and unified dashboard
 *
 * This version is synchronized with tab1.py routes version 2025-09-24-v27-ultra-optimized
 */

/**
 * Debounce function with Promise support
 */
function debounce(func, wait) {
    let timeout;
    let isProcessing = false;

    return function executedFunction(...args) {
        if (isProcessing) {
            console.log(`DEBUG: Request blocked - operation in progress at ${new Date().toISOString()}`);
            return Promise.resolve();
        }

        clearTimeout(timeout);
        isProcessing = true;
        console.log(`DEBUG: Setting isProcessing to true at ${new Date().toISOString()}`);

        return new Promise((resolve, reject) => {
            timeout = setTimeout(() => {
                func(...args)
                    .then(result => {
                        isProcessing = false;
                        console.log(`DEBUG: Setting isProcessing to false at ${new Date().toISOString()}`);
                        resolve(result);
                    })
                    .catch(error => {
                        isProcessing = false;
                        console.log(`DEBUG: Setting isProcessing to false after error at ${new Date().toISOString()}`);
                        reject(error);
                    });
            }, wait);
        });
    };
}

// REMOVED: Old duplicate getCurrentFilters function (replaced with GlobalFilters integration version below)

/**
 * Load main categories table using bedrock /tab/1/categories endpoint
 */
async function loadMainCategoriesTable() {
    console.log(`loadMainCategoriesTable: Starting at ${new Date().toISOString()}`);

    try {
        const filters = getCurrentFilters();
        console.log(`Loading categories with filters:`, filters, `at ${new Date().toISOString()}`);

        // Build query parameters
        const params = new URLSearchParams();
        if (filters.store && filters.store !== 'all') params.append('store', filters.store);
        if (filters.type && filters.type !== 'all') params.append('type', filters.type);
        if (filters.status) params.append('statusFilter', filters.status);
        if (filters.bin) params.append('binFilter', filters.bin);
        if (filters.search) params.append('filter', filters.search);

        const url = `/tab/1/categories?${params.toString()}`;
        console.log(`Fetching categories from: ${url} at ${new Date().toISOString()}`);

        const response = await fetch(url);
        console.log(`Categories fetch status: ${response.status} at ${new Date().toISOString()}`);

        if (!response.ok) {
            const text = await response.text();
            throw new Error(`Categories fetch failed: ${response.status} - ${text}`);
        }

        const data = await response.json();
        console.log(`Categories data received:`, data, `at ${new Date().toISOString()}`);

        // Update the main table
        const categoryTable = document.getElementById('category-table');
        if (!categoryTable) {
            console.error(`Category table not found at ${new Date().toISOString()}`);
            return;
        }

        const tbody = categoryTable.querySelector('tbody');
        if (!tbody) {
            console.error(`Category table tbody not found at ${new Date().toISOString()}`);
            return;
        }

        // Check if table already has data (server-side rendered) BEFORE clearing
        const existingRows = tbody.querySelectorAll('.category-row');
        const hasExistingData = existingRows.length > 0;

        // Only replace table data if we're updating filters or if table is empty
        const isInitialLoad = !hasExistingData;

        if (!isInitialLoad) {
            console.log(`Updating existing table with ${data.categories.length} categories at ${new Date().toISOString()}`);
        }

        // Populate/update table with new data
        if (data.categories && data.categories.length > 0) {
            // Always rebuild rows when we have category data to display
            // Clear existing rows
            tbody.innerHTML = '';

            data.categories.forEach(category => {
                    const categoryId = category.category.toLowerCase().replace(/[^a-z0-9]/g, '_');
                    const row = document.createElement('tr');
                    row.className = 'category-row';
                    row.innerHTML = `
                        <td>${category.category}</td>
                        <td>
                            <select class="subcategory-select form-control" data-category="${category.category}" onchange="tab1.loadCommonNames(this)">
                                <option value="">Select a subcategory</option>
                            </select>
                            <div id="loading-subcat-${categoryId}" class="loading-indicator" style="display: none;">Loading...</div>
                        </td>
                        <td>${category.total_items || 0}</td>
                        <td>${category.items_on_contracts || 0}</td>
                        <td>${category.items_requiring_service || 0}</td>
                        <td>${category.items_available || 0}</td>
                        <td>
                            <div class="btn-group">
                                <button class="btn btn-sm btn-info print-btn"
                                        data-print-level="Category"
                                        data-print-id="category-table">Print</button>
                            </div>
                        </td>
                    `;
                    tbody.appendChild(row);

                    // Add expansion row
                    const expansionRow = document.createElement('tr');
                    expansionRow.innerHTML = `
                        <td colspan="7">
                            <div id="common-${categoryId}" class="common-level"></div>
                        </td>
                    `;
                    tbody.appendChild(expansionRow);
                });

                console.log(`Updated table with ${data.categories.length} categories at ${new Date().toISOString()}`);

                // Populate subcategories for each category
                await populateSubcategories();

        } else {
            tbody.innerHTML = '<tr><td colspan="7">No categories found with current filters</td></tr>';
            console.warn(`No categories returned with current filters at ${new Date().toISOString()}`);
        }

    } catch (error) {
        console.error(`Error loading main categories table: ${error.message} at ${new Date().toISOString()}`);
        const categoryTable = document.getElementById('category-table');
        if (categoryTable) {
            const tbody = categoryTable.querySelector('tbody');
            if (tbody) {
                tbody.innerHTML = `<tr><td colspan="6">Error loading categories: ${error.message}</td></tr>`;
            }
        }
    }
}

/**
 * Get current filter values from GlobalFilters (for GlobalFilters integration)
 */
function getCurrentFilters() {
    // Integration with GlobalFilters system from global_filters.html
    if (window.GlobalFilters) {
        const params = window.GlobalFilters.getApiParams();
        console.log(`getCurrentFilters: Using GlobalFilters system:`, params, `at ${new Date().toISOString()}`);
        return {
            store: params.store,
            type: params.type
        };
    } else {
        // Fallback for manual form elements (legacy)
        const storeSelect = document.querySelector('select[name="store"]');
        const typeSelect = document.querySelector('select[name="type"]');
        const statusInput = document.querySelector('input[name="statusFilter"]');
        const binInput = document.querySelector('input[name="binFilter"]');
        const searchInput = document.querySelector('input[name="category-filter"]');

        const filters = {
            store: storeSelect ? storeSelect.value : 'all',
            type: typeSelect ? typeSelect.value : 'all',
            status: statusInput ? statusInput.value : '',
            bin: binInput ? binInput.value : '',
            search: searchInput ? searchInput.value : ''
        };
        console.log(`getCurrentFilters: Using legacy form elements:`, filters, `at ${new Date().toISOString()}`);
        return filters;
    }
}

/**
 * GlobalFilters integration function - called by GlobalFilters system when filters change
 */
window.refreshDashboardData = async function() {
    console.log(`refreshDashboardData: Called by GlobalFilters at ${new Date().toISOString()}`);

    // Clear existing table data to force reload with new filters
    const categoryTable = document.getElementById('category-table');
    if (categoryTable) {
        const tbody = categoryTable.querySelector('tbody');
        if (tbody) {
            const existingRows = tbody.querySelectorAll('.category-row');
            if (existingRows.length > 0) {
                console.log(`refreshDashboardData: Clearing ${existingRows.length} existing rows for reload at ${new Date().toISOString()}`);
                tbody.innerHTML = '';
            }
        }
    }

    // Reload table with current GlobalFilters
    try {
        await loadMainCategoriesTable();
        console.log(`refreshDashboardData: Successfully reloaded Tab 1 data at ${new Date().toISOString()}`);
    } catch (error) {
        console.error(`refreshDashboardData: Error reloading Tab 1 data: ${error.message} at ${new Date().toISOString()}`);
    }
};

/**
 * Apply filters to all levels for Tab 1
 */
function applyFilterToAllLevelsTab1() {
    console.log(`applyFilterToAllLevelsTab1: Starting at ${new Date().toISOString()}`);
    if (getCachedTabNum() === 3 || !window.location.pathname.match(/\/tab\/\d+/)) {
        console.log(`Skipping applyFilterToAllLevels for Tab 3 or non-tab page at ${new Date().toISOString()}`);
        return;
    }

    if (getCachedTabNum() === 1 || getCachedTabNum() === 5) {
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

                                    let itemRowCountDiv = itemTable.nextSibling;
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

                    let commonRowCountDiv = commonTable.nextSibling;
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
 * Populate subcategory dropdowns
 */
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

/**
 * Load common names for a subcategory
 */
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
            if (!tableBody) {
                console.error(`Table body not found in headerRow at ${new Date().toISOString()}`);
                return;
            }
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
                    // Add null checks to prevent replace errors
                    const itemName = item.name || 'Unknown';
                    const rowId = `${targetId}_${itemName.replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '')}`;
                    const escapedName = itemName; // No escaping needed for data attributes
                    const commonRow = document.createElement('tr');
                    commonRow.innerHTML = `
                        <td>${itemName}</td>
                        <td>${item.total_items || '0'}</td>
                        <td>${item.items_on_contracts || '0'}</td>
                        <td>${item.items_in_service || '0'}</td>
                        <td>${item.items_available || '0'}</td>
                        <td>
                            <div class="btn-group">
                                <button class="btn btn-sm btn-secondary expand-btn"
                                        data-category="${category}"
                                        data-subcategory="${subcategory}"
                                        data-common-name='${escapedName}'
                                        data-target-id="items-${rowId}"
                                        data-expanded="false">Expand Items</button>
                                <button class="btn btn-sm btn-secondary collapse-btn" 
                                        data-collapse-target="items-${rowId}" 
                                        style="display:none;">Collapse</button>
                                <button class="btn btn-sm btn-info print-btn"
                                        data-print-level="Common Name"
                                        data-print-id="common-table-${targetId}"
                                        data-common-name='${escapedName}'
                                        data-category="${category}"
                                        data-subcategory="${subcategory}">Print Aggregate</button>
                                <button class="btn btn-sm btn-info print-full-btn"
                                        data-common-name='${escapedName}'
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
                            <div id="items-${rowId}" class="expandable item-level collapsed"></div>
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
                tableBody.innerHTML = `<tr><td colspan="6">No common names found.</td></tr>`;
                console.warn(`No common names returned for category ${category}, subcategory ${subcategory} at ${new Date().toISOString()}`);
            }

            sessionStorage.setItem(`expanded_${targetId}`, JSON.stringify({ category, subcategory, page }));
        })
        .catch(error => {
            console.error(`Common names error: ${error.message} at ${new Date().toISOString()}`);

            // Find the table body to display error (tableBody was out of scope)
            let errorHeaderRow = categoryRow.parentNode.querySelector(`tr.common-name-row[data-target-id="${targetId}"] .common-table`);
            if (errorHeaderRow) {
                const errorTableBody = errorHeaderRow.querySelector('tbody');
                if (errorTableBody) {
                    errorTableBody.innerHTML = `<tr><td colspan="6">Error: ${error.message}</td></tr>`;
                } else {
                    console.error(`Error table body not found for error display at ${new Date().toISOString()}`);
                }
            } else {
                console.error(`Error header row not found for error display at ${new Date().toISOString()}`);
            }
        })
        .finally(() => {
            setTimeout(() => {
                if (loadingDiv) loadingDiv.style.display = 'none';
            }, 700);
        });
}

/**
 * Load individual items for a common name
 */
async function loadItems(category, subcategory, commonName, targetId, page = 1) {
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

    const url = `/tab/1/data?common_name=${encodeURIComponent(commonName)}&page=${page}&subcategory=${encodeURIComponent(subcategory)}&category=${encodeURIComponent(category)}`;
    console.log(`Fetching items: ${url} at ${new Date().toISOString()}`);

    try {
        const response = await fetch(url);
        console.log(`Items fetch status: ${response.status} at ${new Date().toISOString()}`);
        if (!response.ok) {
            throw new Error(`Items fetch failed: ${response.status}`);
        }
        const data = await response.json();
        console.log(`Items data:`, data, `at ${new Date().toISOString()}`);
        const tbody = itemTable.querySelector('tbody');
        tbody.innerHTML = '';

        if (data.items && data.items.length > 0) {
            data.items.forEach(item => {
                const lastScanned = formatDate(item.last_scanned_date);
                const currentStatus = item.status || 'N/A';
                const currentQuality = item.quality || '';
                const binLocationLower = item.bin_location ? item.bin_location.toLowerCase() : '';
                const row = document.createElement('tr');
                row.setAttribute('data-item-id', item.tag_id);
                row.innerHTML = `
                    <td class="editable" data-field="tag_id">${item.tag_id}</td>
                    <td>${item.common_name}</td>
                    <td class="editable" data-field="bin_location">
                        <span class="cell-content">${item.bin_location || 'N/A'}</span>
                        <div class="edit-container" style="display: none;">
                            <select class="edit-select">
                                <option value="" ${!item.bin_location ? 'selected' : ''}>Select Bin Location</option>
                                <option value="resale" ${binLocationLower === 'resale' ? 'selected' : ''}>Resale</option>
                                <option value="sold" ${binLocationLower === 'sold' ? 'selected' : ''}>Sold</option>
                                <option value="pack" ${binLocationLower === 'pack' ? 'selected' : ''}>Pack</option>
                                <option value="burst" ${binLocationLower === 'burst' ? 'selected' : ''}>Burst</option>
                            </select>
                            <button class="btn btn-sm btn-success save-btn">Save</button>
                            <button class="btn btn-sm btn-secondary cancel-btn">Cancel</button>
                        </div>
                    </td>
                    <td class="editable" data-field="status">
                        <span class="cell-content">${currentStatus}</span>
                        <div class="edit-container" style="display: none;">
                            <select class="edit-select">
                                <option value="${currentStatus}" selected>${currentStatus}</option>
                                <option value="Ready to Rent">Ready to Rent</option>
                                <option value="Sold">Sold</option>
                                <option value="Repair">Repair</option>
                                <option value="Needs to be Inspected">Needs to be Inspected</option>
                                <option value="Wash">Wash</option>
                                <option value="Wet">Wet</option>
                            </select>
                            <button class="btn btn-sm btn-success save-btn">Save</button>
                            <button class="btn btn-sm btn-secondary cancel-btn">Cancel</button>
                        </div>
                    </td>
                    <td>${item.last_contract_num || 'N/A'}</td>
                    <td>${lastScanned}</td>
                    <td class="editable" data-field="quality">
                        <span class="cell-content">${currentQuality || 'N/A'}</span>
                        <div class="edit-container" style="display: none;">
                            <select class="edit-select">
                                <option value="" ${!currentQuality ? 'selected' : ''}>Select Quality</option>
                                <option value="A+" ${currentQuality === 'A+' ? 'selected' : ''}>A+</option>
                                <option value="A" ${currentQuality === 'A' ? 'selected' : ''}>A</option>
                                <option value="A-" ${currentQuality === 'A-' ? 'selected' : ''}>A-</option>
                                <option value="B+" ${currentQuality === 'B+' ? 'selected' : ''}>B+</option>
                                <option value="B" ${currentQuality === 'B' ? 'selected' : ''}>B</option>
                                <option value="B-" ${currentQuality === 'B-' ? 'selected' : ''}>B-</option>
                                <option value="C+" ${currentQuality === 'C+' ? 'selected' : ''}>C+</option>
                                <option value="C" ${currentQuality === 'C' ? 'selected' : ''}>C</option>
                                <option value="C-" ${currentQuality === 'C-' ? 'selected' : ''}>C-</option>
                            </select>
                            <button class="btn btn-sm btn-success save-btn">Save</button>
                            <button class="btn btn-sm btn-secondary cancel-btn">Cancel</button>
                        </div>
                    </td>
                    <td class="editable" data-field="notes">
                        <span class="cell-content">${item.notes || 'N/A'}</span>
                        <div class="edit-container" style="display: none;">
                            <input class="edit-input" type="text" value="${item.notes || ''}">
                            <button class="btn btn-sm btn-success save-btn">Save</button>
                            <button class="btn btn-sm btn-secondary cancel-btn">Cancel</button>
                        </div>
                    </td>
                    <td>
                        <button class="btn btn-sm btn-primary print-btn"
                                data-print-level="Item"
                                data-print-id="item-${item.tag_id}"
                                data-common-name='${commonName}'
                                data-category="${category}">Print</button>
                    </td>
                `;
                tbody.appendChild(row);
            });

            const paginationDiv = document.createElement('div');
            paginationDiv.className = 'pagination-controls';
            if (data.total_items > data.per_page) {
                const totalPages = Math.ceil(data.total_items / data.per_page);
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
            tbody.innerHTML = `<tr><td colspan="9">No items found.</td></tr>`;
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
const debouncedSaveEdit = debounce(async (cell, tagId, field, category, subcategory, commonName, targetId, value) => {
    console.log(`saveEdit: Starting at ${new Date().toISOString()}`, { tagId, field, category, subcategory, commonName, targetId, value });
    if (!tagId || !field) {
        console.error(`Invalid parameters for saveEdit: tagId=${tagId}, field=${field} at ${new Date().toISOString()}`);
        alert(`Error: Missing tag ID or field`);
        return;
    }

    const validStatuses = ['Ready to Rent', 'Sold', 'Repair', 'Needs to be Inspected', 'Wash', 'Wet'];
    const validQualities = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', ''];
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

    const url = `/tab/1/update_${field}`;
    try {
        const currentTime = new Date().toISOString().replace('Z', '+00:00');
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                tag_id: tagId,
                [field]: value || '',
                date_updated: currentTime
            })
        });
        console.log(`Update ${field} status for ${tagId}: ${response.status} at ${new Date().toISOString()}`);
        if (!response.ok) {
            const text = await response.text();
            throw new Error(`Update ${field} failed: ${response.status} - ${text}`);
        }
        const data = await response.json();
        if (data.error) {
            console.error(`Update ${field} error: ${data.error} at ${new Date().toISOString()}`);
            alert(`Failed to update ${field}: ${data.error}`);
        } else {
            console.log(`Update ${field} successful at ${new Date().toISOString()}`);
            await loadItems(category, subcategory, commonName, targetId); // Refresh UI
        }
    } catch (error) {
        console.error(`Update ${field} error: ${error.message} at ${new Date().toISOString()}`);
        alert(`Error updating ${field}: ${error.message}`);
    }
}, 500);

/**
 * Initialize the page and handle click events
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log(`tab1.js: DOMContentLoaded at ${new Date().toISOString()}`);
    const isTab1 = window.location.pathname.match(/\/tab\/1\b/);
    console.log(`isTab1: ${isTab1}, getCachedTabNum(): ${getCachedTabNum()}, pathname: ${window.location.pathname} at ${new Date().toISOString()}`);

    if (!isTab1 && getCachedTabNum() !== 1) {
        console.log(`Not Tab 1, skipping at ${new Date().toISOString()}`);
        return;
    }

    console.log(`Initializing Tab 1 BEDROCK VERSION at ${new Date().toISOString()}`);

    // Check if we already have server-rendered data
    const categoryTable = document.getElementById('category-table');
    if (categoryTable) {
        const existingRows = categoryTable.querySelectorAll('.category-row');
        if (existingRows.length > 0) {
            console.log(`Found ${existingRows.length} server-rendered categories, skipping initial API load at ${new Date().toISOString()}`);
            // Just populate subcategories for existing data
            populateSubcategories().then(() => {
                console.log(`Subcategories populated for existing data at ${new Date().toISOString()}`);
            });
        } else {
            console.log(`No server-rendered data found, loading from API at ${new Date().toISOString()}`);
            // Load from API
            loadMainCategoriesTable().then(() => {
                console.log(`Main categories table loaded from API at ${new Date().toISOString()}`);
            }).catch(error => {
                console.error(`Error loading main categories table: ${error.message} at ${new Date().toISOString()}`);
            });
        }
    } else {
        console.warn(`Category table not found during initialization at ${new Date().toISOString()}`);
    }

    // Set up event handlers
    document.removeEventListener('click', handleClick);
    document.addEventListener('click', handleClick);

    // REMOVED: Old incorrect event listeners that looked for non-existent elements
    // Store/type filtering now handled by GlobalFilters system in global_filters.html
    // which calls refreshDashboardData() when filters change

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
            event.preventDefault();
            event.stopPropagation();
            console.log(`Editable cell clicked: field=${editableCell.getAttribute('data-field')} at ${new Date().toISOString()}`);
            const field = editableCell.getAttribute('data-field');
            const row = editableCell.closest('tr');
            const tagId = row.getAttribute('data-item-id');
            const commonName = row.querySelector('td:nth-child(2)').textContent;

            // Traverse to find subcategory and category
            const commonNameRow = row.closest('.common-name-row');
            let categoryRow = null;
            let subcatSelect = null;
            let subcategory = '';
            let category = '';

            // Find the preceding category row
            let prevSibling = commonNameRow.previousElementSibling;
            while (prevSibling) {
                if (prevSibling.classList.contains('category-row')) {
                    categoryRow = prevSibling;
                    break;
                }
                prevSibling = prevSibling.previousElementSibling;
            }

            if (categoryRow) {
                subcatSelect = categoryRow.querySelector('.subcategory-select');
                if (subcatSelect) {
                    subcategory = subcatSelect.value;
                    category = subcatSelect.getAttribute('data-category');
                }
            }

            // Fallback to expand button's data-subcategory if select not found
            if (!subcategory) {
                const expandBtn = commonNameRow.previousElementSibling?.querySelector('.expand-btn');
                if (expandBtn) {
                    subcategory = expandBtn.getAttribute('data-subcategory') || '';
                    category = expandBtn.getAttribute('data-category') || '';
                }
            }

            const targetId = row.closest('.expandable').id;

            if (!subcategory) {
                console.warn(`Subcategory not found for editable cell: field=${field}, tagId=${tagId} at ${new Date().toISOString()}`);
                alert('Please select a subcategory before editing.');
                return;
            }

            const cellContent = editableCell.querySelector('.cell-content');
            const editContainer = editableCell.querySelector('.edit-container');
            const select = editContainer.querySelector('.edit-select');
            const input = editContainer.querySelector('.edit-input');
            const saveBtn = editContainer.querySelector('.save-btn');
            const cancelBtn = editContainer.querySelector('.cancel-btn');

            // Hide all other edit containers
            document.querySelectorAll('.edit-container').forEach(container => {
                container.style.display = 'none';
                container.parentElement.querySelector('.cell-content').style.display = 'block';
            });

            if (editContainer) {
                cellContent.style.display = 'none';
                editContainer.style.display = 'flex';
                (select || input).focus();
                console.log(`Showing edit container for field=${field}, tagId=${tagId} at ${new Date().toISOString()}`);

                const saveChanges = () => {
                    const value = select ? select.value : input ? input.value : '';
                    console.log(`Saving value: ${value} for field=${field}, tagId=${tagId} at ${new Date().toISOString()}`);
                    debouncedSaveEdit(editableCell, tagId, field, category, subcategory, commonName, targetId, value)
                        .then(() => {
                            editContainer.style.display = 'none';
                            cellContent.style.display = 'block';
                        })
                        .catch(error => {
                            console.error(`Save failed for field=${field}, tagId=${tagId}: ${error} at ${new Date().toISOString()}`);
                        });
                    saveBtn.removeEventListener('click', saveChanges);
                    cancelBtn.removeEventListener('click', revert);
                };

                const revert = () => {
                    console.log(`Cancelling edit for field=${field}, tagId=${tagId} at ${new Date().toISOString()}`);
                    editContainer.style.display = 'none';
                    cellContent.style.display = 'block';
                    saveBtn.removeEventListener('click', saveChanges);
                    cancelBtn.removeEventListener('click', revert);
                };

                saveBtn.addEventListener('click', saveChanges);
                cancelBtn.addEventListener('click', revert);

                if (input) {
                    const handleKeypress = (e) => {
                        if (e.key === 'Enter') {
                            saveChanges();
                        }
                    };
                    input.addEventListener('keypress', handleKeypress);
                    input.addEventListener('keypress', () => input.removeEventListener('keypress', handleKeypress), { once: true });
                }
            } else {
                console.warn(`No edit container found for editable cell: field=${field}, tagId=${tagId} at ${new Date().toISOString()}`);
            }
        }
    }
});

if (!window.tab1) {
    window.tab1 = {};
}
window.tab1.loadCommonNames = loadCommonNames;