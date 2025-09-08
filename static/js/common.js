import { getCachedTabNum } from './state.js';
console.log('common.js version: 2025-05-29-v24 loaded');

/**
 * Common.js: Shared utilities for all tabs.
 * Dependencies: None (self-contained for printing, formatting, and pagination).
 * Note: Changes here affect all tabs. Modify with caution to avoid breaking functionality.
 */

/**
 * Global filter state
 * Used by: Tabs 1, 2, 4, 5
 */
window.globalFilter = {
    commonName: '',
    contractNumber: ''
};

/**
 * Global sorting state for common names and items
 * Used by: Tabs 2, 4
 */
window.commonSortState = {};
window.itemSortState = {};

/**
 * Format ISO date strings into "Thurs, Aug 21 2025 4:55 pm"
 * Used by: All tabs (for printing and display)
 */
function formatDate(isoDateString) {
    if (!isoDateString || isoDateString === 'N/A') return 'N/A';
    try {
        const date = new Date(isoDateString);
        if (isNaN(date.getTime())) return 'N/A';

        const days = ['Sun', 'Mon', 'Tues', 'Wed', 'Thurs', 'Fri', 'Sat'];
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

        const dayName = days[date.getDay()];
        const monthName = months[date.getMonth()];
        const day = date.getDate();
        const year = date.getFullYear();

        let hours = date.getHours();
        const minutes = date.getMinutes().toString().padStart(2, '0');
        const ampm = hours >= 12 ? 'pm' : 'am';
        hours = hours % 12 || 12;

        return `${dayName}, ${monthName} ${day} ${year} ${hours}:${minutes} ${ampm}`;
    } catch (error) {
        console.error('Error formatting date:', isoDateString, error);
        return 'N/A';
    }
}

/**
 * Wrapper for formatDate to maintain consistency
 * Used by: All tabs
 */
function formatDateTime(dateTimeStr) {
    return formatDate(dateTimeStr);
}

/**
 * Show loading indicator
 * Used by: Tabs 1, 2, 4, 5
 * Dependency: CSS (.loading-indicator)
 */
