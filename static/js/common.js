console.log('common.js version: 2025-05-07-v8 loaded - confirming script load');

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
    // Skip global filter for Tab 3
    if (window.cachedTabNum === 3) {
        console.log('Skipping global filter application for Tab 3');
        return;
    }

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

// Apply filter to all levels (category, subcategory, common names, items)
function applyFilterToAllLevels() {
    // Skip filtering for Tab 3
    if (window.cachedTabNum === 3) {
        console.log('Skipping applyFilterToAllLevels for Tab 3');
        return;
    }

    // For Tabs 1 and 5 (handled by tab1_5.js)
    if (window.cachedTabNum === 1 || window.cachedTabNum === 5) {
        const categoryTable = document.getElementById('category-table');
        if (!categoryTable) return;

        const categoryRows = categoryTable.querySelectorAll('tbody tr:not(.expandable)');
        let visibleCategoryRows = 0;

        categoryRows.forEach(categoryRow => {
            let showCategoryRow = false;
            const categoryCell = categoryRow.querySelector('td:nth-child(1)'); // Category column
            const categoryValue = categoryCell ? categoryCell.textContent.toLowerCase() : '';
            const subcatSelect = categoryRow.querySelector('.subcategory-select');
            const expandableRow = categoryRow.nextElementSibling;
            const commonLevelDiv = expandableRow.querySelector('.common-level');
            let visibleSubcategories = 0;
            let hasMatchingItems = false;

            // Filter subcategory dropdown options and check for matching items
            const options = subcatSelect ? subcatSelect.querySelectorAll('option:not([value=""])') : [];
            const selectedOption = subcatSelect ? subcatSelect.options[subcatSelect.selectedIndex] : null;
            const selectedValue = selectedOption ? selectedOption.value : '';

            // If a subcategory is selected, we need to check its common names and items
            if (selectedValue) {
                const commonTable = commonLevelDiv.querySelector('.common-table');
                if (commonTable) {
                    const commonRows = commonTable.querySelectorAll('tbody tr:not(.expandable)');
                    let visibleCommonRows = 0;

                    commonRows.forEach(commonRow => {
                        let showCommonRow = false;
                        const commonNameCell = commonRow.querySelector('td:nth-child(1)'); // Common Name column
                        const commonNameValue = commonNameCell ? commonNameCell.textContent.toLowerCase() : '';

                        // Check if the common name matches the filter
                        if (globalFilter.commonName) {
                            if (commonNameValue.includes(globalFilter.commonName)) {
                                showCommonRow = true;
                            }
                        } else {
                            showCommonRow = true; // Show all if no common name filter
                        }

                        // Check expanded item tables if they exist
                        const commonExpandableRow = commonRow.nextElementSibling;
                        let visibleItemRows = 0;
                        if (commonExpandableRow && commonExpandableRow.classList.contains('expandable')) {
                            const itemTable = commonExpandableRow.querySelector('.item-table');
                            if (itemTable) {
                                const itemRows = itemTable.querySelectorAll('tbody tr');
                                itemRows.forEach(itemRow => {
                                    let showItemRow = true;
                                    const itemCommonNameCell = itemRow.querySelector('td:nth-child(2)'); // Common Name column in item table
                                    const itemContractCell = itemRow.querySelector('td:nth-child(5)'); // Last Contract column in item table
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
                                        showCommonRow = true; // If any item matches, show the common name row
                                        hasMatchingItems = true;
                                    }
                                });

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

                                // Expand the item section if there are matching items
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
                                    commonExpandableRow.style.display = 'none';
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

                    // Update common table row count
                    let commonRowCountDiv = commonTable.nextElementSibling;
                    if (commonRowCountDiv && !commonRowCountDiv.classList.contains('row-count')) {
                        commonRowCountDiv = document.createElement('div');
                        commonRowCountDiv.className = 'row-count mt-2';
                        commonTable.insertAdjacentElement('afterend', commonRowCountDiv);
                    }
                    if (commonRowCountDiv) {
                        commonRowCountDiv.textContent = `Showing ${visibleCommonRows} of ${commonRows.length} rows`;
                    }

                    // Show the subcategory if there are matching common names or items
                    if (visibleCommonRows > 0 || hasMatchingItems) {
                        visibleSubcategories++;
                        showCategoryRow = true;

                        // Expand the common names section
                        commonLevelDiv.classList.remove('collapsed');
                        commonLevelDiv.classList.add('expanded');
                        commonLevelDiv.style.display = 'block';
                        commonLevelDiv.style.opacity = '1';
                        const categoryExpandBtn = categoryRow.querySelector('.expand-btn');
                        const categoryCollapseBtn = categoryRow.querySelector('.collapse-btn');
                        if (categoryExpandBtn && categoryCollapseBtn) {
                            categoryExpandBtn.style.display = 'none';
                            categoryCollapseBtn.style.display = 'inline-block';
                        }
                    } else {
                        commonLevelDiv.classList.remove('expanded');
                        commonLevelDiv.classList.add('collapsed');
                        commonLevelDiv.style.display = 'none';
                        commonLevelDiv.style.opacity = '0';
                        const categoryExpandBtn = categoryRow.querySelector('.expand-btn');
                        const categoryCollapseBtn = categoryRow.querySelector('.collapse-btn');
                        if (categoryExpandBtn && categoryCollapseBtn) {
                            categoryExpandBtn.style.display = 'inline-block';
                            categoryCollapseBtn.style.display = 'none';
                        }
                    }
                } else {
                    // If no common names are loaded, check subcategory items directly
                    options.forEach(option => {
                        const subcatValue = option.textContent.toLowerCase();
                        if (subcatValue === selectedValue) {
                            // Fetch common names and items to check for matches
                            fetch(`/tab/${window.cachedTabNum}/common_names?category=${encodeURIComponent(categoryValue)}&subcategory=${encodeURIComponent(subcatValue)}`)
                                .then(response => response.json())
                                .then(data => {
                                    const commonNames = data.common_names || [];
                                    let hasMatches = false;

                                    commonNames.forEach(common => {
                                        const commonNameValue = common.name.toLowerCase();
                                        if (globalFilter.commonName && commonNameValue.includes(globalFilter.commonName)) {
                                            hasMatches = true;
                                            return;
                                        }

                                        // Fetch items for this common name
                                        fetch(`/tab/${window.cachedTabNum}/data?category=${encodeURIComponent(categoryValue)}&subcategory=${encodeURIComponent(subcatValue)}&common_name=${encodeURIComponent(common.name)}`)
                                            .then(itemResponse => itemResponse.json())
                                            .then(itemData => {
                                                const items = itemData.items || [];
                                                items.forEach(item => {
                                                    const itemCommonNameValue = item.common_name.toLowerCase();
                                                    const itemContractValue = item.last_contract_num ? item.last_contract_num.toLowerCase() : '';
                                                    if (globalFilter.commonName && itemCommonNameValue.includes(globalFilter.commonName)) {
                                                        hasMatches = true;
                                                    }
                                                    if (globalFilter.contractNumber && itemContractValue.includes(globalFilter.contractNumber)) {
                                                        hasMatches = true;
                                                    }
                                                });

                                                if (hasMatches) {
                                                    visibleSubcategories++;
                                                    showCategoryRow = true;
                                                    option.style.display = '';
                                                    subcatSelect.value = subcatValue; // Select this subcategory
                                                    loadCommonNames(subcatSelect); // Load common names to display matches
                                                }
                                            })
                                            .catch(error => console.error('Error fetching items for filtering:', error));
                                    });
                                })
                                .catch(error => console.error('Error fetching common names for filtering:', error));
                        }
                    });
                }
            } else {
                // If no subcategory is selected, check all subcategories
                options.forEach(option => {
                    let showOption = false;
                    const subcatValue = option.textContent.toLowerCase();
                    if (globalFilter.commonName) {
                        if (subcatValue.includes(globalFilter.commonName)) {
                            showOption = true;
                        }
                    }

                    // Fetch common names and items to check for matches
                    fetch(`/tab/${window.cachedTabNum}/common_names?category=${encodeURIComponent(categoryValue)}&subcategory=${encodeURIComponent(subcatValue)}`)
                        .then(response => response.json())
                        .then(data => {
                            const commonNames = data.common_names || [];
                            let hasMatches = false;

                            commonNames.forEach(common => {
                                const commonNameValue = common.name.toLowerCase();
                                if (globalFilter.commonName && commonNameValue.includes(globalFilter.commonName)) {
                                    hasMatches = true;
                                    return;
                                }

                                // Fetch items for this common name
                                fetch(`/tab/${window.cachedTabNum}/data?category=${encodeURIComponent(categoryValue)}&subcategory=${encodeURIComponent(subcatValue)}&common_name=${encodeURIComponent(common.name)}`)
                                    .then(itemResponse => itemResponse.json())
                                    .then(itemData => {
                                        const items = itemData.items || [];
                                        items.forEach(item => {
                                            const itemCommonNameValue = item.common_name.toLowerCase();
                                            const itemContractValue = item.last_contract_num ? item.last_contract_num.toLowerCase() : '';
                                            if (globalFilter.commonName && itemCommonNameValue.includes(globalFilter.commonName)) {
                                                hasMatches = true;
                                            }
                                            if (globalFilter.contractNumber && itemContractValue.includes(globalFilter.contractNumber)) {
                                                hasMatches = true;
                                            }
                                        });

                                        if (hasMatches) {
                                            showOption = true;
                                            visibleSubcategories++;
                                            showCategoryRow = true;
                                        }
                                        option.style.display = showOption ? '' : 'none';
                                        if (showOption && visibleSubcategories === 1 && !subcatSelect.value) {
                                            subcatSelect.value = subcatValue; // Select the first matching subcategory
                                            loadCommonNames(subcatSelect); // Load common names to display matches
                                        }
                                    })
                                    .catch(error => console.error('Error fetching items for filtering:', error));
                            });
                        })
                        .catch(error => console.error('Error fetching common names for filtering:', error));
                });
            }

            // Show category row if there are visible subcategories or matching items
            if (!globalFilter.commonName && !globalFilter.contractNumber) {
                showCategoryRow = true;
                options.forEach(option => option.style.display = '');
                if (commonLevelDiv) {
                    commonLevelDiv.classList.remove('expanded');
                    commonLevelDiv.classList.add('collapsed');
                    commonLevelDiv.style.display = 'none';
                    commonLevelDiv.style.opacity = '0';
                    const categoryExpandBtn = categoryRow.querySelector('.expand-btn');
                    const categoryCollapseBtn = categoryRow.querySelector('.collapse-btn');
                    if (categoryExpandBtn && categoryCollapseBtn) {
                        categoryExpandBtn.style.display = 'inline-block';
                        categoryCollapseBtn.style.display = 'none';
                    }
                }
            }

            categoryRow.style.display = showCategoryRow ? '' : 'none';
            expandableRow.style.display = showCategoryRow ? '' : 'none';
            if (showCategoryRow) visibleCategoryRows++;
        });

        // Update category table row count
        let rowCountDiv = document.querySelector('.row-count');
        if (!rowCountDiv) {
            rowCountDiv = document.createElement('div');
            rowCountDiv.className = 'row-count mt-2';
            categoryTable.insertAdjacentElement('afterend', rowCountDiv);
        }
        rowCountDiv.textContent = `Showing ${visibleCategoryRows} of ${categoryRows.length} rows`;
    } else {
        // For Tabs 2 and 4 (handled by expand.js)
        const categoryTable = document.getElementById('category-table');
        if (!categoryTable) return;

        const categoryRows = categoryTable.querySelectorAll('tbody tr:not(.expandable)');
        let visibleCategoryRows = 0;

        categoryRows.forEach(categoryRow => {
            let showCategoryRow = false;
            const contractCell = categoryRow.querySelector('td:nth-child(1)'); // Contract Number column
            const contractValue = contractCell ? contractCell.textContent.toLowerCase() : '';
            const expandableRow = categoryRow.nextElementSibling;
            const subcatDiv = expandableRow.querySelector('.expandable');

            // Check if the contract number matches the filter
            if (globalFilter.contractNumber) {
                if (contractValue.includes(globalFilter.contractNumber)) {
                    showCategoryRow = true;
                }
            } else {
                showCategoryRow = true; // Show all if no contract filter
            }

            // Check expanded common names and items
            let hasMatchingItems = false;
            if (subcatDiv && subcatDiv.classList.contains('expanded')) {
                const commonTable = subcatDiv.querySelector('.common-table');
                if (commonTable) {
                    const commonRows = commonTable.querySelectorAll('tbody tr:not(.expandable)');
                    let visibleCommonRows = 0;

                    commonRows.forEach(commonRow => {
                        let showCommonRow = false;
                        const commonNameCell = commonRow.querySelector('td:nth-child(1)'); // Common Name column
                        const commonNameValue = commonNameCell ? commonNameCell.textContent.toLowerCase() : '';

                        if (globalFilter.commonName) {
                            if (commonNameValue.includes(globalFilter.commonName)) {
                                showCommonRow = true;
                            }
                        } else {
                            showCommonRow = true; // Show all if no common name filter
                        }

                        // Check expanded item tables
                        const commonExpandableRow = commonRow.nextElementSibling;
                        let visibleItemRows = 0;
                        if (commonExpandableRow && commonExpandableRow.classList.contains('expandable')) {
                            const itemTable = commonExpandableRow.querySelector('.item-table');
                            if (itemTable) {
                                const itemRows = itemTable.querySelectorAll('tbody tr');
                                itemRows.forEach(itemRow => {
                                    let showItemRow = true;
                                    const itemCommonNameCell = itemRow.querySelector('td:nth-child(2)'); // Common Name column
                                    const itemContractCell = itemRow.querySelector('td:nth-child(5)'); // Last Contract column
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
                                        showCommonRow = true; // If any item matches, show the common name row
                                        hasMatchingItems = true;
                                    }
                                });

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

                                // Expand the item section if there are matching items
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
                                    commonExpandableRow.style.display = 'none';
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

                    // Update common table row count
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
                        subcatDiv.style.display = 'none';
                        subcatDiv.style.opacity = '0';
                        const categoryExpandBtn = categoryRow.querySelector('.expand-btn');
                        const categoryCollapseBtn = categoryRow.querySelector('.collapse-btn');
                        if (categoryExpandBtn && categoryCollapseBtn) {
                            categoryExpandBtn.style.display = 'inline-block';
                            categoryCollapseBtn.style.display = 'none';
                        }
                    }
                } else {
                    // If not expanded, fetch common names and items to check for matches
                    fetch(`/tab/${window.cachedTabNum}/common_names?contract_number=${encodeURIComponent(contractValue)}`)
                        .then(response => response.json())
                        .then(data => {
                            const commonNames = data.common_names || [];
                            let hasMatches = false;

                            commonNames.forEach(common => {
                                const commonNameValue = common.name.toLowerCase();
                                if (globalFilter.commonName && commonNameValue.includes(globalFilter.commonName)) {
                                    hasMatches = true;
                                    return;
                                }

                                fetch(`/tab/${window.cachedTabNum}/data?contract_number=${encodeURIComponent(contractValue)}&common_name=${encodeURIComponent(common.name)}`)
                                    .then(itemResponse => itemResponse.json())
                                    .then(itemData => {
                                        const items = itemData.items || [];
                                        items.forEach(item => {
                                            const itemCommonNameValue = item.common_name.toLowerCase();
                                            const itemContractValue = item.last_contract_num ? item.last_contract_num.toLowerCase() : '';
                                            if (globalFilter.commonName && itemCommonNameValue.includes(globalFilter.commonName)) {
                                                hasMatches = true;
                                            }
                                            if (globalFilter.contractNumber && itemContractValue.includes(globalFilter.contractNumber)) {
                                                hasMatches = true;
                                            }
                                        });

                                        if (hasMatches) {
                                            showCategoryRow = true;
                                            window.expandCategory(contractValue, `subcat-${contractValue}`, contractValue);
                                        }
                                    })
                                    .catch(error => console.error('Error fetching items for filtering:', error));
                            });
                        })
                        .catch(error => console.error('Error fetching common names for filtering:', error));
                }
            }

            if (!globalFilter.commonName && !globalFilter.contractNumber) {
                showCategoryRow = true;
                if (subcatDiv) {
                    subcatDiv.classList.remove('expanded');
                    subcatDiv.classList.add('collapsed');
                    subcatDiv.style.display = 'none';
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
            expandableRow.style.display = showCategoryRow ? '' : 'none';
            if (showCategoryRow) visibleCategoryRows++;
        });

        // Update category table row count
        let rowCountDiv = document.querySelector('.row-count');
        if (!rowCountDiv) {
            rowCountDiv = document.createElement('div');
            rowCountDiv.className = 'row-count mt-2';
            categoryTable.insertAdjacentElement('afterend', rowCountDiv);
        }
        rowCountDiv.textContent = `Showing ${visibleCategoryRows} of ${categoryRows.length} rows`;
    }
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
            const contractValue = contractCell ? contractCell.textContent.toLowerCase() : '';
            const commonNameValue = commonNameCell ? commonNameCell.textContent.toLowerCase() : '';

            if (globalFilter.contractNumber && !contractValue.includes(globalFilter.contractNumber)) {
                showRow = false;
            }
            if (globalFilter.commonName && !commonNameValue.includes(globalFilter.commonName)) {
                showRow = false;
            }

            // Check child tables (common names or items)
            let hasMatchingChildren = false;
            const expandableRow = row.nextElementSibling;
            if (expandableRow && expandableRow.classList.contains('expandable')) {
                const childTable = expandableRow.querySelector('.common-table, .item-table');
                if (childTable) {
                    const childRows = childTable.querySelectorAll('tbody tr:not(.expandable)');
                    childRows.forEach(childRow => {
                        let showChildRow = true;
                        const childContractCell = childRow.querySelector('td:nth-child(1)'); // Contract Number or Category
                        const childCommonNameCell = childRow.querySelector('td:nth-child(2)') || childRow.querySelector('td:nth-child(1)'); // Common Name
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

                    // Update child table row count
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