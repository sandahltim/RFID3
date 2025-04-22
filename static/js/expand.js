console.log('expand.js version: 2025-04-22 v13 loaded');

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
            div.style.display = 'none'; // Ensure hidden
        }
    });
}

// --- Common Names Display Management ---
function hideOtherCommonNames(currentSubcategoryId) {
    console.log('hideOtherCommonNames called with currentSubcategoryId:', currentSubcategoryId);
    const allCommonDivs = document.querySelectorAll('div[id^="common-"]');
    console.log('Found common name divs:', allCommonDivs.length);
    allCommonDivs.forEach(div => {
        console.log('Common name div ID:', div.id);
        if (div.id !== 'common-' + currentSubcategoryId) {
            console.log('Collapsing common name div:', div.id);
            div.classList.remove('expanded');
            div.classList.add('collapsed');
            div.style.display = 'none'; // Ensure hidden
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
            div.style.display = 'none'; // Ensure hidden
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
        container.style.display = 'none'; // Ensure hidden
    } else {
        console.warn('Container not found for collapsing with targetId:', targetId);
    }
}

// --- Render Individual Items Data ---
function loadItems(category, subcategory, commonName, targetId) {
    const decodedCategory = decodeURIComponent(category);
    const decodedSubcategory = decodeURIComponent(subcategory);
    const decodedCommonName = decodeURIComponent(commonName);
    console.log('loadItems called with category:', decodedCategory, 'subcategory:', decodedSubcategory, 'commonName:', decodedCommonName, 'targetId:', targetId);
    
    const url = '/tab/' + window.cachedTabNum + '/data?category=' + encodeURIComponent(decodedCategory) + '&subcategory=' + encodeURIComponent(decodedSubcategory) + '&common_name=' + encodeURIComponent(decodedCommonName);
    const container = document.getElementById(targetId);
    if (!container) {
        console.error('Items container not found for ID:', targetId);
        return;
    }

    showLoading(targetId.replace('items-', '')); // Show loading indicator

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
            container.style.display = 'block'; // Ensure visibility

            let html = '';
            if (data && Array.isArray(data) && data.length > 0) {
                hideOtherItems(targetId.replace('items-', ''));
                html += [
                    '<table class="table table-bordered ms-4 mt-2" id="items-table-' + targetId.replace('items-', '') + '">',
                        '<thead>',
                            '<tr>',
                                '<th>Tag ID</th>',
                                '<th>Common Name</th>',
                                '<th>Bin Location</th>',
                                '<th>Status</th>',
                                '<th>Last Contract</th>',
                                '<th>Last Scanned</th>',
                                '<th>Quality</th>',
                                '<th>Notes</th>',
                            '</tr>',
                        '</thead>',
                        '<tbody>'
                ].join('');
                
                data.forEach(item => {
                    html += [
                        '<tr>',
                            '<td>' + (item.tag_id || 'N/A') + '</td>',
                            '<td>' + (item.common_name || 'N/A') + '</td>',
                            '<td>' + (item.bin_location || 'N/A') + '</td>',
                            '<td>' + (item.status || 'N/A') + '</td>',
                            '<td>' + (item.last_contract_num || 'N/A') + '</td>',
                            '<td>' + (item.last_scanned_date || 'N/A') + '</td>',
                            '<td>' + (item.quality || 'N/A') + '</td>',
                            '<td>' + (item.notes || 'N/A') + '</td>',
                        '</tr>'
                    ].join('');
                });

                html += [
                    '</tbody>',
                    '</table>'
                ].join('');
            } else {
                html = '<p class="ms-4">No items found for this common name.</p>';
            }

            container.innerHTML = html;
            console.log('Items table rendered into container');
        })
        .catch(error => {
            console.error('Items fetch error:', error);
            container.innerHTML = '<p class="ms-4 text-danger">Error loading items: ' + error.message + '</p>';
        })
        .finally(() => {
            hideLoading(targetId.replace('items-', ''));
            console.log('loadItems completed for targetId:', targetId);
        });
}