function showLoading(targetId) {
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
 * Used by: Tabs 1, 2, 4, 5
 * Dependency: None
 */
function hideLoading(targetId) {
    const loadingDiv = document.getElementById(`loading-${targetId}`);
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

/**
 * Collapse section (common names or items level)
 * Used by: Tabs 1, 2, 4, 5
 * Dependency: sessionStorage
 */
function collapseSection(targetId) {
    const section = document.getElementById(targetId);
    if (section) {
        section.classList.remove('expanded');
        section.classList.add('collapsed');
        section.style.display = 'none';
        section.style.opacity = '0';
        const collapseBtn = document.querySelector(`button[data-collapse-target="${targetId}"]`);
        const expandBtn = collapseBtn ? collapseBtn.previousElementSibling : null;
        if (expandBtn && collapseBtn) {
            expandBtn.style.display = 'inline-block';
            collapseBtn.style.display = 'none';
        } else {
            console.warn(`Expand/collapse buttons not found for ${targetId}`);
        }
        sessionStorage.removeItem(`expanded_${targetId}`);
        sessionStorage.removeItem(`expanded_items_${targetId}`);
    } else {
        console.error(`Section ${targetId} not found for collapsing`);
    }
}

/**
 * Refresh the current tab
 * Used by: All tabs (via refresh buttons)
 */
function refreshTab() {
    window.location.reload();
}

/**
 * Normalize common name by removing quotes and extra spaces
 * Used by: All tabs (via printFullItemList)
 */
function normalizeCommonName(commonName) {
    return commonName.replace(/['"]/g, '').replace(/\s+/g, ' ').trim();
}

/**
 * Render pagination controls
 * Used by: All tabs for parent and expanded layers
 * @param {HTMLElement} container - The container to render pagination controls
 * @param {number} totalItems - Total number of items
 * @param {number} currentPage - Current page number
 * @param {number} perPage - Items per page
 * @param {function} onPageChange - Callback to handle page changes
 */
function renderPaginationControls(container, totalItems, currentPage, perPage, onPageChange) {
    if (!container) return;

    const totalPages = Math.ceil(totalItems / perPage);
    container.innerHTML = '';

    if (totalPages <= 1) return;

    const nav = document.createElement('nav');
    nav.setAttribute('aria-label', 'Pagination');
    const ul = document.createElement('ul');
    ul.className = 'pagination justify-content-center';

    // Previous button
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
    const prevLink = document.createElement('a');
    prevLink.className = 'page-link';
    prevLink.href = '#';
    prevLink.textContent = 'Previous';
    prevLink.addEventListener('click', (e) => {
        e.preventDefault();
        if (currentPage > 1) onPageChange(currentPage - 1);
    });
    prevLi.appendChild(prevLink);
    ul.appendChild(prevLi);

    // Page numbers (show up to 5 pages around current)
    const maxPagesToShow = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxPagesToShow / 2));
    let endPage = Math.min(totalPages, startPage + maxPagesToShow - 1);
    if (endPage - startPage + 1 < maxPagesToShow) {
        startPage = Math.max(1, endPage - maxPagesToShow + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
        const li = document.createElement('li');
        li.className = `page-item ${i === currentPage ? 'active' : ''}`;
        const link = document.createElement('a');
        link.className = 'page-link';
        link.href = '#';
        link.textContent = i;
        link.addEventListener('click', (e) => {
            e.preventDefault();
            onPageChange(i);
        });
        li.appendChild(link);
        ul.appendChild(li);
    }

    // Next button
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
    const nextLink = document.createElement('a');
    nextLink.className = 'page-link';
    nextLink.href = '#';
    nextLink.textContent = 'Next';
    nextLink.addEventListener('click', (e) => {
        e.preventDefault();
        if (currentPage < totalPages) onPageChange(currentPage + 1);
    });
    nextLi.appendChild(nextLink);
    ul.appendChild(nextLi);

    nav.appendChild(ul);
    container.appendChild(nav);
}

/**
 * Apply filter to a specific table (used for Tabs 2 and 4)
 * Used by: Tabs 2, 4
 * Dependency: window.globalFilter, DOM
 */
function applyFilterToTable(table) {
    if (!table) {
        console.warn('Table element is null, skipping applyFilterToTable');
        return;
    }

    const rows = table.querySelectorAll('tbody tr:not(.expandable)') || [];
    if (!rows.length) {
        console.warn('No rows found in table, skipping applyFilterToTable');
        return;
    }

    let visibleRows = 0;

    if (!window.globalFilter.commonName && !window.globalFilter.contractNumber) {
        rows.forEach(row => {
            row.style.display = '';
            visibleRows++;
            const expandableRow = row.nextElementSibling;
            if (expandableRow && expandableRow.classList.contains('expandable')) {
                expandableRow.style.display = '';
                const childTable = expandableRow.querySelector('.common-table, .item-table');
                if (childTable) {
                    applyFilterToTable(childTable);
                }
            }
        });
    } else {
        rows.forEach(row => {
            let showRow = true;

            const contractCell = row.querySelector('td:nth-child(1)');
            const commonNameCell = row.querySelector('td:nth-child(2), td:nth-child(1)');
            const contractValue = contractCell ? contractCell.textContent.toLowerCase() : '';
            const commonNameValue = commonNameCell ? commonNameCell.textContent.toLowerCase() : '';

            if (window.globalFilter.contractNumber && !contractValue.includes(window.globalFilter.contractNumber)) {
                showRow = false;
            }
            if (window.globalFilter.commonName && !commonNameValue.includes(window.globalFilter.commonName)) {
                showRow = false;
            }

            let hasMatchingChildren = false;
            const expandableRow = row.nextElementSibling;
            if (expandableRow && expandableRow.classList.contains('expandable') && expandableRow.classList.contains('expanded')) {
                const childTable = expandableRow.querySelector('.common-table, .item-table');
                if (childTable) {
                    const childRows = childTable.querySelectorAll('tbody tr:not(.expandable)') || [];
                    childRows.forEach(childRow => {
                        let showChildRow = true;
                        const childContractCell = childRow.querySelector('td:nth-child(1)');
                        const childCommonNameCell = childRow.querySelector('td:nth-child(2), td:nth-child(1)');
                        const childContractValue = childContractCell ? childContractCell.textContent.toLowerCase() : '';
                        const childCommonNameValue = childCommonNameCell ? childCommonNameCell.textContent.toLowerCase() : '';

                        if (window.globalFilter.contractNumber && !childContractValue.includes(window.globalFilter.contractNumber)) {
                            showChildRow = false;
                        }
                        if (window.globalFilter.commonName && !childCommonNameValue.includes(window.globalFilter.commonName)) {
                            showChildRow = false;
                        }

                        childRow.style.display = showChildRow ? '' : 'none';
                        if (showChildRow) hasMatchingChildren = true;
                    });

                    const visibleChildRows = Array.from(childRows).filter(r => r.style.display !== 'none').length;
                    let childRowCountDiv = childTable.nextElementSibling;
                    if (childRowCountDiv && !childRowCountDiv.classList.contains('row-count')) {
                        childRowCountDiv = document.createElement('div');
                        childRowCountDiv.className = 'row-count mt-2';
                        childTable.insertAdjacentElement('afterend', childRowCountDiv);
                    }
                    if (childRowCountDiv) {
                        childRowCountDiv.textContent = `Showing ${visibleChildRows} of ${childRows.length} rows`;
                    }
                }
            }

            if (showRow || hasMatchingChildren) {
                row.style.display = '';
                visibleRows++;
                if (expandableRow) {
                    expandableRow.style.display = '';
                    if (hasMatchingChildren) {
                        expandableRow.classList.remove('collapsed');
                        expandableRow.classList.add('expanded');
                        expandableRow.style.opacity = '1';
                        const expandBtn = row.querySelector('.expand-btn');
                        const collapseBtn = row.querySelector('.collapse-btn');
                        if (expandBtn && collapseBtn) {
                            expandBtn.style.display = 'none';
                            collapseBtn.style.display = 'inline-block';
                        }
                    }
                }
            } else {
                row.style.display = 'none';
                if (expandableRow) {
                    expandableRow.style.display = 'none';
                    expandableRow.classList.remove('expanded');
                    expandableRow.classList.add('collapsed');
                    expandableRow.style.opacity = '0';
                    const expandBtn = row.querySelector('.expand-btn');
                    const collapseBtn = row.querySelector('.collapse-btn');
                    if (expandBtn && collapseBtn) {
                        expandBtn.style.display = 'inline-block';
                        collapseBtn.style.display = 'none';
                    }
                }
            }
        });
    }
    
    // Update row count after DOM operations
    let rowCountDiv = table.nextElementSibling;
    while (rowCountDiv && !rowCountDiv.classList.contains('row-count') && !rowCountDiv.classList.contains('pagination-controls')) {
        rowCountDiv = rowCountDiv.nextElementSibling;
    }
    if (!rowCountDiv || !rowCountDiv.classList.contains('row-count')) {
        rowCountDiv = document.createElement('div');
        rowCountDiv.className = 'row-count mt-2';
        table.insertAdjacentElement('afterend', rowCountDiv);
    }
    rowCountDiv.textContent = `Showing ${visibleRows} of ${rows.length} rows`;
}

// Expose shared helpers for tab modules
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.collapseSection = collapseSection;
window.refreshTab = refreshTab;
window.normalizeCommonName = normalizeCommonName;
window.renderPaginationControls = renderPaginationControls;
window.applyFilterToTable = applyFilterToTable;

/**
 * Apply filter to all levels for Tabs 2 and 4
 * Used by: Tabs 2, 4
 * Dependency: window.globalFilter, applyFilterToTable
 */
function applyFilterToAllLevelsTabs2And4() {
    // Skip filtering for Tab 3 and non-tab pages
    const tabNum = getCachedTabNum();
    if (tabNum === 3 || !window.location.pathname.match(/\/tab\/\d+/)) {
        console.log('Skipping applyFilterToAllLevels for Tab 3 or non-tab page');
        return;
    }

    const categoryTable = document.getElementById('category-table');
    if (!categoryTable) {
        console.warn('Category table not found, skipping filter application');
        return;
    }

    const categoryRows = categoryTable.querySelectorAll('tbody tr:not(.expandable)') || [];
    if (!categoryRows.length) {
        console.warn('No category rows found in table, skipping filter application');
        return;
    }

    let visibleCategoryRows = 0;

    categoryRows.forEach(categoryRow => {
        let showCategoryRow = false;
        const contractCell = categoryRow.querySelector('td:nth-child(1)');
        const contractValue = contractCell ? contractCell.textContent.toLowerCase() : '';
        const expandableRow = categoryRow.nextElementSibling;
        const subcatDiv = expandableRow ? expandableRow.querySelector('.expandable') : null;

        if (window.globalFilter.contractNumber) {
            if (contractValue.includes(window.globalFilter.contractNumber)) {
                showCategoryRow = true;
            }
        } else {
            showCategoryRow = true;
        }

        let hasMatchingItems = false;
        if (subcatDiv && subcatDiv.classList.contains('expanded')) {
            const commonTable = subcatDiv.querySelector('.common-table');
            if (commonTable) {
                const commonRows = commonTable.querySelectorAll('tbody tr:not(.expandable)') || [];
                let visibleCommonRows = 0;

                commonRows.forEach(commonRow => {
                    let showCommonRow = false;
                    const commonNameCell = commonRow.querySelector('td:nth-child(1)');
                    const commonNameValue = commonNameCell ? commonNameCell.textContent.toLowerCase() : '';

                    if (window.globalFilter.commonName) {
                        if (commonNameValue.includes(window.globalFilter.commonName)) {
                            showCommonRow = true;
                        }
                    } else {
                        showCommonRow = true;
                    }

                    const commonExpandableRow = commonRow.nextElementSibling;
                    let visibleItemRows = 0;
                    if (commonExpandableRow && commonExpandableRow.classList.contains('expandable') && commonExpandableRow.classList.contains('expanded')) {
                        const itemTable = commonExpandableRow.querySelector('.item-table');
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
                                commonExpandableRow.classList.remove('collapsed');
                                commonExpandableRow.classList.add('expanded');
                                commonExpandableRow.style.display = 'block';
                                commonExpandableRow.style.opacity = '1';
                                const expandBtn = commonRow.querySelector('.expand-btn');
                                const collapseBtn = commonRow.querySelector('.collapse-btn');
                                if (expandBtn && collapseBtn) {
                                    expandBtn.style.display = 'none';
                                    collapseBtn.style.display = 'inline-block';
                                }
                            } else {
                                commonExpandableRow.classList.remove('expanded');
                                commonExpandableRow.classList.add('collapsed');
                                commonExpandableRow.style.display = 'block';
                                commonExpandableRow.style.opacity = '0';
                                const expandBtn = commonRow.querySelector('.expand-btn');
                                const collapseBtn = commonRow.querySelector('.collapse-btn');
                                if (expandBtn && collapseBtn) {
                                    expandBtn.style.display = 'inline-block';
                                    collapseBtn.style.display = 'none';
                                }
                            }
                        }
                    }

                    commonRow.style.display = showCommonRow ? '' : 'none';
                    if (showCommonRow) visibleCommonRows++;
                });

                let commonRowCountDiv = commonTable.nextElementSibling;
                if (commonRowCountDiv && !commonRowCountDiv.classList.contains('row-count')) {
                    commonRowCountDiv = document.createElement('div');
                    commonRowCountDiv.className = 'row-count mt-2';
                    commonTable.insertAdjacentElement('afterend', commonRowCountDiv);
                }
                if (commonRowCountDiv) {
                    commonRowCountDiv.textContent = `Showing ${visibleCommonRows} of ${commonRows.length} rows`;
                }

                if (visibleCommonRows > 0 || hasMatchingItems) {
                    showCategoryRow = true;
                    subcatDiv.classList.remove('collapsed');
                    subcatDiv.classList.add('expanded');
                    subcatDiv.style.display = 'block';
                    subcatDiv.style.opacity = '1';
                    const categoryExpandBtn = categoryRow.querySelector('.expand-btn');
                    const categoryCollapseBtn = categoryRow.querySelector('.collapse-btn');
                    if (categoryExpandBtn && categoryCollapseBtn) {
                        categoryExpandBtn.style.display = 'none';
                        categoryCollapseBtn.style.display = 'inline-block';
                    }
                } else {
                    subcatDiv.classList.remove('expanded');
                    subcatDiv.classList.add('collapsed');
                    subcatDiv.style.display = 'block';
                    subcatDiv.style.opacity = '0';
                    const categoryExpandBtn = categoryRow.querySelector('.expand-btn');
                    const categoryCollapseBtn = categoryRow.querySelector('.collapse-btn');
                    if (categoryExpandBtn && categoryCollapseBtn) {
                        categoryExpandBtn.style.display = 'inline-block';
                        categoryCollapseBtn.style.display = 'none';
                    }
                }
            }
        }

        if (!window.globalFilter.commonName && !window.globalFilter.contractNumber) {
            showCategoryRow = true;
            if (subcatDiv) {
                subcatDiv.classList.remove('expanded');
                subcatDiv.classList.add('collapsed');
                subcatDiv.style.display = 'block';
                subcatDiv.style.opacity = '0';
                const categoryExpandBtn = categoryRow.querySelector('.expand-btn');
                const categoryCollapseBtn = categoryRow.querySelector('.collapse-btn');
                if (categoryExpandBtn && categoryCollapseBtn) {
                    categoryExpandBtn.style.display = 'inline-block';
                    categoryCollapseBtn.style.display = 'none';
                }
            }
        }

        categoryRow.style.display = showCategoryRow ? '' : 'none';
        if (expandableRow) {
            expandableRow.style.display = showCategoryRow ? '' : 'none';
        }
        if (showCategoryRow) visibleCategoryRows++;
    });

    let rowCountDiv = document.querySelector('.row-count');
    if (!rowCountDiv) {
        rowCountDiv = document.createElement('div');
        rowCountDiv.className = 'row-count mt-2';
        categoryTable.insertAdjacentElement('afterend', rowCountDiv);
    }
    rowCountDiv.textContent = `Showing ${visibleCategoryRows} of ${categoryRows.length} rows`;
}

/**
 * Apply global filter function for Tabs 1, 2, 4, 5 - PERFORMANCE OPTIMIZED
 * Used by: Tabs 1, 2, 4, 5
 * Dependency: sessionStorage, applyFilterToAllLevelsTabs2And4 or tab-specific filtering
 */
let filterTimeout;
window.applyGlobalFilter = function() {
    // Debounce filter application to prevent excessive calls
    clearTimeout(filterTimeout);
    filterTimeout = setTimeout(() => {
        // Skip global filter for Tab 3 and non-tab pages (e.g., /categories)
        const tabNum = getCachedTabNum();
        if (tabNum === 3 || !window.location.pathname.match(/\/tab\/\d+/)) {
            console.log('Skipping global filter application for Tab 3 or non-tab page');
            return;
        }
    
        performGlobalFilter(tabNum);
    }, 150); // Debounce delay
};

// Separate the actual filter logic to allow for debouncing
function performGlobalFilter(tabNum) {

    const commonNameInput = document.getElementById('commonNameFilter');
    const contractNumberInput = document.getElementById('contractNumberFilter');
    const commonName = commonNameInput ? commonNameInput.value.toLowerCase().trim() : '';
    const contractNumber = contractNumberInput ? contractNumberInput.value.toLowerCase().trim() : '';

    // Only update if values have actually changed
    const newFilter = {
        commonName: commonName,
        contractNumber: contractNumber
    };
    
    if (JSON.stringify(window.globalFilter) === JSON.stringify(newFilter)) {
        return; // No change, skip update
    }
    
    window.globalFilter = newFilter;

    // Save filter state to sessionStorage
    sessionStorage.setItem('globalFilter', JSON.stringify(window.globalFilter));

    // Apply filter based on the current tab with performance monitoring
    const startTime = performance.now();
    
    try {
        if (tabNum === 1 && typeof applyFilterToAllLevelsTab1 === 'function') {
            applyFilterToAllLevelsTab1();
        } else if (tabNum === 2 || tabNum === 4) {
            applyFilterToAllLevelsTabs2And4();
        } else if (tabNum === 5 && typeof applyFilterToAllLevelsTab5 === 'function') {
            applyFilterToAllLevelsTab5();
        }
    } catch (error) {
        console.error('Error applying global filter:', error);
    }
    
    const endTime = performance.now();
    if (endTime - startTime > 100) {
        console.warn(`Filter application took ${endTime - startTime}ms - consider optimizing`);
    }
}

/**
 * Clear global filter function for Tabs 1, 2, 4, 5
 * Used by: Tabs 1, 2, 4, 5
 * Dependency: sessionStorage
 */
window.clearGlobalFilter = function() {
    window.globalFilter = {
        commonName: '',
        contractNumber: ''
    };

    // Clear sessionStorage
    sessionStorage.removeItem('globalFilter');

    // Clear input fields
    const commonNameInput = document.getElementById('commonNameFilter');
    const contractNumberInput = document.getElementById('contractNumberFilter');
    if (commonNameInput) commonNameInput.value = '';
    if (contractNumberInput) contractNumberInput.value = '';

    // Refresh the page to clear filters
    window.location.reload();
};

/**
 * Sort common names for Tabs 2 and 4
 * Used by: Tabs 2, 4
 * Dependency: window.commonSortState
 */
window.sortCommonNames = function(contractNumber, column, tabNum) {
    const targetId = `common-${contractNumber}`;
    if (!window.commonSortState[contractNumber]) {
        window.commonSortState[contractNumber] = { column: '', direction: '' };
    }

    let direction = 'asc';
    if (window.commonSortState[contractNumber].column === column) {
        direction = window.commonSortState[contractNumber].direction === 'asc' ? 'desc' : 'asc';
    }
    window.commonSortState[contractNumber] = { column, direction };

    const headers = document.querySelectorAll(`#${targetId} .common-table thead tr:first-child th`);
    headers.forEach(header => {
        const sortArrow = header.querySelector('.sort-arrow') || document.createElement('span');
        sortArrow.className = 'sort-arrow';
        if (!header.querySelector('.sort-arrow')) header.appendChild(sortArrow);
        const headerColumn = header.textContent.trim().toLowerCase().replace(/\s+/g, '_');
        if (headerColumn === column) {
            sortArrow.textContent = direction === 'asc' ? '↑' : '↓';
        } else {
            sortArrow.textContent = '';
        }
    });

    const sortColumn = column === 'common_name' ? 'name' : column;
    const url = `/tab/${tabNum}/common_names?contract_number=${encodeURIComponent(contractNumber)}&sort=${sortColumn}_${direction}`;
    console.log(`Fetching sorted common names: ${url}`);

    fetch(url)
        .then(response => {
            console.log(`Common names sort fetch status: ${response.status}`);
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`Common names sort failed: ${response.status} - ${text}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Sorted common names data:', data);
            const targetElement = document.getElementById(targetId);
            if (!targetElement) return;

            const commonNames = data.common_names || [];
            const totalCommonNames = data.total_common_names || 0;
            const perPage = data.per_page || 10;
            const currentPage = data.page || 1;

            let html = `
                <div class="subcategory-container">
                    <table class="table table-bordered table-hover common-table">
                        <thead class="thead-dark">
                            <tr>
                                <th onclick="window.sortCommonNames('${contractNumber}', 'common_name', ${tabNum})">Common Name <span class="sort-arrow"></span></th>
                                <th onclick="window.sortCommonNames('${contractNumber}', 'on_contracts', ${tabNum})">Items on Contract <span class="sort-arrow"></span></th>
                                <th onclick="window.sortCommonNames('${contractNumber}', 'total_items_inventory', ${tabNum})">Total Items in Inventory <span class="sort-arrow"></span></th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            commonNames.forEach(common => {
                const commonId = `${contractNumber}-${common.name.replace(/[^a-z0-9]/g, '_')}`;
                const escapedCommonName = common.name.replace(/'/g, "\\'").replace(/"/g, '\\"');
                html += `
                    <tr>
                        <td class="expandable-cell" onclick="window.expandItems('${contractNumber}', '${escapedCommonName}', 'items-${commonId}', 1, ${tabNum})">${common.name}</td>
                        <td>${common.on_contracts}</td>
                        <td>${common.is_hand_counted ? 'N/A' : common.total_items_inventory}</td>
                        <td>
                            <button class="btn btn-sm btn-secondary expand-btn" data-common-name="${escapedCommonName}" data-target-id="items-${commonId}" data-contract-number="${contractNumber}">Expand</button>
                            <button class="btn btn-sm btn-secondary collapse-btn" data-collapse-target="items-${commonId}" style="display:none;">Collapse</button>
                            <button class="btn btn-sm btn-info print-btn" data-print-level="Common Name" data-print-id="items-${commonId}" data-common-name="${escapedCommonName}" data-category="${contractNumber}">Print</button>
                            <button class="btn btn-sm btn-info print-full-btn" data-common-name="${escapedCommonName}" data-category="${contractNumber}">Print Full List</button>
                            <div id="loading-items-${commonId}" style="display:none;" class="loading-indicator">Loading...</div>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="4">
                            <div id="items-${commonId}" class="expandable collapsed item-level"></div>
                        </td>
                    </tr>
                `;
            });

            html += `</tbody></table></div>`;

            if (totalCommonNames > perPage) {
                const totalPages = Math.ceil(totalCommonNames / perPage);
                html += `
                    <div class="pagination-controls mt-2">
                        <button class="btn btn-sm btn-secondary" onclick="window.expandCategory('', '${targetId}', '${contractNumber}', ${currentPage - 1}, ${tabNum})" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>
                        <span class="mx-2">Page ${currentPage} of ${totalPages}</span>
                        <button class="btn btn-sm btn-secondary" onclick="window.expandCategory('', '${targetId}', '${contractNumber}', ${currentPage + 1}, ${tabNum})" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>
                    </div>
                `;
            }

            targetElement.innerHTML = html;
            const table = targetElement.querySelector('.common-table');
            if (table) {
                applyFilterToTable(table);
            }
        })
        .catch(error => {
            console.error('Common names sort error:', error.message);
        });
};

/**
 * Sort items for Tabs 2 and 4
 * Used by: Tabs 2, 4
 * Dependency: window.itemSortState
 */
window.sortItems = function(contractNumber, commonName, column, tabNum) {
    const targetId = `items-${contractNumber}-${commonName.replace(/[^a-z0-9]/g, '_')}`;
    if (!window.itemSortState[targetId]) {
        window.itemSortState[targetId] = { column: '', direction: '' };
    }

    let direction = 'asc';
    if (window.itemSortState[targetId].column === column) {
        direction = window.itemSortState[targetId].direction === 'asc' ? 'desc' : 'asc';
    }
    window.itemSortState[targetId] = { column, direction };

    const headers = document.querySelectorAll(`#${targetId} .item-table thead tr:first-child th`);
    headers.forEach(header => {
        const sortArrow = header.querySelector('.sort-arrow') || document.createElement('span');
        sortArrow.className = 'sort-arrow';
        if (!header.querySelector('.sort-arrow')) header.appendChild(sortArrow);
        const headerColumn = header.textContent.trim().toLowerCase().replace(/\s+/g, '_');
        if (headerColumn === column) {
            sortArrow.textContent = direction === 'asc' ? '↑' : '↓';
        } else {
            sortArrow.textContent = '';
        }
    });

    const url = `/tab/${tabNum}/data?contract_number=${encodeURIComponent(contractNumber)}&common_name=${encodeURIComponent(commonName)}&sort=${column}_${direction}`;
    console.log(`Fetching sorted items: ${url}`);

    fetch(url)
        .then(response => {
            console.log(`Items sort fetch status: ${response.status}`);
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`Items sort failed: ${response.status} - ${text}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Sorted items data:', data);
            const targetElement = document.getElementById(targetId);
            if (!targetElement) return;

            const items = data.items || [];
            const totalItems = data.total_items || 0;
            const perPage = data.per_page || 10;
            const currentPage = data.page || 1;

            let html = `
                <div class="item-level-wrapper ml-4">
                    <table class="table table-bordered table-hover item-table">
                        <thead class="thead-dark">
                            <tr>
                                <th onclick="window.sortItems('${contractNumber}', '${commonName}', 'tag_id', ${tabNum})">Tag ID <span class="sort-arrow"></span></th>
                                <th onclick="window.sortItems('${contractNumber}', '${commonName}', 'common_name', ${tabNum})">Common Name <span class="sort-arrow"></span></th>
                                <th onclick="window.sortItems('${contractNumber}', '${commonName}', 'bin_location', ${tabNum})">Bin Location <span class="sort-arrow"></span></th>
                                <th onclick="window.sortItems('${contractNumber}', '${commonName}', 'status', ${tabNum})">Status <span class="sort-arrow"></span></th>
                                <th onclick="window.sortItems('${contractNumber}', '${commonName}', 'last_contract_num', ${tabNum})">Last Contract <span class="sort-arrow"></span></th>
                                <th onclick="window.sortItems('${contractNumber}', '${commonName}', 'last_scanned_date', ${tabNum})">Last Scanned Date <span class="sort-arrow"></span></th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            items.forEach(item => {
                const formattedScanDate = formatDate(item.last_scanned_date);
                html += `
                    <tr>
                        <td>${item.tag_id}</td>
                        <td>${item.common_name}</td>
                        <td>${item.bin_location || 'N/A'}</td>
                        <td>${item.status}</td>
                        <td>${item.last_contract_num || 'N/A'}</td>
                        <td>${formattedScanDate}</td>
                    </tr>
                `;
            });

            html += `</tbody></table></div>`;

            if (totalItems > perPage) {
                const totalPages = Math.ceil(totalItems / perPage);
                const escapedCommonName = commonName.replace(/'/g, "\\'").replace(/"/g, '\\"');
                html += `
                    <div class="pagination-controls mt-2 ml-4">
                        <button class="btn btn-sm btn-secondary" onclick="window.expandItems('${contractNumber}', '${escapedCommonName}', '${targetId}', ${currentPage - 1}, ${tabNum})" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>
                        <span class="mx-2">Page ${currentPage} of ${totalPages}</span>
                        <button class="btn btn-sm btn-secondary" onclick="window.expandItems('${contractNumber}', '${escapedCommonName}', '${targetId}', ${currentPage + 1}, ${tabNum})" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>
                    </div>
                `;
            }

            targetElement.innerHTML = html;
            const table = targetElement.querySelector('.item-table');
            if (table) {
                applyFilterToTable(table);
            }
        })
        .catch(error => {
            console.error('Items sort error:', error.message);
        });
};

/**
 * Print a table (Contract, Common Name, or Item level)
 * Used by: All tabs
 * Dependency: formatDateTime, removeTotalItemsInventoryColumn
 */
window.printTable = async function printTable(level, id, commonName = null, category = null, subcategory = null) {
    console.log(`Printing table: ${level}, ID: ${id}, Common Name: ${commonName}, Category: ${category}, Subcategory: ${subcategory}`);
    const element = document.getElementById(id);
    if (!element) {
        console.error(`Element with ID ${id} not found for printing`);
        return;
    }

    const tabNum = getCachedTabNum() || 1;
    const tabName = tabNum == 2 ? 'Open Contracts' : tabNum == 4 ? 'Laundry Contracts' : tabNum == 5 ? 'Resale/Rental Packs' : tabNum == 3 ? 'Service' : `Tab ${tabNum}`;

    let contractNumber = '';
    if (level === 'Contract') {
        if (id.startsWith('common-')) {
            contractNumber = id.replace('common-', '');
        } else {
            const contractCell = element.querySelector('td:first-child');
            contractNumber = contractCell ? contractCell.textContent.trim() : '';
        }
    } else {
        contractNumber = category || '';
    }

    let contractDate = 'N/A';
    if (contractNumber && (tabNum == 2 || tabNum == 4)) {
        try {
            const response = await fetch(`/get_contract_date?contract_number=${encodeURIComponent(contractNumber)}`);
            const data = await response.json();
            contractDate = data.date ? formatDateTime(data.date) : 'N/A';
        } catch (error) {
            console.error('Error fetching contract date:', error);
        }
    }

    let printElement;
    let tableWrapper;

    if (level === 'Common Name' && commonName && category) {
        let url = `/tab/${tabNum}/data?common_name=${encodeURIComponent(commonName)}`;
        if (tabNum == 2 || tabNum == 4) {
            url += `&contract_number=${encodeURIComponent(category)}`;
        } else {
            url += `&category=${encodeURIComponent(category)}`;
        }
        if (subcategory) {
            url += `&subcategory=${encodeURIComponent(subcategory)}`;
        }
        const response = await fetch(url);
        const data = await response.json();
        const items = data.items || [];

        const statusCounts = {};
        items.forEach(item => {
            const status = item.status || 'Unknown';
            statusCounts[status] = (statusCounts[status] || 0) + 1;
        });

        tableWrapper = document.createElement('table');
        tableWrapper.className = 'table table-bordered';
        tableWrapper.innerHTML = `
            <thead>
                <tr>
                    <th>Common Name</th>
                    <th>Status</th>
                    <th>Count</th>
                </tr>
            </thead>
            <tbody>
                ${Object.entries(statusCounts).map(([status, count]) => `
                    <tr>
                        <td>${commonName}</td>
                        <td>${status}</td>
                        <td>${count}</td>
                    </tr>
                `).join('')}
            </tbody>
        `;
    } else if (level === 'Contract' && tabNum === 4) {
        const url = `/tab/4/common_names?contract_number=${encodeURIComponent(contractNumber)}&all=true`;
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`Failed to fetch all common names: ${response.status}`);
            }
            const data = await response.json();
            const commonNames = data.common_names || [];

            tableWrapper = document.createElement('table');
            tableWrapper.className = 'table table-bordered';
            tableWrapper.innerHTML = `
                <thead>
                    <tr>
                        <th>Common Name</th>
                        <th>Items on Contract</th>
                        <th>Total Items in Inventory</th>
                    </tr>
                </thead>
                <tbody>
                    ${commonNames.map(common => `
                        <tr>
                            <td>${common.name}</td>
                            <td>${common.on_contracts}</td>
                            <td>${common.is_hand_counted ? 'N/A' : common.total_items_inventory}</td>
                        </tr>
                    `).join('')}
                </tbody>
            `;
        } catch (error) {
            console.error('Error fetching all common names for print:', error);
            tableWrapper = document.createElement('table');
            tableWrapper.className = 'table table-bordered';
            tableWrapper.innerHTML = `<tr><td colspan="3">Error loading common names: ${error.message}</td></tr>`;
        }
    } else {
        printElement = element.cloneNode(true);

        if (level === 'Contract') {
            let commonTable;
            if (id.startsWith('common-')) {
                if (printElement.classList.contains('expanded')) {
                    commonTable = printElement.querySelector('.common-table');
                }
            } else {
                const row = element.closest('tr');
                if (row) {
                    const nextRow = row.nextElementSibling;
                    if (nextRow) {
                        const expandedContent = nextRow.querySelector('.expandable.expanded');
                        if (expandedContent) {
                            commonTable = expandedContent.querySelector('.common-table');
                        }
                    }
                }
            }

            if (commonTable) {
                tableWrapper = commonTable.cloneNode(true);
            } else {
                const url = `/tab/${tabNum}/common_names?contract_number=${encodeURIComponent(contractNumber)}`;
                const response = await fetch(url);
                const data = await response.json();
                const commonNames = data.common_names || [];

                tableWrapper = document.createElement('table');
                tableWrapper.className = 'table table-bordered';
                tableWrapper.innerHTML = `
                    <thead>
                        <tr>
                            <th>Common Name</th>
                            <th>Items on Contract</th>
                            <th>Total Items in Inventory</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${commonNames.map(common => `
                            <tr>
                                <td>${common.name}</td>
                                <td>${common.on_contracts}</td>
                                <td>${common.total_items_inventory}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                `;
            }
        } else {
            tableWrapper = printElement;
        }

        removeTotalItemsInventoryColumn(tableWrapper, tabNum);

        tableWrapper.querySelectorAll('.btn, .loading, .expandable.collapsed, .pagination-controls, .filter-sort-controls, .filter-row').forEach(el => el.remove());
    }

    tableWrapper.querySelectorAll('br').forEach(br => br.remove());

    const printContent = `
        <html>
            <head>
                <title>Broadway Tent and Event - ${tabName} - ${level}</title>
                <style>
                    body {
                        font-family: 'Roboto', sans-serif;
                        margin: 20px;
                        color: #333;
                    }
                    .print-header {
                        text-align: center;
                        margin-bottom: 40px;
                    }
                    .print-header h1 {
                        font-size: 28px;
                        margin: 0;
                    }
                    .print-header h2 {
                        font-size: 20px;
                        margin: 5px 0;
                    }
                    .print-header p {
                        font-size: 14px;
                        color: #666;
                        margin: 5px 0;
                    }
                    table {
                        border-collapse: collapse;
                        width: 100%;
                        margin-top: 20px;
                    }
                    th, td {
                        border: 1px solid #ccc;
                        padding: 12px;
                        text-align: center;
                        font-size: 14px;
                        white-space: normal;
                        word-wrap: break-word;
                    }
                    th {
                        background-color: #f2f2f2;
                        font-weight: bold;
                    }
                    td {
                        vertical-align: middle;
                    }
                    .hidden {
                        display: none;
                    }
                    .common-level {
                        margin-left: 1rem;
                        background-color: #e9ecef;
                        padding: 0.5rem;
                        border-left: 3px solid #28a745;
                        margin-top: 10px;
                    }
                    .item-level-wrapper {
                        margin-left: 1rem;
                        background-color: #dee2e6;
                        padding: 0.5rem;
                        border-left: 3px solid #dc3545;
                        margin-top: 10px;
                    }
                    .signature-line {
                        margin-top: 40px;
                        border-top: 1px solid #000;
                        width: 300px;
                        text-align: center;
                        padding-top: 10px;
                        font-size: 14px;
                    }
                    @media print {
                        body {
                            margin: 0;
                        }
                        .print-header {
                            position: static;
                            width: 100%;
                            margin-bottom: 20px;
                        }
                        table {
                            page-break-inside: auto;
                        }
                        tr {
                            page-break-inside: avoid;
                            page-break-after: auto;
                        }
                        th, td {
                            font-size: 8pt;
                            padding: 4px 8px;
                            word-break: break-word;
                            text-align: center;
                        }
                    }
                </style>
            </head>
            <body>
                <div class="print-header">
                    <h1>Broadway Tent and Event</h1>
                    <h2>${tabName}</h2>
                    ${contractNumber ? `<p>Contract Number: ${contractNumber}</p>` : ''}
                    ${contractDate !== 'N/A' ? `<p>Contract Created: ${contractDate}</p>` : ''}
                    ${commonName ? `<p>Common Name: ${commonName}</p>` : ''}
                    <p>Printed on: ${new Date().toLocaleString()}</p>
                </div>
                <div>
                    ${tableWrapper.outerHTML}
                </div>
                <div class="signature-line">
                    Signature: _______________________________
                </div>
                <script>
                    window.onload = function() {
                        window.print();
                        window.onafterprint = function() {
                            window.close();
                        };
                    };
                </script>
            </body>
        </html>
    `;

    const printWindow = window.open('', '_blank');
    if (!printWindow) {
        console.error('Failed to open print window. Please allow popups.');
        return;
    }
    printWindow.document.write(printContent);
    printWindow.document.close();
}

/**
 * Remove "Total Items in Inventory" column for Tabs 2 and 4
 * Used by: Tabs 2, 4 (via printTable)
 */
function removeTotalItemsInventoryColumn(table, tabNum) {
    if (tabNum == 2 || tabNum == 4) {
        const headers = table.querySelectorAll('th');
        const rows = table.querySelectorAll('tbody tr');
        headers.forEach((th, index) => {
            if (th.textContent.trim() === 'Total Items in Inventory') {
                th.remove();
                rows.forEach(row => {
                    const cell = row.cells[index];
                    if (cell) cell.remove();
                });
            }
        });
    }
}

/**
 * Print full item list
 * Used by: All tabs
 * Dependency: normalizeCommonName, formatDateTime
 */
window.printFullItemList = async function printFullItemList(category, subcategory, commonName) {
    console.log(`Printing full item list for Category: ${category}, Subcategory: ${subcategory}, Common Name: ${commonName}`);
    const tabNum = getCachedTabNum() || 1;
    const tabName = tabNum == 2 ? 'Open Contracts' : tabNum == 4 ? 'Laundry Contracts' : tabNum == 5 ? 'Resale/Rental Packs' : tabNum == 3 ? 'Service' : `Tab ${tabNum}`;

    const normalizedCommonName = normalizeCommonName(commonName);
    console.log(`Normalized Common Name: ${normalizedCommonName}`);

    const url = `/tab/${tabNum}/full_items_by_rental_class?category=${encodeURIComponent(category)}&subcategory=${subcategory ? encodeURIComponent(subcategory) : 'null'}&common_name=${encodeURIComponent(normalizedCommonName)}`;
    const response = await fetch(url);
    const data = await response.json();
    const items = data.items || [];

    const tableWrapper = document.createElement('table');
    tableWrapper.className = 'table table-bordered';
    const headers = ['Tag ID', 'Common Name', 'Rental Class Num', 'Bin Location', 'Status', 'Last Contract', 'Last Scanned Date', 'Quality', 'Notes'];
    tableWrapper.innerHTML = `
        <thead>
            <tr>
                ${headers.map(header => `<th>${header}</th>`).join('')}
            </tr>
        </thead>
        <tbody>
            ${items.map(item => `
                <tr>
                    <td>${item.tag_id}</td>
                    <td>${item.common_name}</td>
                    <td>${item.rental_class_num || 'N/A'}</td>
                    <td>${item.bin_location || 'N/A'}</td>
                    <td>${item.status}</td>
                    <td>${item.last_contract_num || 'N/A'}</td>
                    <td>${formatDateTime(item.last_scanned_date)}</td>
                    <td>${item.quality || 'N/A'}</td>
                    <td>${item.notes || 'N/A'}</td>
                </tr>
            `).join('')}
        </tbody>
    `;

    const printContent = `
        <html>
            <head>
                <title>Broadway Tent and Event - ${tabName} - Full Item List</title>
                <style>
                    body {
                        font-family: 'Roboto', sans-serif;
                        margin: 20px;
                        color: #333;
                    }
                    .print-header {
                        text-align: center;
                        margin-bottom: 40px;
                    }
                    .print-header h1 {
                        font-size: 28px;
                        margin: 0;
                    }
                    .print-header h2 {
                        font-size: 20px;
                        margin: 5px 0;
                    }
                    .print-header p {
                        font-size: 14px;
                        color: #666;
                        margin: 5px 0;
                    }
                    table {
                        border-collapse: collapse;
                        width: 100%;
                        margin-top: 20px;
                    }
                    th, td {
                        border: 1px solid #ccc;
                        padding: 8px;
                        text-align: center;
                        font-size: 12px;
                        white-space: normal;
                        word-wrap: break-word;
                    }
                    th {
                        background-color: #f2f2f2;
                        font-weight: bold;
                    }
                    td {
                        vertical-align: middle;
                    }
                    .signature-line {
                        margin-top: 40px;
                        border-top: 1px solid #000;
                        width: 300px;
                        text-align: center;
                        padding-top: 10px;
                        font-size: 14px;
                    }
                    @media print {
                        body {
                            margin: 0;
                        }
                        .print-header {
                            position: static;
                            width: 100%;
                            margin-bottom: 20px;
                        }
                        table {
                            page-break-inside: auto;
                        }
                        tr {
                            page-break-inside: avoid;
                            page-break-after: auto;
                        }
                        th, td {
                            font-size: 8pt;
                            padding: 4px 8px;
                            word-break: break-word;
                            text-align: center;
                        }
                    }
                </style>
            </head>
            <body>
                <div class="print-header">
                    <h1>Broadway Tent and Event</h1>
                    <h2>${tabName}</h2>
                    <p>Common Name: ${commonName}</p>
                    <p>Printed on: ${new Date().toLocaleString()}</p>
                </div>
                <div>
                    ${tableWrapper.outerHTML}
                </div>
                <div class="signature-line">
                    Signature: _______________________________
                </div>
                <script>
                    window.onload = function() {
                        window.print();
                        window.onafterprint = function() {
                            window.close();
                        };
                    };
                </script>
            </body>
        </html>
    `;

    const printWindow = window.open('', '_blank');
    if (!printWindow) {
        console.error('Failed to open print window. Please allow popups.');
        return;
    }
    printWindow.document.write(printContent);
    printWindow.document.close();
}
// CRITICAL FIX: Force fixed navbar positioning
function forceNavbarFixed() {
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        // Force fixed positioning
        navbar.style.position = 'fixed';
        navbar.style.top = '0';
        navbar.style.left = '0';
        navbar.style.right = '0';
        navbar.style.width = '100%';
        navbar.style.zIndex = '1030';
        console.log('Navbar fixed positioning enforced via JavaScript');
    }
}

// CRITICAL: Bootstrap dropdown reinitialization after content loads - FIXED VERSION
function reinitializeBootstrapDropdowns() {
    // Skip reinitialization on tabs 6 and 7 to prevent Chart.js conflicts
    const currentPath = window.location.pathname;
    if (currentPath.includes('/tab/6') || currentPath.includes('/tab/7')) {
        console.log('Skipping dropdown reinit on tab 6/7 to prevent Chart.js conflicts');
        return;
    }
    
    if (typeof bootstrap !== 'undefined') {
        const dropdownElements = document.querySelectorAll('.dropdown-toggle');
        const uninitializedElements = Array.from(dropdownElements).filter(element => 
            !bootstrap.Dropdown.getInstance(element)
        );
        
        if (uninitializedElements.length === 0) {
            // No need to reinitialize if all dropdowns are already initialized
            return;
        }
        
        uninitializedElements.forEach(element => {
            try {
                new bootstrap.Dropdown(element, {
                    autoClose: true,
                    boundary: 'viewport'
                });
            } catch (error) {
                console.warn('Error initializing dropdown:', error);
            }
        });
        
        console.log(`Bootstrap dropdowns reinitialized: ${uninitializedElements.length} new dropdowns`);
    }
}

// Auto-run the navbar fix when this script loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        forceNavbarFixed();
        setTimeout(forceNavbarFixed, 100);
        
        // Single dropdown initialization - no excessive timeouts
        setTimeout(reinitializeBootstrapDropdowns, 500);
    });
} else {
    // Document already loaded
    forceNavbarFixed();
    setTimeout(forceNavbarFixed, 100);
    
    // Single dropdown initialization - no excessive timeouts
    setTimeout(reinitializeBootstrapDropdowns, 100);
}

// Expose the function globally for use by other scripts
window.reinitializeBootstrapDropdowns = reinitializeBootstrapDropdowns;
