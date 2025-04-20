// Show a loading indicator for a given key (e.g., category ID)
function showLoading(key) {
    const loading = document.getElementById('loading-' + key);
    if (loading) loading.style.display = 'block';
}

// Hide the loading indicator for a given key
function hideLoading(key) {
    const loading = document.getElementById('loading-' + key);
    if (loading) loading.style.display = 'none';
}

// Hide all subcategory sections except the current one
function hideOtherSubcats(currentCategory) {
    const allSubcatDivs = document.querySelectorAll('div[id^="subcat-"]');
    allSubcatDivs.forEach(div => {
        if (div.id !== 'subcat-' + currentCategory.toLowerCase().replace(/[^a-z0-9-]/g, '_')) {
            div.style.display = 'none';
            div.innerHTML = '';  // Clear content to prevent bleed-over
        }
    });
}

// Escape HTML attributes to prevent XSS
function escapeHtmlAttribute(value) {
    return value
        .replace(/&/g, '&')
        .replace(/'/g, ''')
        .replace(/"/g, '"')
        .replace(/</g, '<')
        .replace(/>/g, '>');
}

// Escape JavaScript strings to prevent injection
function escapeJsString(value) {
    return value
        .replace(/\\/g, '\\\\')
        .replace(/'/g, '\\\'')
        .replace(/"/g, '\\"')
        .replace(/\n/g, '\\n')
        .replace(/\r/g, '\\r');
}

// Apply filters to all tables based on user input (text, category, status, bin location)
function applyFilters() {
    const textQuery = document.getElementById('filter-input') ? document.getElementById('filter-input').value.toLowerCase() : '';
    const categoryFilter = document.getElementById('category-filter') ? document.getElementById('category-filter').value.toLowerCase() : '';
    const statusFilter = document.getElementById('status-filter') ? document.getElementById('status-filter').value.toLowerCase() : '';
    const binLocationFilter = document.getElementById('bin-location-filter') ? document.getElementById('bin-location-filter').value.toLowerCase() : '';
    
    const tables = document.querySelectorAll('table');
    tables.forEach(table => {
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const text = Array.from(row.children).map(cell => cell.textContent.toLowerCase()).join(' ');
            const categoryCell = row.querySelector('td:first-child') ? row.querySelector('td:first-child').textContent.toLowerCase() : '';
            const statusCell = row.querySelector('td:nth-child(4)') ? row.querySelector('td:nth-child(4)').textContent.toLowerCase() : '';
            const binLocationCell = row.querySelector('td:nth-child(3)') ? row.querySelector('td:nth-child(3)').textContent.toLowerCase() : '';
            
            const matchesText = text.includes(textQuery);
            const matchesCategory = !categoryFilter || categoryCell.includes(categoryFilter);
            const matchesStatus = !statusFilter || statusCell.includes(statusFilter);
            const matchesBinLocation = !binLocationFilter || binLocationCell.includes(binLocationFilter);
            
            row.style.display = (matchesText && matchesCategory && matchesStatus && matchesBinLocation) ? '' : 'none';
        });
    });
}

// Load subcategory data into the specified container
function loadSubcatData(category, subcatData) {
    hideOtherSubcats(category);
    const container = document.getElementById('subcat-' + category.toLowerCase().replace(/[^a-z0-9-]/g, '_'));
    if (!container) return;
    container.innerHTML = '';
    container.style.display = 'block';
    let html = '<div class="ms-3">';
    
    subcatData.forEach(sub => {
        const subId = category + '_' + sub.subcategory.toLowerCase().replace(/[^a-z0-9-]/g, '_');
        const escapedSubcategory = escapeHtmlAttribute(sub.subcategory);
        const escapedCategory = encodeURIComponent(category);
        const escapedSubcategoryParam = encodeURIComponent(sub.subcategory);
        const escapedSubId = escapeJsString(subId);
        html += [
            '<table class="table table-bordered mt-2" id="subcat-table-' + subId + '">',
                '<thead>',
                    '<tr>',
                        '<th>Subcategory</th>',
                        '<th>Total Items</th>',
                        '<th>Items on Contracts</th>',
                        '<th>Items in Service</th>',
                        '<th>Items Available</th>',
                        '<th>Actions</th>',
                    '</tr>',
                '</thead>',
                '<tbody>',
                    '<tr>',
                        '<td>' + escapedSubcategory + '</td>',
                        '<td>' + (sub.total_items !== undefined ? sub.total_items : 'N/A') + '</td>',
                        '<td>' + (sub.on_contracts !== undefined ? sub.on_contracts : 'N/A') + '</td>',
                        '<td>' + (sub.in_service !== undefined ? sub.in_service : 'N/A') + '</td>',
                        '<td>' + (sub.available !== undefined ? sub.available : 'N/A') + '</td>',
                        '<td>',
                            '<button class="btn btn-sm btn-secondary" onclick="loadCommonNames(\'' + escapedCategory + '\', \'' + escapedSubcategoryParam + '\', \'common-' + subId + '\')">Load Items</button>',
                            '<button id="print-btn-' + subId + '" class="btn btn-sm btn-info print-btn" data-print-level="Subcategory" data-print-id="subcat-table-' + subId + '">Print</button>',
                            '<div id="loading-' + subId + '" style="display:none;" class="loading">Loading...</div>',
                        '</td>',
                    '</tr>',
                    '<tr>',
                        '<td colspan="6">',
                            '<div id="common-' + subId + '" style="display:none;"></div>',
                            '<div id="items-' + subId + '" style="display:none;"></div>',
                        '</td>',
                    '</tr>',
                '</tbody>',
            '</table>'
        ].join('');
    });
    
    html += '</div>';
    container.innerHTML = html;
    applyFilters();
}

//部分

