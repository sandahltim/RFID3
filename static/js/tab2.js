import { formatDate } from './utils.js';
import { getCachedTabNum, setCachedTabNum } from './state.js';
console.log('tab2.js version: 2025-05-29-v10 loaded');

/**
 * Tab2.js: Logic for Tab 2 (Open Contracts).
 * Dependencies: common.js (for formatDate, showLoading, hideLoading, collapseSection, applyFilterToTable, sortCommonNames, sortItems).
 * Updated: Fixed sorting for top layer only, added font and title styling, debounced sort clicks.
 */

let sortTimeout;

window.sortContracts = function(column) {
    if (sortTimeout) clearTimeout(sortTimeout); // Debounce
    sortTimeout = setTimeout(() => {
        let currentSort = sessionStorage.getItem('tab2Sort') || 'contract_number_asc';
        let [currentColumn, currentDirection] = currentSort.split('_');
        let direction = (currentColumn === column && currentDirection === 'asc') ? 'desc' : 'asc';
        let sort = `${column}_${direction}`;

        fetch(`/tab/2/sort_contracts?sort=${sort}`)
            .then(response => {
                if (!response.ok) throw new Error('Failed to fetch sorted contracts');
                return response.json();
            })
            .then(data => {
                if (data.error) throw new Error(data.error);
                sessionStorage.setItem('tab2Sort', sort);
                renderContracts(data.contracts);
                updateSortArrows(sort);
            })
            .catch(error => console.error('Sort error:', error));
    }, 300); // 300ms debounce
};

function renderContracts(contracts) {
    const tbody = document.getElementById('category-rows');
    if (!tbody) return;

    tbody.innerHTML = '';
    contracts.forEach(contract => {
        const sanitizedContractNumber = contract.contract_number.replace(/[^a-z0-9]/gi, '_');
        const sanitizedId = `common-${sanitizedContractNumber}`;
        const rowClass = contract.is_stale ? 'stale-contract' : '';
        const bulkControls = contract.is_stale ? `
                <select id="bulk-status-${sanitizedContractNumber}" class="form-control form-control-sm d-inline-block w-auto">
                    <option value="">Status</option>
                    <option value="Ready to Rent">Ready to Rent</option>
                    <option value="Sold">Sold</option>
                    <option value="Repair">Repair</option>
                    <option value="Needs to be Inspected">Needs to be Inspected</option>
                    <option value="Wash">Wash</option>
                    <option value="Wet">Wet</option>
                </select>
                <button class="btn btn-sm btn-warning" onclick="window.updateContractStatus('${contract.contract_number}', '${sanitizedContractNumber}')">Update All</button>
        ` : '';

        let html = `
            <tr class="${rowClass}">
                <td>${contract.contract_number}</td>
                <td>${contract.client_name}</td>
                <td>${contract.items_on_contract}</td>
                <td>${contract.total_items_inventory}</td>
                <td>${contract.scan_date}</td>
                <td>
                    <button class="btn btn-sm btn-secondary expand-btn" data-target-id="${sanitizedId}" data-contract-number="${contract.contract_number}">Expand</button>
                    <button class="btn btn-sm btn-secondary collapse-btn" data-collapse-target="${sanitizedId}" style="display:none;">Collapse</button>
                    <button class="btn btn-sm btn-info print-btn" data-print-level="Contract" data-print-id="${sanitizedId}" data-category="${contract.contract_number}">Print</button>
                    ${bulkControls}
                    <div id="loading-${sanitizedId}" style="display:none;" class="loading-indicator">Loading...</div>
                </td>
            </tr>
            <tr>
                <td colspan="6">
                    <div id="${sanitizedId}" class="expandable collapsed subcategory-container"></div>
                </td>
            </tr>
        `;
        tbody.innerHTML += html;
    });

    // Reformat timestamps
    const contractRows = tbody.querySelectorAll('tr:not(.expandable)');
    contractRows.forEach(row => {
        const timestampCell = row.querySelector('td:nth-child(5)');
        if (timestampCell) {
            const rawDate = timestampCell.textContent.trim();
            const formattedDate = formatDate(rawDate);
            timestampCell.textContent = formattedDate;
        }
    });
}

