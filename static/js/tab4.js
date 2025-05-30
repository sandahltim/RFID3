console.log('tab4.js version: 2025-05-29-v4 loaded');

/**
 * Tab4.js: Logic for Tab 4 (Laundry Contracts).
 * Dependencies: common.js (for formatDate, showLoading, hideLoading, collapseSection, applyFilterToTable, sortCommonNames, sortItems).
 * Updated: Removed duplicate functions, now using common.js utilities.
 */

// Expand category for Tab 4
window.expandCategory = function(category, targetId, contractNumber, page = 1, tabNum = 4) {
    console.log('expandCategory:', { category, targetId, contractNumber, page, tabNum });

    const targetElement = document.getElementById(targetId);
    if (!targetElement) {
        console.error(`Target ${targetId} not found`);
        return;
    }

    const loadingSuccess = showLoading(targetId);
    const url = `/tab/4/common_names?contract_number=${encodeURIComponent(contractNumber)}&page=${page}`;
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
                                <th onclick="window.sortCommonNames('${contractNumber}', 'common_name', 4)">Common Name <span class="sort-arrow"></span></th>
                                <th onclick="window.sortCommonNames('${contractNumber}', 'on_contracts', 4)">Items on Contract <span class="sort-arrow"></span></th>
                                <th onclick="window.sortCommonNames('${contractNumber}', 'total_items_inventory', 4)">Total Items in Inventory <span class="sort-arrow"></span></th>
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
                        <td class="expandable-cell" onclick="window.expandItems('${contractNumber}', '${escapedCommonName}', 'items-${commonId}', 1, 4)">${common.name}</td>
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
                const escapedCategory = category ? category.replace(/'/g, "\\'").replace(/"/g, '\\"') : '';
                html += `
                    <div class="pagination-controls mt-2">
                        <button class="btn btn-sm btn-secondary" onclick="window.expandCategory('${escapedCategory}', '${targetId}', '${contractNumber}', ${currentPage - 1}, 4)" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>
                        <span class="mx-2">Page ${currentPage} of ${totalPages}</span>
                        <button class="btn btn-sm btn-secondary" onclick="window.expandCategory('${escapedCategory}', '${targetId}', '${contractNumber}', ${currentPage + 1}, 4)" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>
                    </div>
                `;
            }

            targetElement.innerHTML = html;
            targetElement.classList.remove('collapsed');
            targetElement.classList.add('expanded');
            targetElement.style.display = 'block';
            targetElement.style.opacity = '1';
            targetElement.style.visibility = 'visible';

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

