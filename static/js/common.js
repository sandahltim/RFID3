console.log('common.js version: 2025-04-27-v3 loaded - confirming script load');

// Global filter state
let globalFilter = {
    commonName: '',
    contractNumber: ''
};

// Load global filter from sessionStorage on page load
document.addEventListener('DOMContentLoaded', function() {
    const savedFilter = sessionStorage.getItem('globalFilter');
    if (savedFilter) {
        globalFilter = JSON.parse(savedFilter);
        document.getElementById('commonNameFilter').value = globalFilter.commonName || '';
        document.getElementById('contractNumberFilter').value = globalFilter.contractNumber || '';
        // Defer applying the filter until subcategory dropdowns are populated (handled in tab1.html and tab5.html)
    }
});

// Apply global filter function
window.applyGlobalFilter = function() {
    const commonName = document.getElementById('commonNameFilter').value.toLowerCase().trim();
    const contractNumber = document.getElementById('contractNumberFilter').value.toLowerCase().trim();

    globalFilter = {
        commonName: commonName,
        contractNumber: contractNumber
    };

    // Save filter state to sessionStorage
    sessionStorage.setItem('globalFilter', JSON.stringify(globalFilter));

    // Apply filter to all levels
    applyFilterToAllLevels();
};

// Clear global filter function
window.clearGlobalFilter = function() {
    globalFilter = {
        commonName: '',
        contractNumber: ''
    };

    // Clear sessionStorage
    sessionStorage.removeItem('globalFilter');

    // Clear input fields
    document.getElementById('commonNameFilter').value = '';
    document.getElementById('contractNumberFilter').value = '';

    // Refresh the page to clear filters
    window.location.reload();
};

// Apply filter to all levels (category, common names, items)
function applyFilterToAllLevels() {
    // Skip filtering the category table for Tabs 1 and 5, as it doesn't contain common names directly
    if (window.cachedTabNum === 1 || window.cachedTabNum === 5) {
        // Apply filter to subcategory dropdowns
        const subcatSelects = document.querySelectorAll('.subcategory-select');
        subcatSelects.forEach(select => {
            const options = select.querySelectorAll('option:not([value=""])');
            let visibleOptions = 0;

            // If no filter is applied, show all options and rows
            if (!globalFilter.commonName && !globalFilter.contractNumber) {
                options.forEach(option => {
                    option.style.display = '';
                    visibleOptions++;
                });
            } else {
                // Apply common name filter to subcategory options
                options.forEach(option => {
                    let showOption = true;
                    const subcatValue = option.textContent.toLowerCase();
                    if (globalFilter.commonName && !subcatValue.includes(globalFilter.commonName)) {
                        showOption = false;
                    }
                    option.style.display = showOption ? '' : 'none';
                    if (showOption) visibleOptions++;
                });
            }

            // Show or hide the parent row based on visible options
            const parentRow = select.closest('tr');
            if (parentRow) {
                parentRow.style.display = visibleOptions > 0 ? '' : 'none';
                const expandableRow = parentRow.nextElementSibling;
                if (expandableRow && expandableRow.classList.contains('expandable')) {
                    expandableRow.style.display = visibleOptions > 0 ? '' : 'none';
                }
            }
        });

        // Update category table row count
        const categoryTable = document.getElementById('category-table');
        if (categoryTable) {
            const rows = categoryTable.querySelectorAll('tbody tr:not(.expandable)');
            const visibleRows = Array.from(rows).filter(row => row.style.display !== 'none').length;
            let rowCountDiv = categoryTable.nextElementSibling;
            while (rowCountDiv && !rowCountDiv.classList.contains('row-count') && !rowCountDiv.classList.contains('pagination-controls')) {
                rowCountDiv = rowCountDiv.nextElementSibling;
            }
            if (!rowCountDiv || !rowCountDiv.classList.contains('row-count')) {
                rowCountDiv = document.createElement('div');
                rowCountDiv.className = 'row-count mt-2';
                categoryTable.insertAdjacentElement('afterend', rowCountDiv);
            }
            rowCountDiv.textContent = `Showing ${visibleRows} of ${rows.length} rows`;
        }
    } else {
        // Apply to category table (top level) for Tabs 2 and 4
        const categoryTable = document.getElementById('category-table');
        if (categoryTable) {
            applyFilterToTable(categoryTable);
        }
    }

    // Apply to all expanded common name tables
    const commonTables = document.querySelectorAll('.common-table');
    commonTables.forEach(table => {
        applyFilterToTable(table);
    });

    // Apply to all expanded item tables
    const itemTables = document.querySelectorAll('.item-table');
    itemTables.forEach(table => {
        applyFilterToTable(table);
    });
}

// Apply filter to a specific table
function applyFilterToTable(table) {
    const rows = table.querySelectorAll('tbody tr:not(.expandable)');
    let visibleRows = 0;

    // If no filter criteria are set, show all rows
    if (!globalFilter.commonName && !globalFilter.contractNumber) {
        rows.forEach(row => {
            row.style.display = '';
            visibleRows++;
            const expandableRow = row.nextElementSibling;
            if (expandableRow && expandableRow.classList.contains('expandable')) {
                expandableRow.style.display = '';
                // If this row has an expanded section, reapply filter to its children
                const childTable = expandableRow.querySelector('.common-table, .item-table');
                if (childTable) {
                    applyFilterToTable(childTable);
                }
            }
        });
    } else {
        rows.forEach(row => {
            let showRow = true;

            // Get the relevant cells based on the table type
            const contractCell = row.querySelector('td:nth-child(1)'); // Contract Number or Category
            const commonNameCell = row.querySelector('td:nth-child(2)') || row.querySelector('td:nth-child(1)'); // Common Name (varies by table)

            if (globalFilter.contractNumber) {
                const contractValue = contractCell ? contractCell.textContent.toLowerCase() : '';
                if (!contractValue.includes(globalFilter.contractNumber)) {
                    showRow = false;
                }
            }

            if (globalFilter.commonName) {
                const commonNameValue = commonNameCell ? commonNameCell.textContent.toLowerCase() : '';
                if (!commonNameValue.includes(globalFilter.commonName)) {
                    showRow = false;
                }
            }

            if (showRow) {
                row.style.display = '';
                visibleRows++;
                const expandableRow = row.nextElementSibling;
                if (expandableRow && expandableRow.classList.contains('expandable')) {
                    expandableRow.style.display = '';
                    // If this row has an expanded section, reapply filter to its children
                    const childTable = expandableRow.querySelector('.common-table, .item-table');
                    if (childTable) {
                        applyFilterToTable(childTable);
                    }
                }
            } else {
                row.style.display = 'none';
                const expandableRow = row.nextElementSibling;
                if (expandableRow && expandableRow.classList.contains('expandable')) {
                    expandableRow.style.display = 'none';
                }
            }
        });
    }

    // Update row count
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