function updateSortArrows(currentSort) {
    const headers = document.querySelectorAll('#category-table thead th');
    const [currentColumn, currentDirection] = (currentSort || 'contract_number_asc').split('_');

    headers.forEach(header => {
        const column = header.getAttribute('onclick')?.match(/'(\w+)'/)?.[1];
        const sortArrow = header.querySelector('.sort-arrow') || document.createElement('span');
        sortArrow.className = 'sort-arrow';
        if (!header.querySelector('.sort-arrow')) header.appendChild(sortArrow);

        if (column === currentColumn) {
            sortArrow.textContent = currentDirection === 'asc' ? '↑' : '↓';
        } else {
            sortArrow.textContent = '';
        }
    });
}

// Expand category for Tab 2
window.expandCategory = function(category, targetId, contractNumber, page = 1, tabNum = 2) {
    console.log('expandCategory:', { category, targetId, contractNumber, page, tabNum });

    const targetElement = document.getElementById(targetId);
    if (!targetElement) {
        console.error(`Target ${targetId} not found`);
        return;
    }

    const parentRow = targetElement.closest('tr').previousElementSibling;
    const expandBtn = parentRow.querySelector('.expand-btn');
    const collapseBtn = parentRow.querySelector('.collapse-btn');

    if (targetElement.classList.contains('expanded') && page === 1) {
        console.log(`Collapsing ${targetId}`);
        collapseSection(targetId);
        if (expandBtn && collapseBtn) {
            expandBtn.style.display = 'inline-block';
            collapseBtn.style.display = 'none';
        }
        return;
    }

    const loadingSuccess = showLoading(targetId);
    const sanitizedContractNumber = contractNumber.trim().replace(/[^a-z0-9]/g, '_').substring(0, 50);
    const url = `/tab/2/common_names?contract_number=${encodeURIComponent(sanitizedContractNumber)}&page=${page}`;
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
            if (data.error) {
                console.error('Common names error:', data.error);
                targetElement.innerHTML = `<p>Error: ${data.error}</p>`;
                return;
            }

            const commonNames = data.common_names || [];
            const totalCommonNames = data.total_common_names || 0;
            const perPage = data.per_page || 10;
            const currentPage = data.page || 1;

            let html = `
                <div class="subcategory-container">
                    <table class="table table-bordered table-hover common-table">
                        <thead class="thead-dark">
                            <tr>
                                <th onclick="window.sortCommonNames('${sanitizedContractNumber}', 'common_name', 2)">Common Name <span class="sort-arrow"></span></th>
                                <th onclick="window.sortCommonNames('${sanitizedContractNumber}', 'on_contracts', 2)">Items on Contract <span class="sort-arrow"></span></th>
                                <th onclick="window.sortCommonNames('${sanitizedContractNumber}', 'total_items_inventory', 2)">Total Items in Inventory <span class="sort-arrow"></span></th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            commonNames.forEach(common => {
                const commonId = `${sanitizedContractNumber}-${common.name.replace(/[^a-z0-9]/g, '_').substring(0, 50)}`;
                const escapedCommonName = common.name.replace(/'/g, "\\'").replace(/"/g, '\\"');
                html += `
                    <tr>
                        <td class="expandable-cell" onclick="window.expandItems('${sanitizedContractNumber}', '${escapedCommonName}', 'items-${commonId}', 1, 2)">${common.name}</td>
                        <td>${common.on_contracts}</td>
                        <td>${common.is_hand_counted ? 'N/A' : common.total_items_inventory}</td>
                        <td>
                            <button class="btn btn-sm btn-secondary expand-btn" data-common-name="${escapedCommonName}" data-target-id="items-${commonId}" data-contract-number="${sanitizedContractNumber}">Expand</button>
                            <button class="btn btn-sm btn-secondary collapse-btn" data-collapse-target="items-${commonId}" style="display:none;">Collapse</button>
                            <button class="btn btn-sm btn-info print-btn" data-print-level="Common Name" data-print-id="items-${commonId}" data-common-name="${escapedCommonName}" data-category="${sanitizedContractNumber}">Print</button>
                            <button class="btn btn-sm btn-info print-full-btn" data-common-name="${escapedCommonName}" data-category="${sanitizedContractNumber}">Print Full List</button>
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
                const escapedCategory = category ? category.replace(/'/g, "\\'").replace(/"/g, '\\"') : '';
                html += `
                    <div class="pagination-controls mt-2">
                        <button class="btn btn-sm btn-secondary" onclick="window.expandCategory('${escapedCategory}', '${targetId}', '${sanitizedContractNumber}', ${currentPage - 1}, 2)" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>
                        <span class="mx-2">Page ${currentPage} of ${totalPages}</span>
                        <button class="btn btn-sm btn-secondary" onclick="window.expandCategory('${escapedCategory}', '${targetId}', '${sanitizedContractNumber}', ${currentPage + 1}, 2)" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>
                    </div>
                `;
            }

            targetElement.innerHTML = html;
            targetElement.classList.remove('collapsed');
            targetElement.classList.add('expanded');
            targetElement.style.display = 'block';
            targetElement.style.opacity = '1';
            targetElement.style.visibility = 'visible';

            if (expandBtn && collapseBtn) {
                expandBtn.style.display = 'none';
                collapseBtn.style.display = 'inline-block';
            }

            console.log('Common names container styles:', {
                classList: targetElement.classList.toString(),
                display: targetElement.style.display,
                opacity: targetElement.style.opacity,
                visibility: window.getComputedStyle(targetElement).visibility
            });

            const table = targetElement.querySelector('.common-table');
            if (table) {
                applyFilterToTable(table);
            }

            sessionStorage.setItem(`expanded_${targetId}`, JSON.stringify({ category, page }));
        })
        .catch(error => {
            console.error('Common names error:', error.message);
            targetElement.innerHTML = `<p>Error: ${error.message}</p>`;
            targetElement.classList.remove('collapsed');
            targetElement.classList.add('expanded');
            targetElement.style.display = 'block';
            targetElement.style.opacity = '1';
            targetElement.style.visibility = 'visible';
        })
        .finally(() => {
            if (loadingSuccess) hideLoading(targetId);
        });
};

