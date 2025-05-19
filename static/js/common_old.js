console.log('common_old.js version: 2025-05-16-v17 loaded - confirming script load');

/**
 * Note: This file preserves the original common.js logic for reference during tab restructuring.
 * Functions will be moved to tab-specific files or a new common.js as needed.
 */

/**
 * Format ISO date strings into "Thurs, Aug 21 2025 4:55 pm"
 * Used by: Tabs 1, 2, 3, 4, 5 (via tab.js, expand.js, tab3.js)
 * Dependency: None
 * To be moved to: Each tab's JS file (already in tab1.js)
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
        hours = hours % 12 || 12; // Convert 0 to 12 for midnight

        return `${dayName}, ${monthName} ${day} ${year} ${hours}:${minutes} ${ampm}`;
    } catch (error) {
        console.error('Error formatting date:', isoDateString, error);
        return 'N/A';
    }
}

/**
 * Show loading indicator
 * Used by: Tabs 1, 2, 4, 5 (via tab1_5.js, expand.js)
 * Dependency: CSS (.loading-indicator)
 * To be moved to: Each tab's JS file (already in tab1.js)
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
 * Used by: Tabs 1, 2, 4, 5 (via tab1_5.js, expand.js)
 * Dependency: None
 * To be moved to: Each tab's JS file (already in tab1.js)
 */
