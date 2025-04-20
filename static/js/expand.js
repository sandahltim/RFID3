// Show a loading indicator for a given key (e.g., category ID)
function showLoading(key) {
    console.log(`Showing loading for key: ${key}`);
    const loading = document.getElementById(`loading-${key}`);
    if (loading) loading.style.display = 'block';
}

// Hide the loading indicator for a given key
function hideLoading(key) {
    console.log(`Hiding loading for key: ${key}`);
    const loading = document.getElementById(`loading-${key}`);
    if (loading) loading.style.display = 'none';
}

// Hide all subcategory sections except the current one
function hideOtherSubcats(currentCategory) {
    console.log(`Hiding other subcategories except for: ${currentCategory}`);
    const allSubcatDivs = document.querySelectorAll('div[id^="subcat-"]');
    allSubcatDivs.forEach(div => {
        if (div.id !== `subcat-${currentCategory.toLowerCase().replace(/[^a-z0-9-]/g, '_')}`) {
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

// Load subcategory data into the specified container
function loadSubcatData(category, subcatData) {
    console.log(`Loading subcategories for category: ${category}`, subcatData);
    hideOtherSubcats(category);
    const container = document.getElementById(`subcat-${category.toLowerCase().replace(/[^a-z0-9-]/g, '_')}`);
    if (!container) {
        console.warn(`Container with ID 'subcat-${category.toLowerCase().replace(/[^a-z0-9-]/g, '_')}' not found.`);
        return;
    }
    container.innerHTML = '';
    container.style.display = 'block';
    let html = '<div class="ms-3">';
    
    subcatData.forEach(sub => {
        console.log(`Rendering subcategory for ${category}: ${sub.subcategory}`);
        const subId = `${category}_${sub.subcategory}`.toLowerCase().replace(/[^a-z0-9-]/g, '_');
        const escapedSubcategory = escapeHtmlAttribute(sub.subcategory);
        const escapedCategory = encodeURIComponent(category);
        const escapedSubcategoryParam = encodeURIComponent(sub.subcategory);
        const escapedSubId = escapeJsString(subId);
        html += `
            <table class="table table-bordered mt-2" id="subcat-table-${subId}">
                <thead>
                    <tr>
                        <th>Subcategory</th>
                        <th>Total Items</th>
                        <th>Items on Contracts</th>
                        <th>Items in Service</th>
                        <th>Items Available</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>${escapedSubcategory}</td>
                        <td>${sub.total_items !== undefined ? sub.total_items : 'N/A'}</td>
                        <td>${sub.on_contracts !== undefined ? sub.on_contracts : 'N/A'}</td>
                        <td>${sub.in_service !== undefined ? sub.in_service : 'N/A'}</td>
                        <td>${sub.available !== undefined ? sub.available : 'N/A'}</td>
                        <td>
                            <button class="btn btn-sm btn-secondary" onclick="loadCommonNames('${escapedCategory}', '${escapedSubcategoryParam}', 'common-${subId}')">Load Items</button>
                            <button id="print-btn-${subId}" class="btn btn-sm btn-info print-btn" data-print-level="Subcategory" data-print-id="subcat-table-${subId}">Print</button>
                            <div id="loading-${subId}" style="display:none;" class="loading">Loading...</div>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="6">
                            <div id="common-${subId}" style="display:none;"></div>
                            <div id="items-${subId}" style="display:none;"></div>
                        </td>
                    </tr>
                </tbody>
            </table>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
    console.log('Subcategory HTML rendered:', container.innerHTML);
    applyFilters();
}

// Load common names data into the specified container
function loadCommonNames(category, subcategory, targetId) {
    console.log(`Fetching common names for category: ${category}, subcategory: ${subcategory}`);
    const url = `/tab/${window.cachedTabNum}/common_names?category=${category}&subcategory=${subcategory}`;
    const container = document.getElementById(targetId);
    if (!container) {
        console.warn(`Container with ID '${targetId}' not found.`);
        return;
    }

    showLoading(targetId.replace('common-', '')); // Show loading indicator

    fetch(url)
        .then(response => {
            console.log('Common names fetch status:', response.status, response.statusText);
            if (!response.ok) {
                throw new Error(`Common names fetch failed with status ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Common names fetch response:', data);
            container.style.display = 'block';

            let html = '';
            if (data.common_names && Array.isArray(data.common_names)) {
                data.common_names.forEach(cn => {
                    const cnId = `${targetId.replace('common-', '')}_${cn.name}`.toLowerCase().replace(/[^a-z0-9-]/g, '_');
                    const escapedCommonName = escapeHtmlAttribute(cn.name);
                    const escapedCategory = encodeURIComponent(category);
                    const escapedSubcategory = encodeURIComponent(subcategory);
                    const escapedCommonNameParam = encodeURIComponent(cn.name);
                    const escapedCnId = escapeJsString(cnId);
                    html += `
                        <table class="table table-bordered ms-3 mt-2" id="common-table-${cnId}">
                            <thead>
                                <tr>
                                    <th>Common Name</th>
                                    <th>Total Items</th>
                                    <th>Items on Contracts</th>
                                    <th>Items in Service</th>
                                    <th>Items Available</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>${escapedCommonName}</td>
                                    <td>${cn.total_items !== undefined ? cn.total_items : 'N/A'}</td>
                                    <td>${cn.on_contracts !== undefined ? cn.on_contracts : 'N/A'}</td>
                                    <td>${cn.in_service !== undefined ? cn.in_service : 'N/A'}</td>
                                    <td>${cn.available !== undefined ? cn.available : 'N/A'}</td>
                                    <td>
                                        <button class="btn btn-sm btn-secondary" onclick="loadItems('${escapedCategory}', '${escapedSubcategory}', '${escapedCommonNameParam}', 'items-${cnId}')">Load Items</button>
                                        <button id="print-btn-${cnId}" class="btn btn-sm btn-info print-btn" data-print-level="Common Name" data-print-id="common-table-${cnId}">Print</button>
                                        <div id="loading-${cnId}" style="display:none;" class="loading">Loading...</div>
                                    </td>
                                </tr>
                                <tr>
                                    <td colspan="6">
                                        <div id="items-${cnId}" style="display:none;"></div>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    `;
                });
            } else {
                html = '<p>No common names found.</p>';
            }

            container.innerHTML = html;
            console.log('Common names HTML rendered:', container.innerHTML);
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
    console.log(`Fetching items for category: ${category}, subcategory: ${subcategory}, common_name: ${commonName}`);
    const url = `/tab/${window.cachedTabNum}/data?category=${category}&subcategory=${subcategory}&common_name=${commonName}`;
    const container = document.getElementById(targetId);
    if (!container) {
        console.warn(`Container with ID '${targetId}' not found.`);
        return;
    }

    showLoading(targetId.replace('items-', '')); // Show loading indicator

    fetch(url)
        .then(response => {
            console.log('Items fetch status:', response.status, response.statusText);
            if (!response.ok) {
                throw new Error(`Items fetch failed with status ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log(`Rendering items for target ${targetId}:`, data);
            container.style.display = 'block';
            let html = `
                <table class="table table-bordered ms-3 mt-2" id="items-table-${targetId}">
                    <thead>
                        <tr>
                            <th>Tag ID</th>
                            <th>Common Name</th>
                            <th>Bin Location</th>
                            <th>Status</th>
                            <th>Last Contract</th>
                            <th>Last Scanned Date</th>
                            <th>Quality</th>
                            <th>Notes</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            if (data.length === 0) {
                html += `
                    <tr>
                        <td colspan="9">No items found for this common name.</td>
                    </tr>
                `;
            } else {
                data.forEach(item => {
                    html += `
                        <tr>
                            <td>${item.tag_id || ''}</td>
                            <td>${item.common_name || ''}</td>
                            <td>${item.bin_location || ''}</td>
                            <td>${item.status || ''}</td>
                            <td>${item.last_contract_num || ''}</td>
                            <td>${item.last_scanned_date || ''}</td>
                            <td>${item.quality || ''}</td>
                            <td>${item.notes || ''}</td>
                            <td>
                                <button id="print-btn-items-${targetId}" class="btn btn-sm btn-info print-btn" data-print-level="Item" data-print-id="items-table-${targetId}">
                                    Print
                                </button>
                            </td>
                        </tr>
                    `;
                });
            }
            html += `
                    </tbody>
                </table>
            `;
            container.innerHTML = html;
            console.log(`Items table rendered for target ${targetId}:`, container.innerHTML);
            applyFilters();
        })
        .catch(error => {
            console.error('Items fetch error:', error);
        })
        .finally(() => {
            hideLoading(targetId.replace('items-', ''));
        });
}

// Handle manual fetching of subcategory data when "Expand" is clicked
function expandCategory(category, targetId) {
    console.log(`Expanding category: ${category}, target: ${targetId}`);
    
    // Fetch subcategory data manually
    const url = `/tab/${window.cachedTabNum}/subcat_data?category=${category}`;
    console.log(`Fetching subcategory data from: ${url}`);
    showLoading(targetId.replace('subcat-', '')); // Show loading indicator

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5-second timeout

    fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        signal: controller.signal
    })
        .then(response => {
            clearTimeout(timeoutId);
            console.log('Subcat fetch status:', response.status, response.statusText);
            if (!response.ok) {
                throw new Error(`Subcat fetch failed with status ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Subcat fetch response:', data);
            const categoryName = targetId.replace('subcat-', '');
            loadSubcatData(categoryName, data);
        })
        .catch(error => {
            console.error('Subcat fetch error:', error);
            if (error.name === 'AbortError') {
                console.error('Subcat fetch timed out after 5 seconds');
            }
        })
        .finally(() => {
            hideLoading(targetId.replace('subcat-', ''));
        });
}

// Attach expandCategory to the window object to ensure global accessibility
window.expandCategory = expandCategory;

// Confirm expandCategory is defined
document.addEventListener('DOMContentLoaded', () => {
    console.log('expand.js loaded, expandCategory defined:', typeof window.expandCategory === 'function');
});