console.log('expand.js version: 2025-04-23 v27 loaded');

// --- Loading Indicator Functions ---
function showLoading(key) {
    console.log('showLoading called with key:', key);
    const loading = document.getElementById('loading-' + key);
    if (loading) {
        console.log('Loading indicator found, displaying:', loading);
        loading.style.display = 'block';
    } else {
        console.warn('Loading indicator not found for key:', key);
    }
}

function hideLoading(key) {
    console.log('hideLoading called with key:', key);
    const loading = document.getElementById('loading-' + key);
    if (loading) {
        console.log('Loading indicator found, hiding:', loading);
        loading.style.display = 'none';
    } else {
        console.warn('Loading indicator not found for key:', key);
    }
}

// --- Subcategory Display Management ---
function hideOtherSubcats(currentCategory) {
    console.log('hideOtherSubcats called with currentCategory:', currentCategory);
    const allSubcatDivs = document.querySelectorAll('div[id^="subcat-"]');
    console.log('Found subcat divs:', allSubcatDivs.length);
    allSubcatDivs.forEach(div => {
        console.log('Subcat div ID:', div.id);
        if (div.id !== 'subcat-' + currentCategory.toLowerCase().replace(/[^a-z0-9-]/g, '_')) {
            console.log('Collapsing subcat div:', div.id);
            div.classList.remove('expanded');
            div.classList.add('collapsed');
            div.style.display = 'none';

            // Reset buttons for collapsed sections
            const parentRow = div.closest('tr');
            if (parentRow) {
                const expandButton = parentRow.previousElementSibling.querySelector('.expand-btn');
                const collapseButton = parentRow.previousElementSibling.querySelector('.collapse-btn');
                if (expandButton && collapseButton) {
                    expandButton.style.display = 'inline-block';
                    collapseButton.style.display = 'none';
                }
            }
        }
    });
}

// --- Common Names Display Management ---
function hideOtherCommonNames(currentId) {
    console.log('hideOtherCommonNames called with currentId:', currentId);
    const allCommonDivs = document.querySelectorAll('div[id^="common-"]');
    console.log('Found common name divs:', allCommonDivs.length);
    allCommonDivs.forEach(div => {
        console.log('Common name div ID:', div.id);
        if (div.id !== 'common-' + currentId) {
            console.log('Collapsing common name div:', div.id);
            div.classList.remove('expanded');
            div.classList.add('collapsed');
            div.style.display = 'none';

            // Reset buttons for collapsed sections
            const parentRow = div.closest('tr');
            if (parentRow) {
                const expandButton = parentRow.previousElementSibling.querySelector('.expand-btn');
                const collapseButton = parentRow.previousElementSibling.querySelector('.collapse-btn');
                if (expandButton && collapseButton) {
                    expandButton.style.display = 'inline-block';
                    collapseButton.style.display = 'none';
                }
            }
        }
    });
}

// --- Individual Items Display Management ---
function hideOtherItems(currentCommonId) {
    console.log('hideOtherItems called with currentCommonId:', currentCommonId);
    const allItemDivs = document.querySelectorAll('div[id^="items-"]');
    console.log('Found item divs:', allItemDivs.length);
    allItemDivs.forEach(div => {
        console.log('Item div ID:', div.id);
        if (div.id !== 'items-' + currentCommonId) {
            console.log('Collapsing item div:', div.id);
            div.classList.remove('expanded');
            div.classList.add('collapsed');
            div.style.display = 'none';

            // Reset buttons for collapsed sections
            const parentRow = div.closest('tr');
            if (parentRow) {
                const expandButton = parentRow.previousElementSibling.querySelector('.expand-btn');
                const collapseButton = parentRow.previousElementSibling.querySelector('.collapse-btn');
                if (expandButton && collapseButton) {
                    expandButton.style.display = 'inline-block';
                    collapseButton.style.display = 'none';
                }
            }
        }
    });
}