// Expand items for Tab 2
window.expandItems = function(contractNumber, commonName, targetId, page = 1, tabNum = 2) {
    console.log('expandItems:', { contractNumber, commonName, targetId, page, tabNum });

    const targetElement = document.getElementById(targetId);
    if (!targetElement) {
        console.error(`Target ${targetId} not found`);
        return;
    }

    const parentRow = targetElement.closest('tr').previousElementSibling;
    const expandBtn = parentRow.querySelector('.expand-btn');
    const collapseBtn = parentRow.querySelector('.collapse-btn');

    if (targetElement.classList.contains('expanded') && page === 1) {
        console.log(`Collapsing ${targetId}`);
        collapseSection(targetId);
        if (expandBtn && collapseBtn) {
            expandBtn.style.display = 'inline-block';
            collapseBtn.style.display = 'none';
        }
        return;
    }

    const commonId = targetId.replace('items-', '');
    const loadingSuccess = showLoading(`loading-items-${commonId}`);
    targetElement.innerHTML = '';

    const sanitizedContractNumber = contractNumber.trim().replace(/[^a-z0-9]/g, '_').substring(0, 50);
    const url = `/tab/2/data?contract_number=${encodeURIComponent(sanitizedContractNumber)}&common_name=${encodeURIComponent(commonName)}&page=${page}`;
    const escapedCommonName = commonName.replace(/'/g, "\\'").replace(/"/g, '\\"');
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
            if (data.error) {
                console.error('Items error:', data.error);
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
                                <th onclick="window.sortItems('${sanitizedContractNumber}', '${commonName}', 'tag_id', 2)">Tag ID <span class="sort-arrow"></span></th>
                                <th onclick="window.sortItems('${sanitizedContractNumber}', '${commonName}', 'common_name', 2)">Common Name <span class="sort-arrow"></span></th>
                                <th onclick="window.sortItems('${sanitizedContractNumber}', '${commonName}', 'bin_location', 2)">Bin Location <span class="sort-arrow"></span></th>
                                <th onclick="window.sortItems('${sanitizedContractNumber}', '${commonName}', 'status', 2)">Status <span class="sort-arrow"></span></th>
                                <th onclick="window.sortItems('${sanitizedContractNumber}', '${commonName}', 'last_contract_num', 2)">Last Contract <span class="sort-arrow"></span></th>
                                <th onclick="window.sortItems('${sanitizedContractNumber}', '${commonName}', 'last_scanned_date', 2)">Last Scanned Date <span class="sort-arrow"></span></th>
                                <th>Actions</th>
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
                        <td>
                            <select id="status-${item.tag_id}" class="form-control form-control-sm d-inline-block w-auto">
                                <option value="">Status</option>
                                <option value="Ready to Rent">Ready to Rent</option>
                                <option value="Sold">Sold</option>
                                <option value="Repair">Repair</option>
                                <option value="Needs to be Inspected">Needs to be Inspected</option>
                                <option value="Wash">Wash</option>
                                <option value="Wet">Wet</option>
                            </select>
                            <button class="btn btn-sm btn-primary ml-1" onclick="window.updateItemStatus('${item.tag_id}', '${sanitizedContractNumber}', '${escapedCommonName}', '${targetId}', ${currentPage})">Update</button>
                        </td>
                    </tr>
                `;
            });

            html += `</tbody></table></div>`;

            if (totalItems > perPage) {
                const totalPages = Math.ceil(totalItems / perPage);
                const escapedCommonName = commonName.replace(/'/g, "\\'").replace(/"/g, '\\"');
                html += `
                    <div class="pagination-controls mt-2 ml-4">
                        <button class="btn btn-sm btn-secondary" onclick="window.expandItems('${sanitizedContractNumber}', '${escapedCommonName}', '${targetId}', ${currentPage - 1}, 2)" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>
                        <span class="mx-2">Page ${currentPage} of ${totalPages}</span>
                        <button class="btn btn-sm btn-secondary" onclick="window.expandItems('${sanitizedContractNumber}', '${escapedCommonName}', '${targetId}', ${currentPage + 1}, 2)" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>
                    </div>
                `;
            }

            targetElement.innerHTML = html;
            targetElement.classList.remove('collapsed');
            targetElement.classList.add('expanded');
            targetElement.style.display = 'block';
            targetElement.style.opacity = '1';
            targetElement.style.visibility = 'visible';

            if (expandBtn && collapseBtn) {
                expandBtn.style.display = 'none';
                collapseBtn.style.display = 'inline-block';
            }

            console.log('Items container styles:', {
                classList: targetElement.classList.toString(),
                display: targetElement.style.display,
                opacity: targetElement.style.opacity,
                visibility: window.getComputedStyle(targetElement).visibility
            });

            const table = targetElement.querySelector('.item-table');
            if (table) {
                applyFilterToTable(table);
            }

            sessionStorage.setItem(`expanded_items_${targetId}`, JSON.stringify({ contractNumber: sanitizedContractNumber, commonName, page }));
        })
        .catch(error => {
            console.error('Items error:', error.message);
            targetElement.innerHTML = `<p>Error: ${error.message}</p>`;
            targetElement.classList.remove('collapsed');
            targetElement.classList.add('expanded');
            targetElement.style.display = 'block';
            targetElement.style.opacity = '1';
            targetElement.style.visibility = 'visible';
        })
        .finally(() => {
            if (loadingSuccess) hideLoading(`loading-items-${commonId}`);
        });
};

window.updateItemStatus = function(tagId, contractNumber, commonName, targetId, page = 1) {
    const statusSelect = document.getElementById(`status-${tagId}`);
    const status = statusSelect ? statusSelect.value : '';
    if (!status) {
        alert('Select a status.');
        return;
    }

    fetch('/tab/2/update_status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tag_id: tagId, status })
    })
        .then(response => {
            if (!response.ok) {
                return response.text().then(text => { throw new Error(text || 'Failed to update status'); });
            }
            return response.json();
        })
        .then(data => {
            if (data.error) throw new Error(data.error);
            window.expandItems(contractNumber, commonName, targetId, page, 2);
        })
        .catch(error => {
            console.error('Status update error:', error.message);
            alert('Error: ' + error.message);
        });
};

window.updateContractStatus = function(contractNumber, sanitizedContractNumber) {
    const select = document.getElementById(`bulk-status-${sanitizedContractNumber}`);
    const status = select ? select.value : '';
    if (!status) {
        alert('Select a status.');
        return;
    }

    fetch('/tab/2/bulk_update_status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ contract_number: contractNumber, status })
    })
        .then(response => {
            if (!response.ok) {
                return response.text().then(text => { throw new Error(text || 'Failed to bulk update'); });
            }
            return response.json();
        })
        .then(data => {
            if (data.error) throw new Error(data.error);
            alert('Bulk update successful!');
            window.location.reload();
        })
        .catch(error => {
            console.error('Bulk update error:', error.message);
            alert('Error: ' + error.message);
        });
};

// Load global filter from sessionStorage on page load and format timestamps
document.addEventListener('DOMContentLoaded', function() {
    // Set cached tab number if needed
    if (!getCachedTabNum()) {
        const pathMatch = window.location.pathname.match(/\/tab\/(\d+)/);
        setCachedTabNum(pathMatch ? parseInt(pathMatch[1], 10) : (window.location.pathname === '/' ? 1 : null));
        console.log('tab2.js: Set cachedTabNum:', getCachedTabNum());
    } else {
        console.log('tab2.js: cachedTabNum already set:', getCachedTabNum());
    }

    if (getCachedTabNum() !== 2) {
        console.log(`Tab ${getCachedTabNum()} detected, skipping tab2.js`);
        return;
    }

    // Format timestamps in the contract table
    const contractRows = document.querySelectorAll('#category-rows tr:not(.expandable)');
    contractRows.forEach(row => {
        const timestampCell = row.querySelector('td:nth-child(5)'); // Last Scanned Date column
        if (timestampCell) {
            const rawDate = timestampCell.textContent.trim();
            const formattedDate = formatDate(rawDate);
            timestampCell.textContent = formattedDate;
        }
    });

    // Update sort arrows on load
    updateSortArrows(sessionStorage.getItem('tab2Sort'));

    // Clean up outdated sessionStorage keys
    Object.keys(sessionStorage).forEach(key => {
        if (key.startsWith('expanded_') || key.startsWith('expanded_common_') || key.startsWith('expanded_items_')) {
            try {
                const state = JSON.parse(sessionStorage.getItem(key));
                const targetId = key.replace(/^(expanded_|expanded_common_|expanded_items_)/, '');
                if (!document.getElementById(targetId) && !document.getElementById(`common-${targetId}`) && !document.getElementById(`items-${targetId}`)) {
                    console.log(`Removing outdated sessionStorage: ${key}`);
                    sessionStorage.removeItem(key);
                }
            } catch (e) {
                console.error('Error parsing sessionStorage:', key, e.message);
                sessionStorage.removeItem(key);
            }
        }
    });

    // Attach event listeners
    document.removeEventListener('click', handleClick);
    console.log('Attaching click event listener');
    document.addEventListener('click', handleClick);

    function handleClick(event) {
        const expandBtn = event.target.closest('.expand-btn');
        if (expandBtn) {
            event.stopPropagation();
            console.log('Expand button clicked:', {
                category: expandBtn.getAttribute('data-category'),
                commonName: expandBtn.getAttribute('data-common-name'),
                targetId: expandBtn.getAttribute('data-target-id'),
                contractNumber: expandBtn.getAttribute('data-contract-number')
            });

            const category = expandBtn.getAttribute('data-category');
            const commonName = expandBtn.getAttribute('data-common-name');
            const targetId = expandBtn.getAttribute('data-target-id');
            const contractNumber = expandBtn.getAttribute('data-contract-number');

            if (commonName) {
                console.log(`Expanding items for ${contractNumber}, ${commonName}`);
                window.expandItems(contractNumber, commonName, targetId, 1, 2);
            } else if (contractNumber && getCachedTabNum() === 2) {
                console.log(`Expanding category for ${contractNumber}`);
                window.expandCategory(category, targetId, contractNumber, 1, 2);
            }
            return;
        }

        const collapseBtn = event.target.closest('.collapse-btn');
        if (collapseBtn) {
            event.stopPropagation();
            console.log(`Collapsing ${collapseBtn.getAttribute('data-collapse-target')}`);
            collapseSection(collapseBtn.getAttribute('data-collapse-target'));
            const parentRow = document.querySelector(`[data-target-id="${collapseBtn.getAttribute('data-collapse-target')}"]`)?.closest('tr');
            if (parentRow) {
                const expandBtn = parentRow.querySelector('.expand-btn');
                const collapseBtn = parentRow.querySelector('.collapse-btn');
                if (expandBtn && collapseBtn) {
                    expandBtn.style.display = 'inline-block';
                    collapseBtn.style.display = 'none';
                }
            }
            return;
        }

        const printBtn = event.target.closest('.print-btn');
        if (printBtn) {
            event.preventDefault();
            event.stopPropagation();
            const level = printBtn.getAttribute('data-print-level');
            const id = printBtn.getAttribute('data-print-id');
            const commonName = printBtn.getAttribute('data-common-name');
            const category = printBtn.getAttribute('data-category');
            const subcategory = printBtn.getAttribute('data-subcategory');
            printTable(level, id, commonName, category, subcategory);
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