// Expand items for Tab 4
window.expandItems = function(contractNumber, commonName, targetId, page = 1, tabNum = 4) {
    console.log('expandItems:', { contractNumber, commonName, targetId, page, tabNum });

    const targetElement = document.getElementById(targetId);
    if (!targetElement) {
        console.error(`Target ${targetId} not found`);
        return;
    }

    if (targetElement.classList.contains('expanded') && page === 1) {
        console.log(`Collapsing ${targetId}`);
        collapseSection(targetId);
        return;
    }

    const commonId = targetId.replace('items-', '');
    const loadingSuccess = showLoading(`loading-items-${commonId}`);
    targetElement.innerHTML = '';

    const url = `/tab/4/data?contract_number=${encodeURIComponent(contractNumber)}&common_name=${encodeURIComponent(commonName)}&page=${page}`;
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
                                <th onclick="window.sortItems('${contractNumber}', '${commonName}', 'tag_id', 4)">Tag ID <span class="sort-arrow"></span></th>
                                <th onclick="window.sortItems('${contractNumber}', '${commonName}', 'common_name', 4)">Common Name <span class="sort-arrow"></span></th>
                                <th onclick="window.sortItems('${contractNumber}', '${commonName}', 'bin_location', 4)">Bin Location <span class="sort-arrow"></span></th>
                                <th onclick="window.sortItems('${contractNumber}', '${commonName}', 'status', 4)">Status <span class="sort-arrow"></span></th>
                                <th onclick="window.sortItems('${contractNumber}', '${commonName}', 'last_contract_num', 4)">Last Contract <span class="sort-arrow"></span></th>
                                <th onclick="window.sortItems('${contractNumber}', '${commonName}', 'last_scanned_date', 4)">Last Scanned Date <span class="sort-arrow"></span></th>
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
                        <button class="btn btn-sm btn-secondary" onclick="window.expandItems('${contractNumber}', '${escapedCommonName}', '${targetId}', ${currentPage - 1}, 4)" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>
                        <span class="mx-2">Page ${currentPage} of ${totalPages}</span>
                        <button class="btn btn-sm btn-secondary" onclick="window.expandItems('${contractNumber}', '${escapedCommonName}', '${targetId}', ${currentPage + 1}, 4)" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>
                    </div>
                `;
            }

            targetElement.innerHTML = html;
            targetElement.classList.remove('collapsed');
            targetElement.classList.add('expanded');
            targetElement.style.display = 'block';
            targetElement.style.opacity = '1';
            targetElement.style.visibility = 'visible';

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

            sessionStorage.setItem(`expanded_items_${targetId}`, JSON.stringify({ contractNumber, commonName, page }));
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

// Load global filter from sessionStorage on page load
document.addEventListener('DOMContentLoaded', function() {
    // Set window.cachedTabNum
    if (!window.cachedTabNum) {
        const pathMatch = window.location.pathname.match(/\/tab\/(\d+)/);
        window.cachedTabNum = pathMatch ? parseInt(pathMatch[1], 10) : (window.location.pathname === '/' ? 1 : null);
        console.log('tab4.js: Set window.cachedTabNum:', window.cachedTabNum);
    } else {
        console.log('tab4.js: window.cachedTabNum already set:', window.cachedTabNum);
    }

    if (window.cachedTabNum !== 4) {
        console.log(`Tab ${window.cachedTabNum} detected, skipping tab4.js`);
        return;
    }

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
                window.expandItems(contractNumber, commonName, targetId, 1, 4);
            }
            return;
        }

        const collapseBtn = event.target.closest('.collapse-btn');
        if (collapseBtn) {
            event.stopPropagation();
            console.log(`Collapsing ${collapseBtn.getAttribute('data-collapse-target')}`);
            collapseSection(collapseBtn.getAttribute('data-collapse-target'));
            return;
        }
    }

    // HTMX event listener for hand-counted items
    document.body.addEventListener('htmx:afterSwap', function(event) {
        const target = event.target;
        if (target.id === 'hand-counted-items') {
            const rows = target.querySelectorAll('tr');
            rows.forEach(row => {
                const timestampCell = row.querySelector('td:nth-child(5)');
                if (timestampCell) {
                    const rawDate = timestampCell.textContent.trim();
                    const formattedDate = formatDate(rawDate);
                    timestampCell.textContent = formattedDate;
                }
            });
        }
    });
});
function formatDate(isoDateString) {
    if (!isoDateString || isoDateString === 'N/A') return 'N/A';
    try {
        const date = new Date(isoDateString);
        if (isNaN(date.getTime())) return isoDateString;
        const days = ['Sun', 'Mon', 'Tues', 'Wed', 'Thurs', 'Fri', 'Sat'];
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec'];
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
        console.error('Error formatting date:', error);
        return isoDateString;
    }
}

function refreshTab() {
    window.location.reload();
}

function filterHandCountedItems() {
    const contractNumber = document.getElementById('hand-counted-filter').value;
    const url = contractNumber ? `/tab/4/hand_counted_items?contract_number=${encodeURIComponent(contractNumber)}` : '/tab/4/hand_counted_items';
    if (typeof htmx !== 'undefined') {
        htmx.ajax('GET', url, '#hand-counted-items');
    } else {
        console.warn('HTMX not available, using fallback fetch');
        fetch(url)
            .then(response => response.text())
            .then(html => {
                const target = document.getElementById('hand-counted-items');
                if (target) {
                    target.innerHTML = html;
                    const rows = target.querySelectorAll('tr');
                    rows.forEach(row => {
                        const timestampCell = row.querySelector('td:nth-child(5)');
                        if (timestampCell) {
                            const rawDate = timestampCell.textContent.trim();
                            timestampCell.textContent = formatDate(rawDate);
                        }
                    });
                }
            })
            .catch(error => {
                console.error('Error fetching hand-counted items:', error);
                document.getElementById('hand-counted-items').innerHTML = '<tr><td colspan="6">Error loading hand-counted items.</td></tr>';
            });
    }
}

function toggleNewContractInput() {
    const contractDropdown = document.getElementById('hand-counted-contract-number');
    const newContractInput = document.getElementById('new-contract-number');
    if (newContractInput.style.display === 'none') {
        newContractInput.style.display = 'block';
        contractDropdown.disabled = true;
    } else {
        newContractInput.style.display = 'none';
        newContractInput.value = '';
        contractDropdown.disabled = false;
        updateItemDropdown();
    }
}

function toggleNewItemInput() {
    const itemDropdown = document.getElementById('hand-counted-item-name');
    const newItemInput = document.getElementById('new-item-name');
    if (newItemInput.style.display === 'none') {
        newItemInput.style.display = 'block';
        itemDropdown.disabled = true;
    } else {
        newItemInput.style.display = 'none';
        newItemInput.value = '';
        itemDropdown.disabled = false;
    }
}

function updateItemDropdown() {
    const contractDropdown = document.getElementById('hand-counted-contract-number');
    const itemDropdown = document.getElementById('hand-counted-item-name');
    const newContractInput = document.getElementById('new-contract-number');
    const contractNumber = newContractInput.style.display === 'block' ? newContractInput.value : contractDropdown.value;
    itemDropdown.innerHTML = '<option value="">Select Item...</option>';
    if (contractNumber) {
        fetch(`/tab/4/hand_counted_items_by_contract?contract_number=${encodeURIComponent(contractNumber)}`)
            .then(response => response.json())
            .then(data => {
                data.items.forEach(item => {
                    const option = document.createElement('option');
                    option.value = item.item_name;
                    option.textContent = `${item.item_name} (Qty: ${item.quantity})`;
                    itemDropdown.appendChild(option);
                });
            })
            .catch(error => console.error('Error fetching hand-counted items:', error));
    }
}

function addHandCountedItem() {
    const contractDropdown = document.getElementById('hand-counted-contract-number');
    const newContractInput = document.getElementById('new-contract-number');
    const itemDropdown = document.getElementById('hand-counted-item-name');
    const newItemInput = document.getElementById('new-item-name');
    const quantityInput = document.getElementById('hand-counted-quantity');
    const employeeInput = document.getElementById('hand-counted-employee');
    const contractNumber = newContractInput.style.display === 'block' ? newContractInput.value : contractDropdown.value;
    const itemName = newItemInput.style.display === 'block' ? newItemInput.value : itemDropdown.value;
    const quantity = parseInt(quantityInput.value);
    const employeeName = employeeInput.value;
    if (!contractNumber || !itemName || !quantity || quantity < 1 || !employeeName) {
        alert('Please fill in all fields: Contract Number, Item Name, Quantity (positive number), and Employee Name.');
        return;
    }
    if (!contractNumber.startsWith('L')) {
        alert('Contract Number must start with "L" for Laundry Contracts.');
        return;
    }
    fetch('/tab/4/add_hand_counted_item', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            contract_number: contractNumber,
            item_name: itemName,
            quantity: quantity,
            action: 'Added',
            employee_name: employeeName
        })
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            alert(data.message);
            if (newContractInput.style.display === 'block') toggleNewContractInput();
            if (newItemInput.style.display === 'block') toggleNewItemInput();
            contractDropdown.value = '';
            itemDropdown.value = '';
            quantityInput.value = '';
            employeeInput.value = '';
            filterHandCountedItems();
            addContractToTable(contractNumber);
            updateContractCounts(contractNumber);
            refreshCommonNames(contractNumber);
        }
    })
    .catch(error => {
        console.error('Error adding hand-counted item:', error);
        alert('Failed to add item. Please try again.');
        addContractToTable(contractNumber);
        updateContractCounts(contractNumber);
        refreshCommonNames(contractNumber);
    });
}

function removeHandCountedItem() {
    const contractDropdown = document.getElementById('hand-counted-contract-number');
    const newContractInput = document.getElementById('new-contract-number');
    const itemDropdown = document.getElementById('hand-counted-item-name');
    const newItemInput = document.getElementById('new-item-name');
    const quantityInput = document.getElementById('hand-counted-quantity');
    const employeeInput = document.getElementById('hand-counted-employee');
    const contractNumber = newContractInput.style.display === 'block' ? newContractInput.value : contractDropdown.value;
    const itemName = newItemInput.style.display === 'block' ? newItemInput.value : itemDropdown.value;
    const quantity = parseInt(quantityInput.value);
    const employeeName = employeeInput.value;
    if (!contractNumber || !itemName || !quantity || quantity < 1 || !employeeName) {
        alert('Please fill in all fields: Contract Number, Item Name, Quantity (positive number), and Employee Name.');
        return;
    }
    fetch('/tab/4/remove_hand_counted_item', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            contract_number: contractNumber,
            item_name: itemName,
            quantity: quantity,
            action: 'Removed',
            employee_name: employeeName
        })
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            alert(data.message);
            if (newContractInput.style.display === 'block') toggleNewContractInput();
            if (newItemInput.style.display === 'block') toggleNewItemInput();
            contractDropdown.value = '';
            itemDropdown.value = '';
            quantityInput.value = '';
            employeeInput.value = '';
            filterHandCountedItems();
            addContractToTable(contractNumber);
            updateContractCounts(contractNumber);
            refreshCommonNames(contractNumber);
        }
    })
    .catch(error => {
        console.error('Error removing hand-counted item:', error);
        alert('Failed to remove item. Please try again.');
        addContractToTable(contractNumber);
        updateContractCounts(contractNumber);
        refreshCommonNames(contractNumber);
    });
}

function addContractToTable(contractNumber) {
    const tbody = document.getElementById('category-rows');
    const existingRow = tbody.querySelector(`tr[data-contract-number="${contractNumber}"]`);
    if (!existingRow) {
        console.log(`Adding new contract row for ${contractNumber}`);
        const newRowHtml = `
            <tr data-contract-number="${contractNumber}">
                <td class="expandable-cell" onclick="window.expandCategory('${encodeURIComponent(contractNumber).replace(/'/g, "\\'").replace(/"/g, '\\"')}', 'common-${contractNumber}', '${contractNumber}')">
                    ${contractNumber}
                </td>
                <td>N/A</td>
                <td id="items-on-contract-${contractNumber}">0</td>
                <td>0</td>
                <td id="hand-counted-entries-${contractNumber}">0</td>
                <td class="date-last-scanned">N/A</td>
                <td>
                    <button class="btn btn-sm btn-secondary expand-btn" data-contract-number="${contractNumber}" data-target-id="common-${contractNumber}">Expand</button>
                    <button class="btn btn-sm btn-secondary collapse-btn" data-collapse-target="common-${contractNumber}" style="display:none;">Collapse</button>
                    <button class="btn btn-sm btn-info print-btn" data-print-level="Contract" data-print-id="common-${contractNumber}" data-contract-number="${contractNumber}">Print</button>
                    <div id="loading-${contractNumber}" style="display:none;" class="loading">Loading...</div>
                </td>
            </tr>
            <tr>
                <td colspan="7">
                    <div id="common-${contractNumber}" class="expandable collapsed"></div>
                </td>
            </tr>
        `;
        tbody.insertAdjacentHTML('beforeend', newRowHtml);
    }
}

function updateContractCounts(contractNumber) {
    fetch(`/tab/4/contract_items_count?contract_number=${encodeURIComponent(contractNumber)}`)
        .then(response => {
            if (!response.ok) throw new Error('Failed to fetch Items on Contract');
            return response.json();
        })
        .then(data => {
            const currentCountElement = document.getElementById(`items-on-contract-${contractNumber}`);
            if (currentCountElement) {
                currentCountElement.textContent = data.total_items || 0;
            }
        })
        .catch(error => console.error('Error updating Items on Contract count:', error));
    fetch(`/tab/4/hand_counted_entries?contract_number=${encodeURIComponent(contractNumber)}`)
        .then(response => {
            if (!response.ok) throw new Error('Failed to fetch Hand-Counted Entries');
            return response.json();
        })
        .then(data => {
            const handCountedElement = document.getElementById(`hand-counted-entries-${contractNumber}`);
            if (handCountedElement) {
                handCountedElement.textContent = data.hand_counted_entries || 0;
            }
        })
        .catch(error => console.error('Error updating Hand-Counted Entries count:', error));
}

function refreshCommonNames(contractNumber) {
    const commonDiv = document.getElementById(`common-${contractNumber}`);
    if (commonDiv && !commonDiv.classList.contains('collapsed')) {
        window.expandCategory(
            encodeURIComponent(contractNumber),
            `common-${contractNumber}`,
            contractNumber
        );
    }
}

document.addEventListener('DOMContentLoaded', function() {
    if (window.cachedTabNum !== 4) return;
    fetch('/tab/4/hand_counted_contracts')
        .then(response => response.json())
        .then(data => {
            const contractDropdown = document.getElementById('hand-counted-contract-number');
            data.contracts.forEach(contract => {
                const option = document.createElement('option');
                option.value = contract;
                option.textContent = contract;
                contractDropdown.appendChild(option);
            });
        })
        .catch(error => console.error('Error fetching hand-counted contracts:', error));
    document.querySelectorAll('#category-rows tr').forEach(row => {
        const scanDateCell = row.querySelector('td.date-last-scanned');
        if (scanDateCell) {
            const rawDate = scanDateCell.textContent.trim();
            scanDateCell.textContent = formatDate(rawDate);
        }
    });
});

document.body.addEventListener('htmx:afterSwap', function(event) {
    const target = event.target;
    if (target.id === 'hand-counted-items') {
        const rows = target.querySelectorAll('tr');
        rows.forEach(row => {
            const timestampCell = row.querySelector('td:nth-child(5)');
            if (timestampCell) {
                const rawDate = timestampCell.textContent.trim();
                timestampCell.textContent = formatDate(rawDate);
            }
        });
    }
});