// Load common names data into the specified container
function loadCommonNames(category, subcategory, targetId) {
    const url = '/tab/' + window.cachedTabNum + '/common_names?category=' + category + '&subcategory=' + subcategory;
    const container = document.getElementById(targetId);
    if (!container) return;

    showLoading(targetId.replace('common-', '')); // Show loading indicator

    fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Common names fetch failed with status ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            container.style.display = 'block';

            let html = '';
            if (data.common_names && Array.isArray(data.common_names)) {
                data.common_names.forEach(cn => {
                    const cnId = targetId.replace('common-', '') + '_' + cn.name.toLowerCase().replace(/[^a-z0-9-]/g, '_');
                    const escapedCommonName = escapeHtmlAttribute(cn.name);
                    const escapedCategory = encodeURIComponent(category);
                    const escapedSubcategory = encodeURIComponent(subcategory);
                    const escapedCommonNameParam = encodeURIComponent(cn.name);
                    const escapedCnId = escapeJsString(cnId);
                    html += [
                        '<table class="table table-bordered ms-3 mt-2" id="common-table-' + cnId + '">',
                            '<thead>',
                                '<tr>',
                                    '<th>Common Name</th>',
                                    '<th>Total Items</th>',
                                    '<th>Items on Contracts</th>',
                                    '<th>Items in Service</th>',
                                    '<th>Items Available</th>',
                                    '<th>Actions</th>',
                                '</tr>',
                            '</thead>',
                            '<tbody>',
                                '<tr>',
                                    '<td>' + escapedCommonName + '</td>',
                                    '<td>' + (cn.total_items !== undefined ? cn.total_items : 'N/A') + '</td>',
                                    '<td>' + (cn.on_contracts !== undefined ? cn.on_contracts : 'N/A') + '</td>',
                                    '<td>' + (cn.in_service !== undefined ? cn.in_service : 'N/A') + '</td>',
                                    '<td>' + (cn.available !== undefined ? cn.available : 'N/A') + '</td>',
                                    '<td>',
                                        '<button class="btn btn-sm btn-secondary" onclick="loadItems(\'' + escapedCategory + '\', \'' + escapedSubcategory + '\', \'' + escapedCommonNameParam + '\', \'items-' + cnId + '\')">Load Items</button>',
                                        '<button id="print-btn-' + cnId + '" class="btn btn-sm btn-info print-btn" data-print-level="Common Name" data-print-id="common-table-' + cnId + '">Print</button>',
                                        '<div id="loading-' + cnId + '" style="display:none;" class="loading">Loading...</div>',
                                    '</td>',
                                '</tr>',
                                '<tr>',
                                    '<td colspan="6">',
                                        '<div id="items-' + cnId + '" style="display:none;"></div>',
                                    '</td>',
                                '</tr>',
                            '</tbody>',
                        '</table>'
                    ].join('');
                });
            } else {
                html = '<p>No common names found.</p>';
            }

            container.innerHTML = html;
            applyFilters();
        })
        .catch(error => {
            console.error('Common names fetch error:', error);
        })
        .finally(() => {
            hideLoading(targetId.replace('common-', ''));
        });
}

// Load items data into the specified container
function loadItems(category, subcategory, commonName, targetId) {
    const url = '/tab/' + window.cachedTabNum + '/data?category=' + category + '&subcategory=' + subcategory + '&common_name=' + commonName;
    const container = document.getElementById(targetId);
    if (!container) return;

    showLoading(targetId.replace('items-', '')); // Show loading indicator

    fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Items fetch failed with status ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            container.style.display = 'block';
            let html = [
                '<table class="table table-bordered ms-3 mt-2" id="items-table-' + targetId + '">',
                    '<thead>',
                        '<tr>',
                            '<th>Tag ID</th>',
                            '<th>Common Name</th>',
                            '<th>Bin Location</th>',
                            '<th>Status</th>',
                            '<th>Last Contract</th>',
                            '<th>Last Scanned Date</th>',
                            '<th>Quality</th>',
                            '<th>Notes</th>',
                            '<th>Actions</th>',
                        '</tr>',
                    '</thead>',
                    '<tbody>'
            ].join('');
            if (data.length === 0) {
                html += [
                    '<tr>',
                        '<td colspan="9">No items found for this common name.</td>',
                    '</tr>'
                ].join('');
            } else {
                data.forEach(item => {
                    html += [
                        '<tr>',
                            '<td>' + (item.tag_id || '') + '</td>',
                            '<td>' + (item.common_name || '') + '</td>',
                            '<td>' + (item.bin_location || '') + '</td>',
                            '<td>' + (item.status || '') + '</td>',
                            '<td>' + (item.last_contract_num || '') + '</td>',
                            '<td>' + (item.last_scanned_date || '') + '</td>',
                            '<td>' + (item.quality || '') + '</td>',
                            '<td>' + (item.notes || '') + '</td>',
                            '<td>',
                                '<button id="print-btn-items-' + targetId + '" class="btn btn-sm btn-info print-btn" data-print-level="Item" data-print-id="items-table-' + targetId + '">',
                                    'Print',
                                '</button>',
                            '</td>',
                        '</tr>'
                    ].join('');
                });
            }
            html += [
                    '</tbody>',
                '</table>'
            ].join('');
            container.innerHTML = html;
            applyFilters();
        })
        .catch(error => {
            console.error('Items fetch error:', error);
        })
        .finally(() => {
            hideLoading(targetId.replace('items-', ''));
        });
}

// Attach expandCategory to the window object to ensure global accessibility
window.expandCategory = expandCategory;

// Confirm expandCategory is defined
document.addEventListener('DOMContentLoaded', () => {
    console.log('expand.js loaded, expandCategory defined:', typeof window.expandCategory === 'function');
});