function hideLoading(targetId) {
    const loadingDiv = document.getElementById(`loading-${targetId}`);
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

/**
 * Collapse section (category/subcategory level)
 * Used by: Tabs 1, 2, 4, 5 (via tab1_5.js, expand.js)
 * Dependency: sessionStorage
 * To be moved to: Each tab's JS file (already in tab1.js)
 */
function collapseSection(categoryRow, targetId) {
    if (!targetId || !categoryRow) {
        console.error('collapseSection: Invalid parameters', { targetId, categoryRow });
        return;
    }
    console.log(`Collapsing ${targetId}`);
    const existingRows = categoryRow.parentNode.querySelectorAll(`tr.common-name-row[data-target-id="${targetId}"]`);
    existingRows.forEach(row => row.remove());
    sessionStorage.removeItem(`expanded_${targetId}`);
}

/**
 * Collapse items (item level)
 * Used by: Tabs 1, 2, 4, 5 (via tab1_5.js, expand.js)
 * Dependency: sessionStorage
 * To be moved to: Each tab's JS file (already in tab1.js)
 */
function collapseItems(targetId) {
    const container = document.getElementById(targetId);
    if (!container) {
        console.error(`Container ${targetId} not found for collapsing items`);
        return;
    }
    console.log(`Collapsing items ${targetId}`);
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
 * Global filter state
 * Used by: Tabs 1, 2, 4, 5 (via applyGlobalFilter)
 * Dependency: sessionStorage
 * To be moved to: Each tab's JS file if needed (Tab 1 doesn’t use it)
 */
let globalFilter = {
    commonName: '',
    contractNumber: ''
};

/**
 * Load global filter from sessionStorage on page load
 * Used by: Tabs 1, 2, 4, 5
 * Dependency: sessionStorage
 * To be moved to: Each tab's JS file if needed
 */
document.addEventListener('DOMContentLoaded', function() {
    const savedFilter = sessionStorage.getItem('globalFilter');
    if (savedFilter) {
        globalFilter = JSON.parse(savedFilter);
        const commonNameInput = document.getElementById('commonNameFilter');
        const contractNumberInput = document.getElementById('contractNumberFilter');
        if (commonNameInput) commonNameInput.value = globalFilter.commonName || '';
        if (contractNumberInput) contractNumberInput.value = globalFilter.contractNumber || '';
    }
});

/**
 * Apply global filter function
 * Used by: Tabs 1, 2, 4, 5
 * Dependency: sessionStorage, applyFilterToAllLevels
 * To be moved to: Each tab's JS file if needed
 */
window.applyGlobalFilter = function() {
    // Skip global filter for Tab 3 and non-tab pages (e.g., /categories)
    if (window.cachedTabNum === 3 || !window.location.pathname.match(/\/tab\/\d+/)) {
        console.log('Skipping global filter application for Tab 3 or non-tab page');
        return;
    }

    const commonNameInput = document.getElementById('commonNameFilter');
    const contractNumberInput = document.getElementById('contractNumberFilter');
    const commonName = commonNameInput ? commonNameInput.value.toLowerCase().trim() : '';
    const contractNumber = contractNumberInput ? contractNumberInput.value.toLowerCase().trim() : '';

    globalFilter = {
        commonName: commonName,
        contractNumber: contractNumber
    };

    // Save filter state to sessionStorage
    sessionStorage.setItem('globalFilter', JSON.stringify(globalFilter));

    // Apply filter to all levels
    applyFilterToAllLevels();
};

/**
 * Clear global filter function
 * Used by: Tabs 1, 2, 4, 5
 * Dependency: sessionStorage
 * To be moved to: Each tab's JS file if needed
 */
window.clearGlobalFilter = function() {
    globalFilter = {
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
 * Apply filter to all levels (category, subcategory, common names, items)
 * Used by: Tabs 1, 2, 4, 5
 * Dependency: globalFilter, DOM
 * To be moved to: Each tab's JS file (already in tab1.js as applyFilterToAllLevelsTab1)
 */
function applyFilterToAllLevels() {
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

                        if (globalFilter.commonName && !commonNameValue.includes(globalFilter.commonName)) {
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

                                        if (globalFilter.commonName && !itemCommonNameValue.includes(globalFilter.commonName)) {
                                            showItemRow = false;
                                        }
                                        if (globalFilter.contractNumber && !itemContractValue.includes(globalFilter.contractNumber)) {
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
                if (globalFilter.commonName) {
                    if (categoryValue.includes(globalFilter.commonName)) {
                        showCategoryRow = true;
                    }
                } else {
                    showCategoryRow = true;
                }
            }

            if (!globalFilter.commonName && !globalFilter.contractNumber) {
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
    } else {
        // For Tabs 2 and 4
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

            if (globalFilter.contractNumber) {
                if (contractValue.includes(globalFilter.contractNumber)) {
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

                        if (globalFilter.commonName) {
                            if (commonNameValue.includes(globalFilter.commonName)) {
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

                                    if (globalFilter.commonName && !itemCommonNameValue.includes(globalFilter.commonName)) {
                                        showItemRow = false;
                                    }
                                    if (globalFilter.contractNumber && !itemContractValue.includes(globalFilter.contractNumber)) {
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

            if (!globalFilter.commonName && !globalFilter.contractNumber) {
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
}

/**
 * Apply filter to a specific table (used for Tabs 2 and 4)
 * Used by: Tabs 2, 4 (via expand.js)
 * Dependency: globalFilter, DOM
 * To be moved to: Each tab's JS file
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

    if (!globalFilter.commonName && !globalFilter.contractNumber) {
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
            const commonNameCell = row.querySelector('td:nth-child(2)') || row.querySelector('td:nth-child(1)');
            const contractValue = contractCell ? contractCell.textContent.toLowerCase() : '';
            const commonNameValue = commonNameCell ? commonNameCell.textContent.toLowerCase() : '';

            if (globalFilter.contractNumber && !contractValue.includes(globalFilter.contractNumber)) {
                showRow = false;
            }
            if (globalFilter.commonName && !commonNameValue.includes(globalFilter.commonName)) {
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
                        const childCommonNameCell = childRow.querySelector('td:nth-child(2)') || childRow.querySelector('td:nth-child(1)');
                        const childContractValue = childContractCell ? childContractCell.textContent.toLowerCase() : '';
                        const childCommonNameValue = childCommonNameCell ? childCommonNameCell.textContent.toLowerCase() : '';

                        if (globalFilter.contractNumber && !childContractValue.includes(globalFilter.contractNumber)) {
                            showChildRow = false;
                        }
                        if (globalFilter.commonName && !childCommonNameValue.includes(globalFilter.commonName)) {
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