// --- Render Common Names Data ---
function loadCommonNames(category, subcategory, targetId) {
    const decodedCategory = decodeURIComponent(category);
    const decodedSubcategory = decodeURIComponent(subcategory);
    console.log('loadCommonNames called with category:', decodedCategory, 'subcategory:', decodedSubcategory, 'targetId:', targetId);
    
    const url = '/tab/' + window.cachedTabNum + '/common_names?category=' + encodeURIComponent(decodedCategory) + '&subcategory=' + encodeURIComponent(decodedSubcategory);
    const container = document.getElementById(targetId);
    if (!container) {
        console.error('Common names container not found for ID:', targetId);
        return;
    }

    showLoading(targetId.replace('common-', '')); // Show loading indicator

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
            container.style.display = 'block'; // Ensure visibility

            let html = '';
            if (data.common_names && Array.isArray(data.common_names) && data.common_names.length > 0) {
                const targetBaseId = targetId.replace('common-', '');
                hideOtherCommonNames(targetBaseId);
                data.common_names.forEach(cn => {
                    const cnId = targetBaseId + '_' + cn.name.toLowerCase().replace(/[^a-z0-9-]/g, '_');
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
                                    '<td>' + cn.name + '</td>',
                                    '<td>' + (cn.total_items !== undefined ? cn.total_items : 'N/A') + '</td>',
                                    '<td>' + (cn.on_contracts !== undefined ? cn.on_contracts : 'N/A') + '</td>',
                                    '<td>' + (cn.in_service !== undefined ? cn.in_service : 'N/A') + '</td>',
                                    '<td>' + (cn.available !== undefined ? cn.available : 'N/A') + '</td>',
                                    '<td>',
                                        '<button class="btn btn-sm btn-secondary expand-btn" onclick="loadItems(\'' + encodeURIComponent(decodedCategory) + '\', \'' + encodeURIComponent(decodedSubcategory) + '\', \'' + encodeURIComponent(cn.name) + '\', \'items-' + cnId + '\')">Expand</button>',
                                        '<button class="btn btn-sm btn-secondary collapse-btn" style="display:none;" onclick="collapseSection(\'items-' + cnId + '\')">Collapse</button>',
                                        '<button class="btn btn-sm btn-info print-btn" data-print-level="Common Name" data-print-id="common-table-' + cnId + '">Print</button>',
                                        '<div id="loading-' + cnId + '" style="display:none;" class="loading">Loading...</div>',
                                    '</td>',
                                '</tr>',
                                '<tr>',
                                    '<td colspan="6">',
                                        '<div id="items-' + cnId + '" class="expandable collapsed"></div>',
                                    '</td>',
                                '</tr>',
                            '</tbody>',
                        '</table>'
                    ].join('');
                });
            } else {
                html = '<p class="ms-3">No common names found for this category.</p>';
            }

            container.innerHTML = html;

            // Add event listeners to toggle Expand/Collapse buttons
            const expandButtons = container.querySelectorAll('.expand-btn');
            const collapseButtons = container.querySelectorAll('.collapse-btn');
            expandButtons.forEach((btn, index) => {
                btn.addEventListener('click', () => {
                    btn.style.display = 'none';
                    collapseButtons[index].style.display = 'inline-block';
                });
            });
            collapseButtons.forEach((btn, index) => {
                btn.addEventListener('click', () => {
                    btn.style.display = 'none';
                    expandButtons[index].style.display = 'inline-block';
                });
            });

            console.log('Common names table rendered into container');
        })
        .catch(error => {
            console.error('Common names fetch error:', error);
            container.innerHTML = '<p class="ms-3 text-danger">Error loading common names: ' + error.message + '</p>';
        })
        .finally(() => {
            hideLoading(targetId.replace('common-', ''));
            console.log('loadCommonNames completed for targetId:', targetId);
        });
}

