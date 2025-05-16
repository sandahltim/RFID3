console.log('expand.js version: 2025-05-16-v88 loaded');

// Show loading indicator [REUSABLE]
function showLoadingExpand(targetId) {
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

// Hide loading indicator [REUSABLE]
function hideLoadingExpand(targetId) {
    const loadingDiv = document.getElementById(`loading-${targetId}`);
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

// Collapse section [REUSABLE]
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

// Expand category [TAB 2/4 SPECIFIC]
window.expandCategory = function(category, targetId, contractNumber, page = 1) {
    console.log('expandCategory:', { category, targetId, contractNumber, page });

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

    const loadingSuccess = showLoadingExpand(targetId);
    const url = `/tab/${window.cachedTabNum}/common_names?contract_number=${encodeURIComponent(contractNumber)}&page=${page}`;
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
                                <th>Common Name <span class="sort-arrow"></span></th>
                                <th>Items on Contract <span class="sort-arrow"></span></th>
                                <th>Total Items in Inventory <span class="sort-arrow"></span></th>
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
                        <td class="expandable-cell" onclick="expandItems('${contractNumber}', '${escapedCommonName}', 'items-${commonId}')">${common.name}</td>
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
                        <button class="btn btn-sm btn-secondary" onclick="window.expandCategory('${escapedCategory}', '${targetId}', '${contractNumber}', ${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>
                        <span class="mx-2">Page ${currentPage} of ${totalPages}</span>
                        <button class="btn btn-sm btn-secondary" onclick="window.expandCategory('${escapedCategory}', '${targetId}', '${contractNumber}', ${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>
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
            if (table && typeof applyFilterToTable === 'function') {
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
            if (loadingSuccess) hideLoadingExpand(targetId);
        });
};

// Expand items [TAB 2/4 SPECIFIC]
window.expandItems = function(contractNumber, commonName, targetId, page = 1) {
    console.log('expandItems:', { contractNumber, commonName, targetId, page });

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
    const loadingSuccess = showLoadingExpand(`loading-items-${commonId}`); // Use the correct ID for the loading indicator
    targetElement.innerHTML = '';

    const url = `/tab/${window.cachedTabNum}/data?contract_number=${encodeURIComponent(contractNumber)}&common_name=${encodeURIComponent(commonName)}&page=${page}`;
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

            html += `</tbody></table></div>`;

            if (totalItems > perPage) {
                const totalPages = Math.ceil(totalItems / perPage);
                const escapedCommonName = commonName.replace(/'/g, "\\'").replace(/"/g, '\\"');
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
            targetElement.style.visibility = 'visible';

            console.log('Items container styles:', {
                classList: targetElement.classList.toString(),
                display: targetElement.style.display,
                opacity: targetElement.style.opacity,
                visibility: window.getComputedStyle(targetElement).visibility
            });

            const table = targetElement.querySelector('.item-table');
            if (table && typeof applyFilterToTable === 'function') {
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
            if (loadingSuccess) hideLoadingExpand(`loading-items-${commonId}`);
        });
};

// Sorting state [TAB 2/4 SPECIFIC]
let commonSortState = {};
let itemSortState = {};

// Sort common names [TAB 2/4 SPECIFIC]
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

    const url = `/tab/${window.cachedTabNum}/common_names?contract_number=${encodeURIComponent(contractNumber)}&sort=${column}_${direction}`;
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
                                <th>Common Name <span class="sort-arrow"></span></th>
                                <th>Items on Contract <span class="sort-arrow"></span></th>
                                <th>Total Items in Inventory <span class="sort-arrow"></span></th>
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
                        <td class="expandable-cell" onclick="expandItems('${contractNumber}', '${escapedCommonName}', 'items-${commonId}')">${common.name}</td>
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
                        <button class="btn btn-sm btn-secondary" onclick="window.expandCategory('', '${targetId}', '${contractNumber}', ${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>
                        <span class="mx-2">Page ${currentPage} of ${totalPages}</span>
                        <button class="btn btn-sm btn-secondary" onclick="window.expandCategory('', '${targetId}', '${contractNumber}', ${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>
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
            console.error('Common names sort error:', error.message);
        });
};

// Sort items [TAB 2/4 SPECIFIC]
function sortItems(contractNumber, commonName, column) {
    const targetId = `items-${contractNumber}-${commonName.replace(/[^a-z0-9]/g, '_')}`;
    if (!itemSortState[targetId]) {
        itemSortState[targetId] = { column: '', direction: '' };
    }

    let direction = 'asc';
    if (itemSortState[targetId].column === column) {
        direction = itemSortState[targetId].direction === 'asc' ? 'desc' : 'asc';
    }
    itemSortState[targetId] = { column, direction };

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

    const url = `/tab/${window.cachedTabNum}/data?contract_number=${encodeURIComponent(contractNumber)}&common_name=${encodeURIComponent(commonName)}&sort=${column}_${direction}`;
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

            html += `</tbody></table></div>`;

            if (totalItems > perPage) {
                const totalPages = Math.ceil(totalItems / perPage);
                const escapedCommonName = commonName.replace(/'/g, "\\'").replace(/"/g, '\\"');
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
            console.error('Items sort error:', error.message);
        });
};

// Event listener [TAB 2/4 SPECIFIC]
document.addEventListener('DOMContentLoaded', function() {
    console.log('expand.js: DOMContentLoaded');

    if (!window.cachedTabNum) {
        const pathMatch = window.location.pathname.match(/\/tab\/(\d+)/);
        window.cachedTabNum = pathMatch ? parseInt(pathMatch[1], 10) : (window.location.pathname === '/' ? 1 : null);
        console.log('expand.js: Set window.cachedTabNum:', window.cachedTabNum);
    } else {
        console.log('expand.js: window.cachedTabNum already set:', window.cachedTabNum);
    }

    if (window.cachedTabNum !== 2 && window.cachedTabNum !== 4) {
        console.log(`Tab ${window.cachedTabNum} detected, skipping expand.js`);
        return;
    }

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
                expandItems(contractNumber, commonName, targetId);
            } else {
                console.log(`Expanding common names for ${contractNumber}`);
                window.expandCategory(category, targetId, contractNumber);
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

        const header = event.target.closest('.common-table th');
        if (header) {
            const table = header.closest('table');
            const contractNumber = table.closest('.expandable').id.replace('common-', '');
            const column = header.textContent.trim().toLowerCase().replace(/\s+/g, '_');
            console.log(`Sorting common names for ${contractNumber}, column: ${column}`);
            sortCommonNames(contractNumber, column);
            return;
        }

        const itemHeader = event.target.closest('.item-table th');
        if (itemHeader) {
            const table = itemHeader.closest('table');
            const itemId = table.closest('.expandable').id;
            const contractNumber = itemId.split('-')[0];
            const commonName = itemId.split('-').slice(1).join('-').replace(/_/g, ' ');
            const column = itemHeader.textContent.trim().toLowerCase().replace(/\s+/g, '_');
            console.log(`Sorting items for ${contractNumber}, ${commonName}, column: ${column}`);
            sortItems(contractNumber, commonName, column);
            return;
        }
    }

    if (window.cachedTabNum === 4) {
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
    }
});