// --- Collapse Functionality ---
function collapseSection(targetId) {
    console.log('collapseSection called with targetId:', targetId);
    const container = document.getElementById(targetId);
    if (container) {
        console.log('Container found, collapsing:', container);
        container.classList.remove('expanded');
        container.classList.add('collapsed');
        container.style.display = 'none';

        // Find the parent row and toggle buttons
        const parentRow = container.closest('tr');
        const expandButton = parentRow.previousElementSibling.querySelector('.expand-btn');
        const collapseButton = parentRow.previousElementSibling.querySelector('.collapse-btn');
        if (expandButton && collapseButton) {
            expandButton.style.display = 'inline-block';
            collapseButton.style.display = 'none';
        }
    } else {
        console.warn('Container not found for collapsing with targetId:', targetId);
    }
}

// --- Update Bin Location (for Tab 5) ---
function updateBinLocation(tagId, selectElement) {
    const newBinLocation = selectElement.value;
    console.log('updateBinLocation called with tagId:', tagId, 'newBinLocation:', newBinLocation);

    fetch('/tab/5/update_bin_location', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            tag_id: tagId,
            bin_location: newBinLocation
        })
    })
    .then(response => {
        console.log('Update bin location response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Update bin location response data:', data);
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error updating bin location:', error);
        alert('Failed to update bin location');
    });
}