// --- Render Subcategory Data ---
function loadSubcatData(originalCategory, normalizedCategory, subcatData) {
    console.log('loadSubcatData called with originalCategory:', originalCategory, 'normalizedCategory:', normalizedCategory, 'subcatData:', subcatData);
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
    container.style.display = 'block'; // Ensure visibility

    let html = '<div class="ms-3">';
    
    if (subcatData && subcatData.length > 0) {
        subcatData.forEach(sub => {
            console.log('Processing subcategory:', sub);
            const subId = normalizedCategory + '_' + sub.subcategory.toLowerCase().replace(/[^a-z0-9-]/g, '_');
            const isTab2 = window.cachedTabNum == 2 || window.cachedTabNum == 3 || window.cachedTabNum == 4; // Tabs 2, 3, 4 treat subcategories as categories
            html += [
                '<table class="table table-bordered mt-2" id="subcat-table-' + subId + '">',
                    '<thead>',
                        '<tr>',
                            '<th>' + (isTab2 ? 'Category' : 'Subcategory') + '</th>',
                            '<th>Total Items</th>',
                            '<th>Items on Contracts</th>',
                            '<th>Items in Service</th>',
                            '<th>Items Available</th>',
                            '<th>Actions</th>',
                        '</tr>',
                    '</thead>',
                    '<tbody>',
                        '<tr>',
                            '<td>' + sub.subcategory + '</td>',
                            '<td>' + (sub.total_items !== undefined ? sub.total_items : 'N/A') + '</td>',
                            '<td>' + (sub.on_contracts !== undefined ? sub.on_contracts : 'N/A') + '</td>',
                            '<td>' + (sub.in_service !== undefined ? sub.in_service : 'N/A') + '</td>',
                            '<td>' + (sub.available !== undefined ? sub.available : 'N/A') + '</td>',
                            '<td>',
                                '<button class="btn btn-sm btn-secondary expand-btn" onclick="loadCommonNames(\'' + encodeURIComponent(originalCategory) + '\', \'' + encodeURIComponent(sub.subcategory) + '\', \'common-' + subId + '\')">Load Items</button>',
                                '<button class="btn btn-sm btn-secondary collapse-btn" style="display:none;" onclick="collapseSection(\'common-' + subId + '\')">Collapse</button>',
                                '<button class="btn btn-sm btn-info print-btn" data-print-level="' + (isTab2 ? 'Category' : 'Subcategory') + '" data-print-id="subcat-table-' + subId + '">Print</button>',
                                '<div id="loading-' + subId + '" style="display:none;" class="loading">Loading...</div>',
                            '</td>',
                        '</tr>',
                        '<tr>',
                            '<td colspan="6">',
                                '<div id="common-' + subId + '" class="expandable collapsed"></div>',
                            '</td>',
                        '</tr>',
                    '</tbody>',
                '</table>'
            ].join('');
        });
    } else {
        html += '<p>No ' + (window.cachedTabNum == 2 || window.cachedTabNum == 3 || window.cachedTabNum == 4 ? 'categories' : 'subcategories') + ' found for this ' + (window.cachedTabNum == 2 || window.cachedTabNum == 3 || window.cachedTabNum == 4 ? 'contract' : 'category') + '.</p>';
    }
    
    html += '</div>';
    console.log('Generated HTML for subcategories:', html);
    container.innerHTML = html;

    // Add event listeners to toggle Expand/Collapse buttons for subcategories
    const expandButtons = container.querySelectorAll('.expand-btn');
    const collapseButtons = container.querySelectorAll('.collapse-btn');
    expandButtons.forEach((btn, index) => {
        btn.addEventListener('click', () => {
            btn.style.display = 'none';
            collapseButtons[index].style.display = 'inline-block';
        });
    });
    collapseButtons.forEach((btn, index) => {
        btn.addEventListener('click', () => {
            btn.style.display = 'none';
            expandButtons[index].style.display = 'inline-block';
        });
    });

    console.log('Subcategory table rendered into container');
}

// --- Main Expand Functionality ---
document.addEventListener('DOMContentLoaded', () => {
    console.log('expand.js: DOMContentLoaded event fired');
    
    window.expandCategory = function(category, targetId) {
        console.log('expandCategory called with category:', category, 'targetId:', targetId);
        const url = '/tab/' + window.cachedTabNum + '/subcat_data?category=' + category;
        showLoading(targetId.replace('subcat-', '')); // Show loading indicator

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
                    throw new Error('Subcat fetch failed with status ' + response.status);
                }
                return response.json();
            })
            .then(data => {
                console.log('Subcat data received:', data);
                const normalizedCategory = targetId.replace('subcat-', '').replace(/\s+/g, '_'); // Normalize spaces to underscores
                const originalCategory = decodeURIComponent(category); // Keep the original category name
                loadSubcatData(originalCategory, normalizedCategory, data);

                // Add event listener for top-level collapse after rendering
                const container = document.getElementById(targetId);
                const expandButton = container.parentElement.parentElement.querySelector('.expand-btn');
                const collapseButton = container.parentElement.parentElement.querySelector('.collapse-btn');
                expandButton.style.display = 'none';
                collapseButton.style.display = 'inline-block';
                collapseButton.addEventListener('click', () => {
                    collapseSection(targetId);
                    collapseButton.style.display = 'none';
                    expandButton.style.display = 'inline-block';
                });
            })
            .catch(error => {
                console.error('Subcat fetch error:', error);
            })
            .finally(() => {
                hideLoading(targetId.replace('subcat-', ''));
                console.log('expandCategory completed for targetId:', targetId);
            });
    };
    
    console.log('expand.js: expandCategory defined');
});