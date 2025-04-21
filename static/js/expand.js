// expand.js - Handles category expansion for RFID Dashboard
// Module Purpose: Expands categories to show subcategories and common names on the tab page
// Version: 2025-04-20 v6 - Fixed category passing for common names fetch

console.log('expand.js version: 2025-04-20 v6 loaded');

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
            console.log('Hiding subcat div:', div.id);
            div.style.display = 'none';
            div.innerHTML = '';  // Clear content to prevent bleed-over
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
            console.log('Hiding common name div:', div.id);
            div.style.display = 'none';
            div.innerHTML = '';  // Clear content to prevent bleed-over
        }
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
            container.style.display = 'block';

            let html = '';
            if (data.common_names && Array.isArray(data.common_names)) {
                hideOtherCommonNames(targetId.replace('common-', ''));
                data.common_names.forEach(cn => {
                    const cnId = targetId.replace('common-', '') + '_' + cn.name.toLowerCase().replace(/[^a-z0-9-]/g, '_');
                    html += [
                        '<table class="table table-bordered ms-3 mt-2" id="common-table-' + cnId + '">',
                            '<thead>',
                                '<tr>',
                                    '<th>Common Name</th>',
                                    '<th>Total Items</th>',
                                    '<th>Items on Contracts</th>',
                                    '<th>Items in Service</th>',
                                    '<th>Items Available</th>',
                                '</tr>',
                            '</thead>',
                            '<tbody>',
                                '<tr>',
                                    '<td>' + cn.name + '</td>',
                                    '<td>' + (cn.total_items !== undefined ? cn.total_items : 'N/A') + '</td>',
                                    '<td>' + (cn.on_contracts !== undefined ? cn.on_contracts : 'N/A') + '</td>',
                                    '<td>' + (cn.in_service !== undefined ? cn.in_service : 'N/A') + '</td>',
                                    '<td>' + (cn.available !== undefined ? cn.available : 'N/A') + '</td>',
                                '</tr>',
                            '</tbody>',
                        '</table>'
                    ].join('');
                });
            } else {
                html = '<p class="ms-3">No common names found.</p>';
            }

            container.innerHTML = html;
            console.log('Common names table rendered into container');
        })
        .catch(error => {
            console.error('Common names fetch error:', error);
            container.innerHTML = '<p class="ms-3 text-danger">Error loading common names.</p>';
        })
        .finally(() => {
            hideLoading(targetId.replace('common-', ''));
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
    container.innerHTML = '';
    container.style.display = 'block';
    let html = '<div class="ms-3">';
    
    subcatData.forEach(sub => {
        console.log('Processing subcategory:', sub);
        const subId = normalizedCategory + '_' + sub.subcategory.toLowerCase().replace(/[^a-z0-9-]/g, '_');
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
                        '<td>' + sub.subcategory + '</td>',
                        '<td>' + (sub.total_items !== undefined ? sub.total_items : 'N/A') + '</td>',
                        '<td>' + (sub.on_contracts !== undefined ? sub.on_contracts : 'N/A') + '</td>',
                        '<td>' + (sub.in_service !== undefined ? sub.in_service : 'N/A') + '</td>',
                        '<td>' + (sub.available !== undefined ? sub.available : 'N/A') + '</td>',
                        '<td>',
                            '<button class="btn btn-sm btn-secondary" onclick="loadCommonNames(\'' + encodeURIComponent(originalCategory) + '\', \'' + encodeURIComponent(sub.subcategory) + '\', \'common-' + subId + '\')">Load Items</button>',
                            '<div id="loading-' + subId + '" style="display:none;" class="loading">Loading...</div>',
                        '</td>',
                    '</tr>',
                    '<tr>',
                        '<td colspan="6">',
                            '<div id="common-' + subId + '" style="display:none;"></div>',
                        '</td>',
                    '</tr>',
                '</tbody>',
            '</table>'
        ].join('');
    });
    
    html += '</div>';
    console.log('Generated HTML for subcategories:', html);
    container.innerHTML = html;
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
            })
            .catch(error => {
                console.error('Subcat fetch error:', error);
            })
            .finally(() => {
                hideLoading(targetId.replace('subcat-', ''));
            });
    };
    
    console.log('expand.js: expandCategory defined');
});