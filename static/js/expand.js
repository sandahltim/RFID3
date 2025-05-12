console.log('expand.js version: 2025-05-07-v82 loaded - confirming script load');

// Note: Common function - will be moved to common.js during split
function showLoadingExpand(targetId) {
    const container = document.getElementById(targetId);
    if (!container) {
        console.warn(`Container with ID ${targetId} not found for showing loading indicator (expand.js)`);
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

// Note: Common function - will be moved to common.js during split
function hideLoadingExpand(targetId) {
    const loadingDiv = document.getElementById(`loading-${targetId}`);
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

// Note: Common function - will be moved to common.js during split
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
            console.warn('Could not find expand/collapse buttons for targetId:', targetId);
        }

        sessionStorage.removeItem(`expanded_${targetId}`);
        sessionStorage.removeItem(`expanded_items_${targetId}`);
    } else {
        console.error(`Section with ID ${targetId} not found for collapsing`);
    }
}

// Define expandCategory for all tabs
window.expandCategory = function(category, targetId, contractNumber, page = 1) {
    console.log('expandCategory called with', { category, targetId, contractNumber, page });

    const targetElement = document.getElementById(targetId);
    if (!targetElement) {
        console.error(`Target element with ID ${targetId} not found`);
        return;
    }

    // Only collapse if the section is expanded and we're not paginating
    if (targetElement.classList.contains('expanded') && page === 1) {
        console.log(`Section ${targetId} is already expanded, collapsing instead`);
        collapseSection(targetId);
        return;
    }

    const loadingSuccess = showLoadingExpand(targetId);

    let url;
    if (window.cachedTabNum === 1 || window.cachedTabNum === 5) {
        // For Tabs 1 and 5, fetch subcategories
        url = `/tab/${window.cachedTabNum}/subcat_data?category=${encodeURIComponent(category)}&page=${page}`;
    } else {
        // For Tabs 2 and 4, fetch common names
        url = `/tab/${window.cachedTabNum}/common_names?contract_number=${encodeURIComponent(contractNumber)}&page=${page}`;
    }

    console.log('Fetching data from URL:', url);

    fetch(url)
        .then(response => {
            console.log(`Fetch response status for ${url}: ${response.status}`);
            if (!response.ok) {
                throw new Error(`Fetch failed with status ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Data received:', data);
            if (data.error) {
                console.error('Error fetching data:', data.error);
                targetElement.innerHTML = `<p>Error: ${data.error}</p>`;
                return;
            }

            let html = '';
            if (window.cachedTabNum === 1 || window.cachedTabNum === 5) {
                // Handle Tabs 1 and 5: Load subcategories
                if (data.subcategories && data.subcategories.length > 0) {
                    html = `
                        <select class="subcategory-select form-control" data-category="${category}" onchange="loadCommonNames(this)">
                            <option value="">Select a subcategory</option>
                    `;
                    data.subcategories.forEach(subcat => {
                        const escapedSubcategory = subcat.subcategory.replace(/'/g, "\\'").replace(/"/g, '\\"');
                        html += `<option value="${escapedSubcategory}">${subcat.subcategory}</option>`;
                    });
                    html += '</select>';
                } else {
                    html = `<p>No subcategories found for this category.</p>`;
                    if (data.message) {
                        html += `<p>${data.message}</p>`;
                    }
                }

                // Add pagination for subcategories if applicable
                if (data.total_subcats > data.per_page) {
                    const totalPages = Math.ceil(data.total_subcats / data.per_page);
                    const escapedCategory = category.replace(/'/g, "\\'").replace(/"/g, '\\"');
                    html += `
                        <div class="pagination-controls mt-2">
                            <button class="btn btn-sm btn-secondary" onclick="window.expandCategory('${escapedCategory}', '${targetId}', null, ${data.page - 1})" ${data.page === 1 ? 'disabled' : ''}>Previous</button>
                            <span class="mx-2">Page ${data.page} of ${totalPages}</span>
                            <button class="btn btn-sm btn-secondary" onclick="window.expandCategory('${escapedCategory}', '${targetId}', null, ${data.page + 1})" ${data.page === totalPages ? 'disabled' : ''}>Next</button>
                        </div>
                    `;
                }
            } else {
                // Handle Tabs 2 and 4: Load common names
                const commonNames = data.common_names || [];
                const totalCommonNames = data.total_common_names || 0;
                const perPage = data.per_page || 10;
                const currentPage = data.page || 1;

                html = `
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
                                <button class="btn btn-sm btn-secondary expand-btn" data-common-name="${escapedCommonName}" data-target-id="items-${commonId}" data-contract-number="${contractNumber}">Expand</button>
                                <button class="btn btn-sm btn-secondary collapse-btn" data-collapse-target="items-${commonId}" style="display:none;">Collapse</button>
                                <button class="btn btn-sm btn-info print-btn" data-print-level="Common Name" data-print-id="items-${commonId}" data-common-name="${escapedCommonName}" data-category="${contractNumber}">Print</button>
                                <button class="btn btn-sm btn-info print-full-btn" data-common-name="${escapedCommonName}" data-category="${contractNumber}">Print Full List</button>
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

                // Add pagination controls for common names
                if (totalCommonNames > perPage) {
                    const totalPages = Math.ceil(totalCommonNames / perPage);
                    const escapedCategory = category.replace(/'/g, "\\'").replace(/"/g, '\\"');
                    html += `
                        <div class="pagination-controls mt-2">
                            <button class="btn btn-sm btn-secondary" onclick="window.expandCategory('${escapedCategory}', '${targetId}', '${contractNumber}', ${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>
                            <span class="mx-2">Page ${currentPage} of ${totalPages}</span>
                            <button class="btn btn-sm btn-secondary" onclick="window.expandCategory('${escapedCategory}', '${targetId}', '${contractNumber}', ${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>
                        </div>
                    `;
                }
            }

            targetElement.innerHTML = html;
            targetElement.classList.remove('collapsed');
            targetElement.classList.add('expanded');
            targetElement.style.display = 'block';
            targetElement.style.opacity = '1';

            // Apply global filter if applicable (for Tabs 2 and 4)
            if (window.cachedTabNum === 2 || window.cachedTabNum === 4) {
                const table = targetElement.querySelector('.common-table');
                if (table && typeof applyFilterToTable === 'function') {
                    applyFilterToTable(table);
                }
            }

            // Save expanded state
            sessionStorage.setItem(`expanded_${targetId}`, JSON.stringify({ category, page }));
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            targetElement.innerHTML = `<p>Error loading data: ${error.message}</p>`;
            targetElement.classList.remove('collapsed');
            targetElement.classList.add('expanded');
            targetElement.style.display = 'block';
            targetElement.style.opacity = '1';
        })
        .finally(() => {
            if (loadingSuccess) {
                hideLoadingExpand(targetId);
            }
        });
};

// Sorting state for common names and items tables (Tabs 2 and 4)
let commonSortState = {};
let itemSortState = {};

// Event listener for Tabs 2, 3, 4, Categories, and Home
document.addEventListener('DOMContentLoaded', function() {
    console.log('expand.js: DOMContentLoaded event fired');

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
                // Expand to items level (Tabs 2 and 4)
                console.log('Expanding items for:', { contractNumber, commonName, targetId });
                expandItems(contractNumber, commonName, targetId);
            } else {
                // Expand to common names level (Tabs 2 and 4)
                console.log('Expanding common names for:', { contractNumber, targetId });
                window.expandCategory(category, targetId, contractNumber);
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

    // Format timestamps in the Hand-Counted Items table after HTMX load (Tab 4)
    if (window.cachedTabNum === 4) {
        document.body.addEventListener('htmx:afterSwap', function(event) {
            const target = event.target;
            if (target.id === 'hand-counted-items') {
                const rows = target.querySelectorAll('tr');
                rows.forEach(row => {
                    const timestampCell = row.querySelector('td:nth-child(5)'); // Timestamp column
                    if (timestampCell) {
                        const rawDate = timestampCell.textContent.trim();
                        const formattedDate = formatDate(rawDate);
                        timestampCell.textContent = formattedDate;
                    }
                });
            }
        });
    }

    // Function to expand items under a common name (Tabs 2 and 4)
    window.expandItems = function(contractNumber, commonName, targetId, page = 1) {
        console.log('expandItems called with', { contractNumber, commonName, targetId, page });

        const targetElement = document.getElementById(targetId);
        if (!targetElement) {
            console.error(`Target element with ID ${targetId} not found`);
            return;
        }

        // Only collapse if the section is expanded and we're not paginating
        if (targetElement.classList.contains('expanded') && page === 1) {
            console.log(`Section ${targetId} is already expanded, collapsing instead`);
            collapseSection(targetId);
            return;
        }

        const commonId = targetId.replace('items-', '');
        const loadingSuccess = showLoadingExpand(commonId);
        targetElement.innerHTML = ''; // Clear previous content

        let url = `/tab/${window.cachedTabNum}/data?contract_number=${encodeURIComponent(contractNumber)}&common_name=${encodeURIComponent(commonName)}&page=${page}`;
        fetch(url)
            .then(response => {
                console.log(`Fetch response status for ${url}: ${response.status}`);
                if (!response.ok) {
                    throw new Error(`Items fetch failed with status ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Items data received:', data);
                if (data.error) {
                    console.error('Error fetching items:', data.error);
                    targetElement.innerHTML = `<p>Error: ${data.error}</p>`;
                    return;
                }

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

                html += `
                            </tbody>
                        </table>
                    </div>
                `;

                // Add pagination controls for items
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
                targetElement.style.display = 'block';
                targetElement.style.opacity = '1';

                // Apply global filter to the newly loaded table
                const table = targetElement.querySelector('.item-table');
                if (table && typeof applyFilterToTable === 'function') {
                    applyFilterToTable(table);
                }

                // Save expanded state
                sessionStorage.setItem(`expanded_items_${targetId}`, JSON.stringify({ contractNumber, commonName, page }));
            })
            .catch(error => {
                console.error('Error fetching items:', error);
                targetElement.innerHTML = `<p>Error loading items: ${error.message}</p>`;
                targetElement.classList.remove('collapsed');
                targetElement.classList.add('expanded');
                targetElement.style.display = 'block';
                targetElement.style.opacity = '1';
            })
            .finally(() => {
                if (loadingSuccess) {
                    hideLoadingExpand(commonId);
                }
            });
    };

    // Function to sort common names table (Tabs 2 and 4)
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
        let url = `/tab/${window.cachedTabNum}/common_names?contract_number=${encodeURIComponent(contractNumber)}&sort=${column}_${direction}`;
        fetch(url)
            .then(response => {
                console.log(`Fetch response status for ${url}: ${response.status}`);
                if (!response.ok) {
                    throw new Error(`Common names sort fetch failed with status ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Sorted common names data received:', data);
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
                                <button class="btn btn-sm btn-secondary expand-btn" data-common-name="${escapedCommonName}" data-target-id="items-${commonId}" data-contract-number="${contractNumber}">Expand</button>
                                <button class="btn btn-sm btn-secondary collapse-btn" data-collapse-target="items-${commonId}" style="display:none;">Collapse</button>
                                <button class="btn btn-sm btn-info print-btn" data-print-level="Common Name" data-print-id="items-${commonId}" data-common-name="${escapedCommonName}" data-category="${contractNumber}">Print</button>
                                <button class="btn btn-sm btn-info print-full-btn" data-common-name="${escapedCommonName}" data-category="${contractNumber}">Print Full List</button>
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
                if (table && typeof applyFilterToTable === 'function') {
                    applyFilterToTable(table);
                }
            })
            .catch(error => {
                console.error('Error sorting common names:', error);
            });
    }

    // Function to sort items table (Tabs 2 and 4)
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
        let url = `/tab/${window.cachedTabNum}/data?contract_number=${encodeURIComponent(contractNumber)}&common_name=${encodeURIComponent(commonName)}&sort=${column}_${direction}`;
        fetch(url)
            .then(response => {
                console.log(`Fetch response status for ${url}: ${response.status}`);
                if (!response.ok) {
                    throw new Error(`Items sort fetch failed with status ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Sorted items data received:', data);
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
                if (table && typeof applyFilterToTable === 'function') {
                    applyFilterToTable(table);
                }
            })
            .catch(error => {
                console.error('Error sorting items:', error);
            });
    }
});