// --- Render Individual Items Data with Pagination ---
function loadItems(category, subcategory, commonName, targetId, page = 1) {
    const decodedCategory = decodeURIComponent(category);
    const decodedSubcategory = subcategory ? decodeURIComponent(subcategory) : null;
    const decodedCommonName = decodeURIComponent(commonName);
    console.log('loadItems called with category:', decodedCategory, 'subcategory:', decodedSubcategory, 'commonName:', decodedCommonName, 'targetId:', targetId, 'page:', page);
    
    const isTab2or4 = window.cachedTabNum == 2 || window.cachedTabNum == 4;
    const url = isTab2or4 
        ? '/tab/' + window.cachedTabNum + '/data?category=' + encodeURIComponent(decodedCategory) + '&common_name=' + encodeURIComponent(decodedCommonName) + '&page=' + page
        : '/tab/' + window.cachedTabNum + '/data?category=' + encodeURIComponent(decodedCategory) + '&subcategory=' + encodeURIComponent(decodedSubcategory) + '&common_name=' + encodeURIComponent(decodedCommonName) + '&page=' + page;

    const container = document.getElementById(targetId);
    if (!container) {
        console.error('Items container not found for ID:', targetId);
        return;
    }

    showLoading(targetId.replace('items-', ''));

    fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    })
        .then(response => {
            console.log('Fetch finished loading: GET "' + url + '"');
            if (!response.ok) {
                throw new Error('Items fetch failed with status ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            console.log('Items data received:', data);
            container.classList.add('expandable');
            container.classList.remove('collapsed');
            container.classList.add('expanded');
            container.style.display = 'block';

            let html = '';
            const isTab1or5 = window.cachedTabNum == 1 || window.cachedTabNum == 5;
            if ((data.items && Array.isArray(data.items) && data.items.length > 0) || (data && Array.isArray(data) && data.length > 0)) {
                const items = data.items || data;
                hideOtherItems(targetId.replace('items-', ''));
                html += [
                    '<div class="item-level-wrapper">',
                    '<div class="pagination-controls mt-2">'
                ].join('');

                const totalPages = Math.ceil(data.total_items / data.per_page);
                if (totalPages > 1) {
                    if (data.page > 1) {
                        html += `<button class="btn btn-sm btn-secondary" onclick="loadItems('${encodeURIComponent(decodedCategory)}', ${isTab2or4 ? 'null' : '\'' + encodeURIComponent(decodedSubcategory) + '\''}, '${encodeURIComponent(decodedCommonName)}', '${targetId}', ${data.page - 1})">Previous</button>`;
                    }
                    html += `<span>Page ${data.page} of ${totalPages}</span>`;
                    if (data.page < totalPages) {
                        html += `<button class="btn btn-sm btn-secondary" onclick="loadItems('${encodeURIComponent(decodedCategory)}', ${isTab2or4 ? 'null' : '\'' + encodeURIComponent(decodedSubcategory) + '\''}, '${encodeURIComponent(decodedCommonName)}', '${targetId}', ${data.page + 1})">Next</button>`;
                    }
                }
                html += '</div>';

                html += [
                    '<table class="table table-bordered item-level mt-2">',
                        '<thead>',
                            '<tr>',
                                '<th>Tag ID</th>',
                                '<th>Common Name</th>',
                                '<th>Bin Location</th>',
                                '<th>Status</th>',
                                '<th>Last Contract</th>',
                                '<th>Last Scanned</th>',
                                isTab1or5 ? '<th>Quality</th>' : '',
                                isTab1or5 ? '<th>Notes</th>' : '',
                                window.cachedTabNum == 5 ? '<th>Actions</th>' : '',
                            '</tr>',
                        '</thead>',
                        '<tbody>'
                ].join('');
                
                items.forEach(item => {
                    html += [
                        '<tr>',
                            '<td>' + (item.tag_id || 'N/A') + '</td>',
                            '<td>' + (item.common_name || 'N/A') + '</td>',
                            '<td>',
                                window.cachedTabNum == 5 ? [
                                    '<select class="form-control bin-location-select" onchange="updateBinLocation(\'' + item.tag_id + '\', this)">',
                                        '<option value="resale"' + (item.bin_location === 'resale' ? ' selected' : '') + '>Resale</option>',
                                        '<option value="sold"' + (item.bin_location === 'sold' ? ' selected' : '') + '>Sold</option>',
                                        '<option value="pack"' + (item.bin_location === 'pack' ? ' selected' : '') + '>Pack</option>',
                                        '<option value="burst"' + (item.bin_location === 'burst' ? ' selected' : '') + '>Burst</option>',
                                    '</select>'
                                ].join('') : (item.bin_location || 'N/A'),
                            '</td>',
                            '<td>' + (item.status || 'N/A') + '</td>',
                            '<td>' + (item.last_contract_num || 'N/A') + '</td>',
                            '<td>' + (item.last_scanned_date || 'N/A') + '</td>',
                            isTab1or5 ? '<td>' + (item.quality || 'N/A') + '</td>' : '',
                            isTab1or5 ? '<td>' + (item.notes || 'N/A') + '</td>' : '',
                            window.cachedTabNum == 5 ? '<td><button class="btn btn-sm btn-primary" onclick="updateBinLocation(\'' + item.tag_id + '\', this.previousElementSibling)">Update</button></td>' : '',
                        '</tr>'
                    ].join('');
                });

                html += [
                    '</tbody>',
                    '</table>'
                ].join('');

                if (totalPages > 1) {
                    html += '<div class="pagination-controls mt-2">';
                    if (data.page > 1) {
                        html += `<button class="btn btn-sm btn-secondary" onclick="loadItems('${encodeURIComponent(decodedCategory)}', ${isTab2or4 ? 'null' : '\'' + encodeURIComponent(decodedSubcategory) + '\''}, '${encodeURIComponent(decodedCommonName)}', '${targetId}', ${data.page - 1})">Previous</button>`;
                    }
                    html += `<span>Page ${data.page} of ${totalPages}</span>`;
                    if (data.page < totalPages) {
                        html += `<button class="btn btn-sm btn-secondary" onclick="loadItems('${encodeURIComponent(decodedCategory)}', ${isTab2or4 ? 'null' : '\'' + encodeURIComponent(decodedSubcategory) + '\''}, '${encodeURIComponent(decodedCommonName)}', '${targetId}', ${data.page + 1})">Next</button>`;
                    }
                    html += '</div>';
                }
                html += '</div>';
            } else {
                html = '<p class="item-level">No items found for this common name.</p>';
            }

            container.innerHTML = html;

            const parentRow = container.closest('tr');
            const expandButton = parentRow.previousElementSibling.querySelector('.expand-btn');
            const collapseButton = parentRow.previousElementSibling.querySelector('.collapse-btn');
            if (expandButton && collapseButton) {
                expandButton.style.display = 'none';
                collapseButton.style.display = 'inline-block';
            }

            console.log('Items table rendered into container');
        })
        .catch(error => {
            console.error('Items fetch error:', error);
            container.innerHTML = '<p class="item-level text-danger">Error loading items: ' + error.message + '</p>';
        })
        .finally(() => {
            hideLoading(targetId.replace('items-', ''));
            console.log('loadItems completed for targetId:', targetId);
        });
}

// --- Render Common Names Data with Pagination ---
function loadCommonNames(category, subcategory, targetId, page = 1) {
    const decodedCategory = decodeURIComponent(category);
    const decodedSubcategory = subcategory ? decodeURIComponent(subcategory) : null;
    console.log('loadCommonNames called with category:', decodedCategory, 'subcategory:', decodedSubcategory, 'targetId:', targetId, 'page:', page);
    
    const isTab2or4 = window.cachedTabNum == 2 || window.cachedTabNum == 4;
    const url = isTab2or4
        ? '/tab/' + window.cachedTabNum + '/common_names?category=' + encodeURIComponent(decodedCategory) + '&page=' + page
        : '/tab/' + window.cachedTabNum + '/common_names?category=' + encodeURIComponent(decodedCategory) + '&subcategory=' + encodeURIComponent(decodedSubcategory) + '&page=' + page;

    const containerId = isTab2or4 ? targetId : 'common-' + targetId;
    const container = document.getElementById(containerId);
    if (!container) {
        console.error('Common names container not found for ID:', containerId);
        return;
    }

    showLoading(targetId.replace('common-', ''));

    fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    })
        .then(response => {
            console.log('Fetch finished loading: GET "' + url + '"');
            if (!response.ok) {
                throw new Error('Common names fetch failed with status ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            console.log('Common names data received:', data);
            container.classList.add('expandable');
            container.classList.remove('collapsed');
            container.classList.add('expanded');
            container.style.display = 'block';

            let html = '';
            const isTab1or5 = window.cachedTabNum == 1 || window.cachedTabNum == 5;
            if (data.common_names && Array.isArray(data.common_names) && data.common_names.length > 0) {
                const targetBaseId = targetId.replace('common-', '');
                hideOtherCommonNames(targetBaseId);

                html += '<div class="pagination-controls mt-2">';
                const totalPages = Math.ceil(data.total_common_names / data.per_page);
                if (totalPages > 1) {
                    if (data.page > 1) {
                        html += `<button class="btn btn-sm btn-secondary" onclick="loadCommonNames('${encodeURIComponent(decodedCategory)}', ${isTab2or4 ? 'null' : '\'' + encodeURIComponent(decodedSubcategory) + '\''}, '${targetId}', ${data.page - 1})">Previous</button>`;
                    }
                    html += `<span>Page ${data.page} of ${totalPages}</span>`;
                    if (data.page < totalPages) {
                        html += `<button class="btn btn-sm btn-secondary" onclick="loadCommonNames('${encodeURIComponent(decodedCategory)}', ${isTab2or4 ? 'null' : '\'' + encodeURIComponent(decodedSubcategory) + '\''}, '${targetId}', ${data.page + 1})">Next</button>`;
                    }
                }
                html += '</div>';

                data.common_names.forEach(cn => {
                    const cnId = targetBaseId + '_' + cn.name.toLowerCase().replace(/[^a-z0-9-]/g, '_');
                    html += [
                        '<table class="table table-bordered common-level mt-2" id="common-table-' + cnId + '">',
                            '<thead>',
                                '<tr>',
                                    '<th>Common Name</th>',
                                    isTab1or5 ? '<th>Total Items</th>' : '<th>Total Items in Inventory</th>',
                                    isTab1or5 ? '<th>Items on Contracts</th>' : '<th>Items on This Contract</th>',
                                    isTab1or5 ? '<th>Items in Service</th>' : '',
                                    isTab1or5 ? '<th>Items Available</th>' : '',
                                    '<th>Actions</th>',
                                '</tr>',
                            '</thead>',
                            '<tbody>',
                                '<tr>',
                                    '<td>' + cn.name + '</td>',
                                    isTab1or5 ? '<td>' + (cn.total_items !== undefined ? cn.total_items : 'N/A') + '</td>' : '<td>' + (cn.total_items_inventory !== undefined ? cn.total_items_inventory : 'N/A') + '</td>',
                                    '<td>' + (cn.items_on_contract !== undefined ? cn.items_on_contract : cn.on_contracts !== undefined ? cn.on_contracts : 'N/A') + '</td>',
                                    isTab1or5 ? '<td>' + (cn.in_service !== undefined ? cn.in_service : 'N/A') + '</td>' : '',
                                    isTab1or5 ? '<td>' + (cn.available !== undefined ? cn.available : 'N/A') + '</td>' : '',
                                    '<td>',
                                        '<button class="btn btn-sm btn-secondary expand-btn" onclick="loadItems(\'' + encodeURIComponent(decodedCategory) + '\', ' + (isTab2or4 ? 'null' : '\'' + encodeURIComponent(decodedSubcategory) + '\'') + ', \'' + encodeURIComponent(cn.name) + '\', \'items-' + cnId + '\')">Expand</button>',
                                        '<button class="btn btn-sm btn-secondary collapse-btn" style="display:none;" onclick="collapseSection(\'items-' + cnId + '\')">Collapse</button>',
                                        '<button class="btn btn-sm btn-info print-btn" data-print-level="Common Name" data-print-id="common-table-' + cnId + '">Print</button>',
                                        '<div id="loading-' + cnId + '" style="display:none;" class="loading">Loading...</div>',
                                    '</td>',
                                '</tr>',
                                '<tr>',
                                    isTab1or5 ? '<td colspan="6">' : '<td colspan="4">',
                                        '<div id="items-' + cnId + '" class="expandable collapsed"></div>',
                                    '</td>',
                                '</tr>',
                            '</tbody>',
                        '</table>'
                    ].join('');
                });

                if (totalPages > 1) {
                    html += '<div class="pagination-controls mt-2">';
                    if (data.page > 1) {
                        html += `<button class="btn btn-sm btn-secondary" onclick="loadCommonNames('${encodeURIComponent(decodedCategory)}', ${isTab2or4 ? 'null' : '\'' + encodeURIComponent(decodedSubcategory) + '\''}, '${targetId}', ${data.page - 1})">Previous</button>`;
                    }
                    html += `<span>Page ${data.page} of ${totalPages}</span>`;
                    if (data.page < totalPages) {
                        html += `<button class="btn btn-sm btn-secondary" onclick="loadCommonNames('${encodeURIComponent(decodedCategory)}', ${isTab2or4 ? 'null' : '\'' + encodeURIComponent(decodedSubcategory) + '\''}, '${targetId}', ${data.page + 1})">Next</button>`;
                    }
                    html += '</div>';
                }
            } else {
                html = '<p class="common-level">No common names found for this ' + (isTab2or4 ? 'contract' : 'subcategory') + '.</p>';
            }

            container.innerHTML = html;

            const parentRow = container.closest('tr');
            const expandButton = parentRow.previousElementSibling.querySelector('.expand-btn');
            const collapseButton = parentRow.previousElementSibling.querySelector('.collapse-btn');
            if (expandButton && collapseButton) {
                expandButton.style.display = 'none';
                collapseButton.style.display = 'inline-block';
            }

            console.log('Common names table rendered into container');
        })
        .catch(error => {
            console.error('Common names fetch error:', error);
            container.innerHTML = '<p class="common-level text-danger">Error loading common names: ' + error.message + '</p>';
        })
        .finally(() => {
            hideLoading(targetId.replace('common-', ''));
            console.log('loadCommonNames completed for targetId:', targetId);
        });
}

// --- Render Subcategory Data with Pagination ---
function loadSubcatData(originalCategory, normalizedCategory, targetId, page = 1) {
    console.log('loadSubcatData called with originalCategory:', originalCategory, 'normalizedCategory:', normalizedCategory, 'targetId:', targetId, 'page:', page);
    hideOtherSubcats(normalizedCategory);
    const containerId = 'subcat-' + normalizedCategory.toLowerCase().replace(/[^a-z0-9-]/g, '_');
    console.log('Looking for container with ID:', containerId);
    const container = document.getElementById(containerId);
    if (!container) {
        console.error('Subcategory container not found for ID:', containerId);
        return;
    }
    console.log('Container found:', container);
    container.classList.add('expandable');
    container.classList.remove('collapsed');
    container.classList.add('expanded');
    container.style.display = 'block';

    const url = '/tab/' + window.cachedTabNum + '/subcat_data?category=' + encodeURIComponent(originalCategory) + '&page=' + page;
    showLoading(containerId.replace('subcat-', ''));

    fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Subcat fetch failed with status ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            let html = '<div class="subcat-level">';
            const isTab1or5 = window.cachedTabNum == 1 || window.cachedTabNum == 5;

            const totalPages = Math.ceil(data.total_subcats / data.per_page);
            if (totalPages > 1) {
                html += '<div class="pagination-controls mt-2">';
                if (data.page > 1) {
                    html += `<button class="btn btn-sm btn-secondary" onclick="loadSubcatData('${encodeURIComponent(originalCategory)}', '${normalizedCategory}', '${targetId}', ${data.page - 1})">Previous</button>`;
                }
                html += `<span>Page ${data.page} of ${totalPages}</span>`;
                if (data.page < totalPages) {
                    html += `<button class="btn btn-sm btn-secondary" onclick="loadSubcatData('${encodeURIComponent(originalCategory)}', '${normalizedCategory}', '${targetId}', ${data.page + 1})">Next</button>`;
                }
                html += '</div>';
            }

            if (data.subcategories && Array.isArray(data.subcategories) && data.subcategories.length > 0) {
                data.subcategories.forEach(sub => {
                    console.log('Processing subcategory:', sub);
                    const subId = normalizedCategory + '_' + sub.subcategory.toLowerCase().replace(/[^a-z0-9-]/g, '_');
                    html += [
                        '<table class="table table-bordered subcat-table mt-2" id="subcat-table-' + subId + '">',
                            '<thead>',
                                '<tr>',
                                    '<th>Subcategory</th>',
                                    isTab1or5 ? '<th>Total Items</th>' : '<th>Total Items in Inventory</th>',
                                    isTab1or5 ? '<th>Items on Contracts</th>' : '<th>Items on This Contract</th>',
                                    isTab1or5 ? '<th>Items in Service</th>' : '',
                                    isTab1or5 ? '<th>Items Available</th>' : '',
                                    '<th>Actions</th>',
                                '</tr>',
                            '</thead>',
                            '<tbody>',
                                '<tr>',
                                    '<td>' + sub.subcategory + '</td>',
                                    isTab1or5 ? '<td>' + (sub.total_items !== undefined ? sub.total_items : 'N/A') + '</td>' : '<td>' + (sub.total_items_inventory !== undefined ? sub.total_items_inventory : 'N/A') + '</td>',
                                    isTab1or5 ? '<td>' + (sub.on_contracts !== undefined ? sub.on_contracts : 'N/A') + '</td>' : '<td>' + (sub.items_on_contract !== undefined ? sub.items_on_contract : 'N/A') + '</td>',
                                    isTab1or5 ? '<td>' + (sub.in_service !== undefined ? sub.in_service : 'N/A') + '</td>' : '',
                                    isTab1or5 ? '<td>' + (sub.available !== undefined ? sub.available : 'N/A') + '</td>' : '',
                                    '<td>',
                                        '<button class="btn btn-sm btn-secondary expand-btn" onclick="loadCommonNames(\'' + encodeURIComponent(originalCategory) + '\', \'' + encodeURIComponent(sub.subcategory) + '\', \'' + subId + '\')">Expand</button>',
                                        '<button class="btn btn-sm btn-secondary collapse-btn" style="display:none;" onclick="collapseSection(\'common-' + subId + '\')">Collapse</button>',
                                        '<button class="btn btn-sm btn-info print-btn" data-print-level="' + (isTab1or5 ? 'Subcategory' : 'Subcategory') + '" data-print-id="subcat-table-' + subId + '">Print</button>',
                                        '<div id="loading-' + subId + '" style="display:none;" class="loading">Loading...</div>',
                                    '</td>',
                                '</tr>',
                                '<tr>',
                                    isTab1or5 ? '<td colspan="6">' : '<td colspan="4">',
                                        '<div id="common-' + subId + '" class="expandable collapsed"></div>',
                                    '</td>',
                                '</tr>',
                            '</tbody>',
                        '</table>'
                    ].join('');
                });

                if (totalPages > 1) {
                    html += '<div class="pagination-controls mt-2">';
                    if (data.page > 1) {
                        html += `<button class="btn btn-sm btn-secondary" onclick="loadSubcatData('${encodeURIComponent(originalCategory)}', '${normalizedCategory}', '${targetId}', ${data.page - 1})">Previous</button>`;
                    }
                    html += `<span>Page ${data.page} of ${totalPages}</span>`;
                    if (data.page < totalPages) {
                        html += `<button class="btn btn-sm btn-secondary" onclick="loadSubcatData('${encodeURIComponent(originalCategory)}', '${normalizedCategory}', '${targetId}', ${data.page + 1})">Next</button>`;
                    }
                    html += '</div>';
                }
            } else {
                html += '<p>No subcategories found for this category.</p>';
            }
            
            html += '</div>';
            console.log('Generated HTML for subcategories:', html);
            container.innerHTML = html;

            const parentRow = container.closest('tr');
            const expandButton = parentRow.previousElementSibling.querySelector('.expand-btn');
            const collapseButton = parentRow.previousElementSibling.querySelector('.collapse-btn');
            if (expandButton && collapseButton) {
                expandButton.style.display = 'none';
                collapseButton.style.display = 'inline-block';
            }

            console.log('Subcategory table rendered into container');
        })
        .catch(error => {
            console.error('Subcat fetch error:', error);
            container.innerHTML = '<p class="subcat-level text-danger">Error loading subcategories: ' + error.message + '</p>';
        })
        .finally(() => {
            hideLoading(containerId.replace('subcat-', ''));
            console.log('loadSubcatData completed for targetId:', containerId);
        });
}

// --- Main Expand Functionality ---
document.addEventListener('DOMContentLoaded', () => {
    console.log('expand.js: DOMContentLoaded event fired');
    
    window.expandCategory = function(category, targetId, page = 1) {
        console.log('expandCategory called with category:', category, 'targetId:', targetId, 'page:', page);
        const normalizedCategory = targetId.replace('subcat-', '').replace('common-', '').replace(/\s+/g, '_');
        const originalCategory = decodeURIComponent(category);

        const isTab2or4 = window.cachedTabNum == 2 || window.cachedTabNum == 4;
        if (isTab2or4) {
            loadCommonNames(originalCategory, null, targetId, page);
        } else {
            loadSubcatData(originalCategory, normalizedCategory, targetId, page);
        }
    };
    
    console.log('expand.js: expandCategory defined');
});