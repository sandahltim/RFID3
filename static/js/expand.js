// expand.js - Handles category expansion for RFID Dashboard
// Module Purpose: Expands categories to show subcategories on the tab page
// Version: 2025-04-20 v3 - Added detailed logging and space normalization

console.log('expand.js version: 2025-04-20 v3 loaded');

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

// --- Render Subcategory Data ---
function loadSubcatData(category, subcatData) {
    console.log('loadSubcatData called with category:', category, 'subcatData:', subcatData);
    hideOtherSubcats(category);
    const containerId = 'subcat-' + category.toLowerCase().replace(/[^a-z0-9-]/g, '_');
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
        const subId = category + '_' + sub.subcategory.toLowerCase().replace(/[^a-z0-9-]/g, '_');
        html += [
            '<table class="table table-bordered mt-2" id="subcat-table-' + subId + '">',
                '<thead>',
                    '<tr>',
                        '<th>Subcategory</th>',
                        '<th>Total Items</th>',
                        '<th>Items on Contracts</th>',
                        '<th>Items in Service</th>',
                        '<th>Items Available</th>',
                    '</tr>',
                '</thead>',
                '<tbody>',
                    '<tr>',
                        '<td>' + sub.subcategory + '</td>',
                        '<td>' + (sub.total_items !== undefined ? sub.total_items : 'N/A') + '</td>',
                        '<td>' + (sub.on_contracts !== undefined ? sub.on_contracts : 'N/A') + '</td>',
                        '<td>' + (sub.in_service !== undefined ? sub.in_service : 'N/A') + '</td>',
                        '<td>' + (sub.available !== undefined ? sub.available : 'N/A') + '</td>',
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
                const categoryName = targetId.replace('subcat-', '').replace(/\s+/g, '_'); // Normalize spaces to underscores
                loadSubcatData(categoryName, data);
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