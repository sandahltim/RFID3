console.log('common.js version: 2025-04-27-v6 loaded - confirming script load');

// Function to format ISO date strings into "Thurs, Aug 21 2025 4:55 pm"
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
        const categoryTable = document.getElementById('category-table');
        if (!categoryTable) return;

        const rows = categoryTable.querySelectorAll('tbody tr:not(.expandable)');
        let visibleRows = 0;

        rows.forEach(row => {
            let showRow = true;

            // Check the subcategory dropdown options
            const subcatSelect = row.querySelector('.subcategory-select');
            const options = subcatSelect ? subcatSelect.querySelectorAll('option:not([value=""])') : [];
            let visibleOptions = 0;
            const selectedOption = subcatSelect ? subcatSelect.options[subcatSelect.selectedIndex] : null;
            const selectedValue = selectedOption ? selectedOption.value : '';

            // Check if the expanded common name table contains matching items
            const expandableRow = row.nextElementSibling;
            let hasMatchingCommonNames = false;
            if (expandableRow && expandableRow.classList.contains('expandable')) {
                const commonTable = expandableRow.querySelector('.common-table');
                if (commonTable) {
                    const commonRows = commonTable.querySelectorAll('tbody tr:not(.expandable)');
                    commonRows.forEach(commonRow => {
                        let showCommonRow = true;
                        const commonNameCell = commonRow.querySelector('td:nth-child(1)'); // Common Name column
                        if (globalFilter.commonName) {
                            const commonNameValue = commonNameCell ? commonNameCell.textContent.toLowerCase() : '';
                            if (!commonNameValue.includes(globalFilter.commonName)) {
                                showCommonRow = false;
                            }
                        }
                        commonRow.style.display = showCommonRow ? '' : 'none';
                        const commonExpandableRow = commonRow.nextElementSibling;
                        if (commonExpandableRow && commonExpandableRow.classList.contains('expandable')) {
                            commonExpandableRow.style.display = showCommonRow ? '' : 'none';
                            // Check expanded item tables
                            const itemTable = commonExpandableRow.querySelector('.item-table');
                            if (itemTable) {
                                const itemRows = itemTable.querySelectorAll('tbody tr');
                                let visibleItemRows = 0;
                                itemRows.forEach(itemRow => {
                                    let showItemRow = true;
                                    const itemCommonNameCell = itemRow.querySelector('td:nth-child(2)'); // Common Name column in item table
                                    if (globalFilter.commonName) {
                                        const itemCommonNameValue = itemCommonNameCell ? itemCommonNameCell.textContent.toLowerCase() : '';
                                        if (!itemCommonNameValue.includes(globalFilter.commonName)) {
                                            showItemRow = false;
                                        }
                                    }
                                    itemRow.style.display = showItemRow ? '' : 'none';
                                    if (showItemRow) visibleItemRows++;
                                });
                                if (visibleItemRows > 0) hasMatchingCommonNames = true;
                                // Update item table row count
                                let itemRowCountDiv = itemTable.nextElementSibling;
                                if (itemRowCountDiv && !itemRowCountDiv.classList.contains('row-count')) {
                                    itemRowCountDiv = document.createElement('div');
                                    itemRowCountDiv.className = 'row-count mt-2';
                                    itemTable.insertAdjacentElement('afterend', itemRowCountDiv);
                                }
                                if (itemRowCountDiv) {
                                    itemRowCountDiv.textContent = `Showing ${visibleItemRows} of ${itemRows.length} rows`;
                                }
                            }
                        }
                        if (showCommonRow) hasMatchingCommonNames = true;
                    });
                    // Update common table row count
                    const visibleCommonRows = Array.from(commonRows).filter(r => r.style.display !== 'none').length;
                    let commonRowCountDiv = commonTable.nextElementSibling;
                    if (commonRowCountDiv && !commonRowCountDiv.classList.contains('row-count')) {
                        commonRowCountDiv = document.createElement('div');
                        commonRowCountDiv.className = 'row-count mt-2';
                        commonTable.insertAdjacentElement('afterend', commonRowCountDiv);
                    }
                    if (commonRowCountDiv) {
                        commonRowCountDiv.textContent = `Showing ${visibleCommonRows} of ${commonRows.length} rows`;
                    }
                }
            }

            // Filter subcategory dropdown options, but ensure the selected option is considered
            if (globalFilter.commonName) {
                options.forEach(option => {
                    let showOption = false;
                    const subcatValue = option.textContent.toLowerCase();
                    // Show the option if it matches the filter or if it's the selected option and has matching common names
                    if (subcatValue.includes(globalFilter.commonName)) {
                        showOption = true;
                    } else if (option.value === selectedValue && hasMatchingCommonNames) {
                        showOption = true;
                    }
                    option.style.display = showOption ? '' : 'none';
                    if (showOption) visibleOptions++;
                });
            } else {
                options.forEach(option => {
                    option.style.display = '';
                    visibleOptions++;
                });
            }

            // Show the category row if there are visible subcategory options, matching common names, or if no filter is applied
            if (!globalFilter.commonName && !globalFilter.contractNumber) {
                showRow = true;
            } else {
                showRow = visibleOptions > 0 || hasMatchingCommonNames;
            }

            row.style.display = showRow ? '' : 'none';
            if (expandableRow) {
                expandableRow.style.display = showRow ? '' : 'none';
            }
            if (showRow) visibleRows++;
        });

        // Update category table row count
        let rowCountDiv = document.querySelector('.row-count');
        if (!rowCountDiv) {
            rowCountDiv = document.createElement('div');
            rowCountDiv.className = 'row-count mt-2';
            categoryTable.insertAdjacentElement('afterend', rowCountDiv);
        }
        rowCountDiv.textContent = `Showing ${visibleRows} of ${rows.length} rows`;
    } else {
        // Apply to category table (top level) for Tabs 2 and 4
        const categoryTable = document.getElementById('category-table');
        if (categoryTable) {
            applyFilterToTable(categoryTable);
        }
    }

    // Apply to all expanded common name tables (for Tabs 2 and 4)
    const commonTables = document.querySelectorAll('.common-table');
    commonTables.forEach(table => {
        applyFilterToTable(table);
    });

    // Apply to all expanded item tables (for Tabs 2 and 4)
    const itemTables = document.querySelectorAll('.item-table');
    itemTables.forEach(table => {
        applyFilterToTable(table);
    });
}

// Apply filter to a specific table (used for Tabs 2 and 4)
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