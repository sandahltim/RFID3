console.log('expand.js version: 2025-04-27-v75 loaded - confirming script load');

// Note: Common function - will be moved to common.js during split
function showLoading(key) {
    const loadingDiv = document.getElementById(`loading-${key}`);
    if (loadingDiv) {
        console.log('Loading indicator found, displaying:', loadingDiv);
        loadingDiv.style.display = 'block';
    } else {
        console.warn(`Loading indicator with ID loading-${key} not found`);
    }
}

// Note: Common function - will be moved to common.js during split
function hideLoading(key) {
    const loadingDiv = document.getElementById(`loading-${key}`);
    if (loadingDiv) {
        console.log('Loading indicator found, hiding:', loadingDiv);
        loadingDiv.style.display = 'none';
    } else {
        console.warn(`Loading indicator with ID loading-${key} not found`);
    }
}

// Note: Common function - will be moved to common.js during split
function toggleCollapseButton(targetId) {
    const expandBtn = document.querySelector(`[data-target-id="${targetId}"]`);
    const collapseBtn = document.querySelector(`[data-collapse-target="${targetId}"]`);
    if (expandBtn && collapseBtn) {
        expandBtn.style.display = expandBtn.style.display === 'none' ? 'inline-block' : 'none';
        collapseBtn.style.display = collapseBtn.style.display === 'none' ? 'inline-block' : 'none';
    } else {
        console.warn(`Expand or collapse button not found for targetId ${targetId}`);
    }
}

