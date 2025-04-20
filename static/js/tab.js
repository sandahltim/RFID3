// Global variable to cache the tab number, extracted from the h1 element
let cachedTabNum = '1'; // Default to '1' if h1 is not found or no number is present

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

// Sort a table by a specified column
function sortTable(column, tableId) {
    console.log(`Sorting table ${tableId} by column: ${column}`);
    const table = document.getElementById(tableId);
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    const index = Array.from(table.querySelector('thead tr').children).findIndex(th => th.textContent === column);
    
    rows.sort((a, b) => {
        const aText = a.children[index].textContent.trim();
        const bText = b.children[index].textContent.trim();
        return aText.localeCompare(bText);
    });
    
    const tbody = table.querySelector('tbody');
    tbody.innerHTML = '';
    rows.forEach(row => tbody.appendChild(row));
}

// Apply filters to all tables based on user input (text, category, status, bin location)
function applyFilters() {
    console.log('Applying filters');
    const textQuery = document.getElementById('filter-input')?.value.toLowerCase() || '';
    const categoryFilter = document.getElementById('category-filter')?.value.toLowerCase() || '';
    const statusFilter = document.getElementById('status-filter')?.value.toLowerCase() || '';
    const binLocationFilter = document.getElementById('bin-location-filter')?.value.toLowerCase() || '';
    
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

// Print the table content in the current window
function printTable(level, id) {
    console.log(`Printing table: ${level}, ID: ${id}`);
    const element = document.getElementById(id);
    if (!element) {
        console.warn(`Element with ID '${id}' not found for printing.`);
        return;
    }

    // Inform the user that printing will occur in the current window due to popup blockers
    alert('Printing will occur in the current window.\n\nNote: If you prefer a new window, please allow popups for this site:\n1. Click the lock icon in the address bar (left of "pi5:3609")\n2. Click "Site settings"\n3. Find "Pop-ups and redirects" and set to "Allow"\n4. Reload the page and try again');

    // Create a temporary container for the print content
    const printContainer = document.createElement('div');
    printContainer.style.position = 'absolute';
    printContainer.style.top = '0';
    printContainer.style.left = '0';
    printContainer.style.width = '100%';
    printContainer.style.background = 'white';
    printContainer.style.zIndex = '1000';
    printContainer.innerHTML = `
        <div class="print-header">
            <h1>RFID Dashboard Report</h1>
            <p>Generated on ${new Date().toLocaleString()}</p>
            <h2>${level}</h2>
        </div>
        ${element.outerHTML}
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h2 { text-align: center; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .print-header { text-align: center; margin-bottom: 20px; }
        </style>
    `;

    // Hide the main content and show the print content
    const originalContent = document.body.innerHTML;
    document.body.innerHTML = '';
    document.body.appendChild(printContainer);

    // Trigger print and restore original content
    try {
        window.print();
        console.log('Print triggered successfully');
    } catch (error) {
        console.error('Error during print:', error);
    } finally {
        document.body.innerHTML = originalContent;
        console.log('Original content restored after print');
    }
}

// Refresh the category table by triggering a manual fetch
let isRefreshing = false;
function refreshTable(tabNum) {
    if (isRefreshing) return;
    isRefreshing = true;
    console.log(`Refreshing table for tab ${tabNum}`);
    const categoryTableBody = document.getElementById('category-table-body');
    if (!categoryTableBody) {
        console.warn('Category table body not found for refresh.');
        setTimeout(() => { isRefreshing = false; }, 1000);
        return;
    }

    // Manually fetch the categories
    fetch(`/tab/${tabNum}/categories`)
        .then(response => {
            console.log('Refresh fetch status:', response.status, response.statusText);
            if (!response.ok) {
                throw new Error(`Refresh fetch failed with status ${response.status}`);
            }
            return response.text();
        })
        .then(html => {
            console.log('Refresh fetch response:', html.slice(0, 100) + '...');
            categoryTableBody.innerHTML = html;
        })
        .catch(error => {
            console.error('Refresh fetch error:', error);
        })
        .finally(() => {
            setTimeout(() => { isRefreshing = false; }, 1000);
        });
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
    const url = `/tab/${cachedTabNum}/common_names?category=${category}&subcategory=${subcategory}`;
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
    const url = `/tab/${cachedTabNum}/data?category=${category}&subcategory=${subcategory}&common_name=${commonName}`;
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
    const url = `/tab/${cachedTabNum}/subcat_data?category=${category}`;
    console.log(`Fetching subcategory data from: ${url}`);
    showLoading(targetId.replace('subcat-', '')); // Show loading indicator

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5-second timeout

    try {
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
    } catch (error) {
        console.error('Error in subcat fetch:', error);
        hideLoading(targetId.replace('subcat-', ''));
    }
}

// Attach expandCategory to the window object to ensure global accessibility
window.expandCategory = expandCategory;

document.addEventListener('DOMContentLoaded', () => {
    console.log('Document loaded, initializing script');
    
    // Safely extract the tab number from the h1 element
    const h1Element = document.querySelector('h1');
    if (h1Element) {
        try {
            const h1Text = h1Element.textContent.trim();
            const tabNumMatch = h1Text.match(/Tab\s+(\d+)/i);
            if (tabNumMatch && tabNumMatch[1]) {
                cachedTabNum = tabNumMatch[1];
                console.log(`Extracted tab number: ${cachedTabNum}`);
                // Only set up the refresh interval on tab pages
                if (window.location.pathname.startsWith('/tab/')) {
                    setInterval(() => refreshTable(cachedTabNum), 30000);
                }
            } else {
                console.warn('No tab number found in h1 element, using default tab number 1.');
            }
        } catch (error) {
            console.error('Error extracting tab number from h1:', error);
        }
    } else {
        console.warn('No h1 element found on the page, using default tab number 1.');
    }

    // Skip tab-specific logic on non-tab pages
    if (!window.location.pathname.startsWith('/tab/')) {
        console.debug('Not a tab page, skipping tab-specific logic.');
    }

    // Confirm expandCategory is defined
    console.log('expandCategory defined:', typeof window.expandCategory === 'function');

    // Direct click listener for print-btn buttons
    document.querySelectorAll('.print-btn').forEach(button => {
        console.log('Setting up print button listener for:', button);
        button.addEventListener('click', (event) => {
            console.log('Direct click on print-btn:', button);
            console.log('Event details:', event);
            const level = button.getAttribute('data-print-level');
            const id = button.getAttribute('data-print-id');
            console.log(`Print button clicked: level=${level}, id=${id}`);
            printTable(level, id);
        });
    });
});