// Sorting state for common names and items tables
let commonSortState = {};
let itemSortState = {};

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
        applyGlobalFilter(); // Apply the saved filter on page load
    } else {
        // Ensure all data is shown by default
        applyFilterToAllLevels();
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
    // Apply to category table (top level)
    const categoryTable = document.getElementById('category-table');
    if (categoryTable) {
        applyFilterToTable(categoryTable);
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

// Note: Event listener for Tabs 2, 3, 4, Categories, and Home
document.addEventListener('DOMContentLoaded', function() {
    console.log('expand.js: DOMContentLoaded event fired');

    // Ensure window.cachedTabNum is set
    if (!window.cachedTabNum) {
        const pathMatch = window.location.pathname.match(/\/tab\/(\d+)/);
        window.cachedTabNum = pathMatch ? parseInt(pathMatch[1], 10) : (window.location.pathname === '/' ? 1 : null);
        console.log('expand.js: Set window.cachedTabNum:', window.cachedTabNum);
    } else {
        console.log('expand.js: window.cachedTabNum already set:', window.cachedTabNum);
    }

    // Skip if we're on Tab 1 or Tab 5, as they use tab1_5.js
    if (window.cachedTabNum === 1 || window.cachedTabNum === 5) {
        console.log('Tab 1 or Tab 5 detected, skipping expand.js event listeners');
        return;
    }

    // Clear outdated sessionStorage entries that don't match current tab
    Object.keys(sessionStorage).forEach(key => {
        if (key.startsWith('expanded_') || key.startsWith('expanded_common_') || key.startsWith('expanded_items_')) {
            try {
                const state = JSON.parse(sessionStorage.getItem(key));
                const targetId = key.replace(/^(expanded_|expanded_common_|expanded_items_)/, '');
                if (!document.getElementById(targetId) && !document.getElementById(`common-${targetId}`) && !document.getElementById(`items-${targetId}`)) {
                    console.log(`Removing outdated sessionStorage entry: ${key}`);
                    sessionStorage.removeItem(key);
                }
            } catch (e) {
                console.error('Error parsing sessionStorage for', key, ':', e);
                sessionStorage.removeItem(key);
            }
        }
    });

    // Do not automatically expand any sections on load
    console.log('Skipping automatic expansion on load');

    // Remove any existing click event listeners to prevent duplicates
    document.removeEventListener('click', handleClick);
    console.log('Attaching click event listener for expand.js');
    document.addEventListener('click', handleClick);

    function handleClick(event) {
        console.log('handleClick triggered', event.target);
        const expandBtn = event.target.closest('.expand-btn');
        if (expandBtn) {
            event.stopPropagation();
            console.log('Expand button clicked:', expandBtn);
            const category = expandBtn.getAttribute('data-category');
            const commonName = expandBtn.getAttribute('data-common-name');
            const targetId = expandBtn.getAttribute('data-target-id');
            const contractNumber = expandBtn.getAttribute('data-contract-number');

            if (commonName) {
                // Expand to items level
                console.log('Expanding items for:', { contractNumber, commonName, targetId });
                expandItems(contractNumber, commonName, targetId);
            } else {
                // Expand to common names level (Tabs 2 and 4)
                console.log('Expanding common names for:', { contractNumber, targetId });
                expandCategory(contractNumber, targetId, contractNumber);
            }
            return;
        }

        const collapseBtn = event.target.closest('.collapse-btn');
        if (collapseBtn) {
            event.stopPropagation();
            console.log('Collapse button clicked:', collapseBtn);
            const targetId = collapseBtn.getAttribute('data-collapse-target');
            collapseSection(targetId);
            return;
        }

        const header = event.target.closest('.common-table th');
        if (header) {
            console.log('Common table header clicked:', header);
            const table = header.closest('table');
            const contractNumber = table.closest('.expandable').id.replace('common-', '');
            const column = header.textContent.trim().toLowerCase().replace(/\s+/g, '_');
            sortCommonNames(contractNumber, column);
            return;
        }

        const itemHeader = event.target.closest('.item-table th');
        if (itemHeader) {
            console.log('Item table header clicked:', itemHeader);
            const table = itemHeader.closest('table');
            const itemId = table.closest('.expandable').id;
            const contractNumber = itemId.split('-')[0];
            const commonName = itemId.split('-').slice(1).join('-').replace(/_/g, ' ');
            const column = itemHeader.textContent.trim().toLowerCase().replace(/\s+/g, '_');
            sortItems(contractNumber, commonName, column);
            return;
        }
    }

    // Define expandCategory for Tabs 2 and 4 (load common names directly under contract)
    window.expandCategory = function(category, targetId, contractNumber, page = 1) {
        console.log('expandCategory called with', { category, targetId, contractNumber, page });

        const targetElement = document.getElementById(targetId);
        if (!targetElement) {
            console.error(`Target element with ID ${targetId} not found`);
            return;
        }

        // Check if already expanded
        if (targetElement.classList.contains('expanded')) {
            console.log(`Section ${targetId} is already expanded, collapsing instead`);
            collapseSection(targetId);
            return;
        }

        // Show loading indicator
        showLoading(contractNumber);

        // Fetch common names for the contract
        fetch(`/tab/${window.cachedTabNum}/common_names?contract_number=${encodeURIComponent(contractNumber)}&page=${page}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Error fetching common names:', data.error);
                    targetElement.innerHTML = `<p>Error: ${data.error}</p>`;
                    return;
                }

                const commonNames = data.common_names || [];
                const totalCommonNames = data.total_common_names || 0;
                const perPage = data.per_page || 10;
                const currentPage = data.page || 1;

                // Build the common names table with consistent styling
                let html = `
                    <div class="subcategory-container">
                        <table class="table table-bordered table-hover common-table">
                            <thead class="thead-dark">
                                <tr>
                                    <th>Common Name <span class="sort-arrow"></span></th>
                                    <th>Items on Contract <span class="sort-arrow"></span></th>
                                    <th>Total Items in Inventory <span class="sort-arrow"></span></th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                `;

                commonNames.forEach(common => {
                    const commonId = `${contractNumber}-${common.name.replace(/[^a-zA-Z0-9]/g, '_')}`;
                    const escapedCommonName = common.name.replace(/'/g, "\\'").replace(/"/g, '\\"');
                    html += `
                        <tr>
                            <td class="expandable-cell" onclick="expandItems('${contractNumber}', '${escapedCommonName}', 'items-${commonId}')">${common.name}</td>
                            <td>${common.on_contracts}</td>
                            <td>${common.is_hand_counted ? 'N/A' : common.total_items_inventory}</td>
                            <td>
                                <button class="btn btn-sm btn-secondary expand-btn" data-common-name="${common.name}" data-target-id="items-${commonId}" data-contract-number="${contractNumber}">Expand</button>
                                <button class="btn btn-sm btn-secondary collapse-btn" data-collapse-target="items-${commonId}" style="display:none;">Collapse</button>
                                <button class="btn btn-sm btn-info print-btn" data-print-level="Common Name" data-print-id="items-${commonId}" data-common-name="${common.name}" data-category="${contractNumber}">Print</button>
                                <button class="btn btn-sm btn-info print-full-btn" data-common-name="${common.name}" data-category="${contractNumber}">Print Full List</button>
                                <div id="loading-${commonId}" style="display:none;" class="loading">Loading...</div>
                            </td>
                        </tr>
                        <tr>
                            <td colspan="4">
                                <div id="items-${commonId}" class="expandable collapsed item-level"></div>
                            </td>
                        </tr>
                    `;
                });

                html += `
                            </tbody>
                        </table>
                    </div>
                `;

                // Add pagination controls if needed
                if (totalCommonNames > perPage) {
                    const totalPages = Math.ceil(totalCommonNames / perPage);
                    html += `
                        <div class="pagination-controls mt-2">
                            <button class="btn btn-sm btn-secondary" onclick="window.expandCategory('${category}', '${targetId}', '${contractNumber}', ${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>
                            <span class="mx-2">Page ${currentPage} of ${totalPages}</span>
                            <button class="btn btn-sm btn-secondary" onclick="window.expandCategory('${category}', '${targetId}', '${contractNumber}', ${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>
                        </div>
                    `;
                }

                targetElement.innerHTML = html;
                targetElement.classList.remove('collapsed');
                targetElement.classList.add('expanded');
                toggleCollapseButton(targetId);

                // Apply global filter to the newly loaded table
                const table = targetElement.querySelector('.common-table');
                if (table) applyFilterToTable(table);

                // Save expanded state
                sessionStorage.setItem(`expanded_${targetId}`, JSON.stringify({ expanded: true }));
            })
            .catch(error => {
                console.error('Error fetching common names:', error);
                targetElement.innerHTML = '<p>Failed to load common names</p>';
            })
            .finally(() => {
                hideLoading(contractNumber);
            });
    };

    // Function to expand items under a common name
    window.expandItems = function(contractNumber, commonName, targetId, page = 1) {
        console.log('expandItems called with', { contractNumber, commonName, targetId, page });

        const targetElement = document.getElementById(targetId);
        if (!targetElement) {
            console.error(`Target element with ID ${targetId} not found`);
            return;
        }

        // Check if already expanded
        if (targetElement.classList.contains('expanded')) {
            console.log(`Section ${targetId} is already expanded, collapsing instead`);
            collapseSection(targetId);
            return;
        }

        // Show loading indicator
        const commonId = targetId.replace('items-', '');
        showLoading(commonId);

        // Fetch items for the common name
        fetch(`/tab/${window.cachedTabNum}/data?contract_number=${encodeURIComponent(contractNumber)}&common_name=${encodeURIComponent(commonName)}&page=${page}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Error fetching items:', data.error);
                    targetElement.innerHTML = `<p>Error: ${data.error}</p>`;
                    return;
                }

                const items = data.items || [];
                const totalItems = data.total_items || 0;
                const perPage = data.per_page || 10;
                const currentPage = data.page || 1;

                // Build the items table with consistent styling
                let html = `
                    <div class="item-level-wrapper ml-4">
                        <table class="table table-bordered table-hover item-table">
                            <thead class="thead-dark">
                                <tr>
                                    <th>Tag ID <span class="sort-arrow"></span></th>
                                    <th>Common Name <span class="sort-arrow"></span></th>
                                    <th>Bin Location <span class="sort-arrow"></span></th>
                                    <th>Status <span class="sort-arrow"></span></th>
                                    <th>Last Contract <span class="sort-arrow"></span></th>
                                    <th>Last Scanned Date <span class="sort-arrow"></span></th>
                                </tr>
                            </thead>
                            <tbody>
                `;

                items.forEach(item => {
                    html += `
                        <tr>
                            <td>${item.tag_id}</td>
                            <td>${item.common_name}</td>
                            <td>${item.bin_location || 'N/A'}</td>
                            <td>${item.status}</td>
                            <td>${item.last_contract_num || 'N/A'}</td>
                            <td>${item.last_scanned_date || 'N/A'}</td>
                        </tr>
                    `;
                });

                html += `
                            </tbody>
                        </table>
                    </div>
                `;

                // Add pagination controls if needed
                const escapedCommonName = commonName.replace(/'/g, "\\'").replace(/"/g, '\\"');
                if (totalItems > perPage) {
                    const totalPages = Math.ceil(totalItems / perPage);
                    html += `
                        <div class="pagination-controls mt-2 ml-4">
                            <button class="btn btn-sm btn-secondary" onclick="expandItems('${contractNumber}', '${escapedCommonName}', '${targetId}', ${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>
                            <span class="mx-2">Page ${currentPage} of ${totalPages}</span>
                            <button class="btn btn-sm btn-secondary" onclick="expandItems('${contractNumber}', '${escapedCommonName}', '${targetId}', ${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>
                        </div>
                    `;
                }

                targetElement.innerHTML = html;
                targetElement.classList.remove('collapsed');
                targetElement.classList.add('expanded');
                toggleCollapseButton(targetId);

                // Apply global filter to the newly loaded table
                const table = targetElement.querySelector('.item-table');
                if (table) applyFilterToTable(table);

                // Save expanded state
                sessionStorage.setItem(`expanded_items_${targetId}`, JSON.stringify({ expanded: true }));
            })
            .catch(error => {
                console.error('Error fetching items:', error);
                targetElement.innerHTML = '<p>Failed to load items</p>';
            })
            .finally(() => {
                hideLoading(commonId);
            });
    }

    // Function to sort common names table
    function sortCommonNames(contractNumber, column) {
        const targetId = `common-${contractNumber}`;
        if (!commonSortState[contractNumber]) {
            commonSortState[contractNumber] = { column: '', direction: '' };
        }

        let direction = 'asc';
        if (commonSortState[contractNumber].column === column) {
            direction = commonSortState[contractNumber].direction === 'asc' ? 'desc' : 'asc';
        }
        commonSortState[contractNumber] = { column, direction };

        // Update sort arrows
        const headers = document.querySelectorAll(`#${targetId} .common-table thead tr:first-child th`);
        headers.forEach(header => {
            const sortArrow = header.querySelector('.sort-arrow') || document.createElement('span');
            sortArrow.className = 'sort-arrow';
            if (!header.querySelector('.sort-arrow')) header.appendChild(sortArrow);
            if (header.textContent.trim().toLowerCase().replace(/\s+/g, '_') === column) {
                sortArrow.textContent = direction === 'asc' ? '↑' : '↓';
            } else {
                sortArrow.textContent = '';
            }
        });

        // Fetch sorted data
        fetch(`/tab/${window.cachedTabNum}/common_names?contract_number=${encodeURIComponent(contractNumber)}&sort=${column}_${direction}`)
            .then(response => response.json())
            .then(data => {
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
                                    <th>Common Name <span class="sort-arrow"></span></th>
                                    <th>Items on Contract <span class="sort-arrow"></span></th>
                                    <th>Total Items in Inventory <span class="sort-arrow"></span></th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                `;

                commonNames.forEach(common => {
                    const commonId = `${contractNumber}-${common.name.replace(/[^a-zA-Z0-9]/g, '_')}`;
                    const escapedCommonName = common.name.replace(/'/g, "\\'").replace(/"/g, '\\"');
                    html += `
                        <tr>
                            <td class="expandable-cell" onclick="expandItems('${contractNumber}', '${escapedCommonName}', 'items-${commonId}')">${common.name}</td>
                            <td>${common.on_contracts}</td>
                            <td>${common.is_hand_counted ? 'N/A' : common.total_items_inventory}</td>
                            <td>
                                <button class="btn btn-sm btn-secondary expand-btn" data-common-name="${common.name}" data-target-id="items-${commonId}" data-contract-number="${contractNumber}">Expand</button>
                                <button class="btn btn-sm btn-secondary collapse-btn" data-collapse-target="items-${commonId}" style="display:none;">Collapse</button>
                                <button class="btn btn-sm btn-info print-btn" data-print-level="Common Name" data-print-id="items-${commonId}" data-common-name="${common.name}" data-category="${contractNumber}">Print</button>
                                <button class="btn btn-sm btn-info print-full-btn" data-common-name="${common.name}" data-category="${contractNumber}">Print Full List</button>
                                <div id="loading-${commonId}" style="display:none;" class="loading">Loading...</div>
                            </td>
                        </tr>
                        <tr>
                            <td colspan="4">
                                <div id="items-${commonId}" class="expandable collapsed item-level"></div>
                            </td>
                        </tr>
                    `;
                });

                html += `
                            </tbody>
                        </table>
                    </div>
                `;

                // Add pagination controls
                if (totalCommonNames > perPage) {
                    const totalPages = Math.ceil(totalCommonNames / perPage);
                    html += `
                        <div class="pagination-controls mt-2">
                            <button class="btn btn-sm btn-secondary" onclick="window.expandCategory('${contractNumber}', '${targetId}', '${contractNumber}', ${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>
                            <span class="mx-2">Page ${currentPage} of ${totalPages}</span>
                            <button class="btn btn-sm btn-secondary" onclick="window.expandCategory('${contractNumber}', '${targetId}', '${contractNumber}', ${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>
                        </div>
                    `;
                }

                targetElement.innerHTML = html;
                const table = targetElement.querySelector('.common-table');
                if (table) applyFilterToTable(table);
            })
            .catch(error => {
                console.error('Error sorting common names:', error);
            });
    }

    // Function to sort items table
    function sortItems(contractNumber, commonName, column) {
        const targetId = `items-${contractNumber}-${commonName.replace(/[^a-zA-Z0-9]/g, '_')}`;
        if (!itemSortState[targetId]) {
            itemSortState[targetId] = { column: '', direction: '' };
        }

        let direction = 'asc';
        if (itemSortState[targetId].column === column) {
            direction = itemSortState[targetId].direction === 'asc' ? 'desc' : 'asc';
        }
        itemSortState[targetId] = { column, direction };

        // Update sort arrows
        const headers = document.querySelectorAll(`#${targetId} .item-table thead tr:first-child th`);
        headers.forEach(header => {
            const sortArrow = header.querySelector('.sort-arrow') || document.createElement('span');
            sortArrow.className = 'sort-arrow';
            if (!header.querySelector('.sort-arrow')) header.appendChild(sortArrow);
            if (header.textContent.trim().toLowerCase().replace(/\s+/g, '_') === column) {
                sortArrow.textContent = direction === 'asc' ? '↑' : '↓';
            } else {
                sortArrow.textContent = '';
            }
        });

        // Fetch sorted data
        fetch(`/tab/${window.cachedTabNum}/data?contract_number=${encodeURIComponent(contractNumber)}&common_name=${encodeURIComponent(commonName)}&sort=${column}_${direction}`)
            .then(response => response.json())
            .then(data => {
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
                                    <th>Tag ID <span class="sort-arrow"></span></th>
                                    <th>Common Name <span class="sort-arrow"></span></th>
                                    <th>Bin Location <span class="sort-arrow"></span></th>
                                    <th>Status <span class="sort-arrow"></span></th>
                                    <th>Last Contract <span class="sort-arrow"></span></th>
                                    <th>Last Scanned Date <span class="sort-arrow"></span></th>
                                </tr>
                            </thead>
                            <tbody>
                `;

                items.forEach(item => {
                    html += `
                        <tr>
                            <td>${item.tag_id}</td>
                            <td>${item.common_name}</td>
                            <td>${item.bin_location || 'N/A'}</td>
                            <td>${item.status}</td>
                            <td>${item.last_contract_num || 'N/A'}</td>
                            <td>${item.last_scanned_date || 'N/A'}</td>
                        </tr>
                    `;
                });

                html += `
                            </tbody>
                        </table>
                    </div>
                `;

                // Add pagination controls
                const escapedCommonName = commonName.replace(/'/g, "\\'").replace(/"/g, '\\"');
                if (totalItems > perPage) {
                    const totalPages = Math.ceil(totalItems / perPage);
                    html += `
                        <div class="pagination-controls mt-2 ml-4">
                            <button class="btn btn-sm btn-secondary" onclick="expandItems('${contractNumber}', '${escapedCommonName}', '${targetId}', ${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>
                            <span class="mx-2">Page ${currentPage} of ${totalPages}</span>
                            <button class="btn btn-sm btn-secondary" onclick="expandItems('${contractNumber}', '${escapedCommonName}', '${targetId}', ${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>
                        </div>
                    `;
                }

                targetElement.innerHTML = html;
                const table = targetElement.querySelector('.item-table');
                if (table) applyFilterToTable(table);
            })
            .catch(error => {
                console.error('Error sorting items:', error);
            });
    }

    // Function to collapse a section
    function collapseSection(targetId) {
        console.log('collapseSection called with targetId:', targetId);
        const targetElement = document.getElementById(targetId);
        if (targetElement) {
            targetElement.classList.remove('expanded');
            targetElement.classList.add('collapsed');
            targetElement.innerHTML = '';
            toggleCollapseButton(targetId);
            sessionStorage.removeItem(`expanded_${targetId}`);
            sessionStorage.removeItem(`expanded_items_${targetId}`);
            console.log(`Section ${targetId} collapsed`);
        } else {
            console.error(`Target element with ID ${targetId} not found for collapsing`);
        }
    }
});