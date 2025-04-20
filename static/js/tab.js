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

// Open a print window with the specified table content
function printTable(level, id) {
    console.log(`Printing table: ${level}, ID: ${id}`);
    const element = document.getElementById(id);
    if (!element) {
        console.warn(`Element with ID '${id}' not found for printing.`);
        return;
    }

    // Alert to check if popup blocker is interfering
    alert('Opening print window... If no window appears, check your browser\'s popup blocker settings.');

    // Test a minimal window.open() to isolate popup blocker issues
    const testWindow = window.open('', '_blank');
    if (testWindow) {
        testWindow.document.write('<html><body><h1>Test Window</h1></body></html>');
        testWindow.document.close();
        console.log('Test window opened successfully');
    } else {
        console.error('Test window failed to open. Popup blocker may be preventing window.open().');
        return;
    }

    // Proceed with the actual print window
    const printWindow = window.open('', '_blank');
    if (!printWindow) {
        console.error('Print window failed to open. Popup blocker may be preventing window.open().');
        return;
    }

    try {
        printWindow.document.write(`
            <html>
                <head>
                    <title>Print ${level} - RFID Dashboard</title>
                    <link href="/static/lib/bootstrap/bootstrap.min.css" rel="stylesheet">
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        h2 { text-align: center; }
                        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                        th { background-color: #f2f2f2; }
                        .print-header { text-align: center; margin-bottom: 20px; }
                    </style>
                </head>
                <body>
                    <div class="print-header">
                        <h1>RFID Dashboard Report</h1>
                        <p>Generated on ${new Date().toLocaleString()}</p>
                        <h2>${level}</h2>
                    </div>
                    ${element.outerHTML}
                    <script>
                        window.onload = function() { 
                            try {
                                window.print();
                                window.close();
                            } catch (e) {
                                console.error('Error in print window:', e);
                            }
                        }
                    </script>
                </body>
            </html>
        `);
        printWindow.document.close();
        console.log('Print window content written successfully');
    } catch (error) {
        console.error('Error writing to print window:', error);
        printWindow.close();
    }
}

// Refresh the category table by triggering an HTMX load event
let isRefreshing = false;
function refreshTable(tabNum) {
    if (isRefreshing) return;
    isRefreshing = true;
    console.log(`Refreshing table for tab ${tabNum}`);
    const categoryTable = document.getElementById('category-table-body');
    if (categoryTable) {
        htmx.trigger('#category-table-body', 'htmx:load');
    } else {
        console.warn('Category table body not found for refresh.');
    }
    setTimeout(() => { isRefreshing = false; }, 1000);
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
        const hxGetUrl = `/tab/${cachedTabNum}/common_names?category=${encodeURIComponent(category)}&subcategory=${encodeURIComponent(sub.subcategory)}`;
        console.log(`Generated hx-get URL for subcategory ${sub.subcategory}: ${hxGetUrl}`);
        
        const escapedHxGetUrl = escapeHtmlAttribute(hxGetUrl);
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
                            <button class="btn btn-sm btn-secondary" hx-get="${escapedHxGetUrl}" hx-target="#common-${subId}" hx-swap="innerHTML">Load Items</button>
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
    // Process HTMX attributes on the newly added content
    if (typeof htmx !== 'undefined') {
        htmx.process(container);
        console.log('HTMX processed subcategory container');
    } else {
        console.error('HTMX not available when processing subcategory container');
    }
    applyFilters();
}

// Load common names data into the specified container
function loadCommonNames(category, subcategory, commonNamesData) {
    console.log(`Loading common names for category: ${category}, subcategory: ${subcategory}`, commonNamesData);
    const subId = `${category}_${subcategory}`.toLowerCase().replace(/[^a-z0-9-]/g, '_');
    const container = document.getElementById(`common-${subId}`);
    if (!container) {
        console.warn(`Container with ID 'common-${subId}' not found.`);
        return;
    }
    container.style.display = 'block';

    let html = '';
    if (commonNamesData.common_names && Array.isArray(commonNamesData.common_names)) {
        commonNamesData.common_names.forEach(cn => {
            const cnId = `${subId}_${cn.name}`.toLowerCase().replace(/[^a-z0-9-]/g, '_');
            const escapedCommonName = escapeHtmlAttribute(cn.name);
            const hxGetUrl = `/tab/${cachedTabNum}/data?category=${encodeURIComponent(category)}&subcategory=${encodeURIComponent(subcategory)}&common_name=${encodeURIComponent(cn.name)}`;
            console.log(`Generated hx-get URL for common name ${cn.name}: ${hxGetUrl}`);
            
            const escapedHxGetUrl = escapeHtmlAttribute(hxGetUrl);
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
                                <button class="btn btn-sm btn-secondary" hx-get="${escapedHxGetUrl}" hx-target="#items-${cnId}" hx-swap="innerHTML">Load Items</button>
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
    // Process HTMX attributes on the newly added content
    if (typeof htmx !== 'undefined') {
        htmx.process(container);
        console.log('HTMX processed common names container');
    } else {
        console.error('HTMX not available when processing common names container');
    }
    applyFilters();
}

// Handle manual fetching of subcategory data when "Expand" is clicked
function expandCategory(category, targetId) {
    console.log(`Expanding category: ${category}, target: ${targetId}`);
    
    // Test fetch to /health to verify network functionality (already confirmed working)
    console.log('Testing network with fetch to /health');
    fetch('/health')
        .then(response => {
            console.log('Health fetch status:', response.status, response.statusText);
            return response.json();
        })
        .then(data => console.log('Health fetch response:', data))
        .catch(error => console.error('Health fetch error:', error));

    // Test fetch to /tab/1/categories to verify if the issue is specific to /tab/1/subcat_data
    console.log('Testing fetch to /tab/1/categories');
    fetch(`/tab/${cachedTabNum}/categories`)
        .then(response => {
            console.log('Categories fetch status:', response.status, response.statusText);
            return response.text(); // Expect HTML, not JSON
        })
        .then(data => console.log('Categories fetch response:', data.slice(0, 100) + '...')) // Log first 100 chars
        .catch(error => console.error('Categories fetch error:', error));

    // Fetch subcategory data manually with enhanced options
    const url = `/tab/${cachedTabNum}/subcat_data?category=${category}`;
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
            hideLoading(targetId.replace('subcat-', ''));
        })
        .catch(error => {
            clearTimeout(timeoutId);
            console.error('Subcat fetch error:', error);
            if (error.name === 'AbortError') {
                console.error('Subcat fetch timed out after 5 seconds');
            }
            hideLoading(targetId.replace('subcat-', ''));
        });
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('Document loaded, initializing HTMX listeners');
    const h1Element = document.querySelector('h1');
    if (h1Element && window.location.pathname.startsWith('/tab/')) {
        const h1Text = h1Element.textContent.trim();
        const tabNumMatch = h1Text.match(/Tab\s+(\d+)/i);
        if (tabNumMatch && tabNumMatch[1]) {
            cachedTabNum = tabNumMatch[1];
            setInterval(() => refreshTable(cachedTabNum), 30000);
        } else {
            console.warn('No tab number found in h1 element, using default tab number 1.');
        }
    } else if (!window.location.pathname.startsWith('/tab/')) {
        console.debug('Not a tab page, skipping tab number detection.');
    } else {
        console.warn('No h1 element found on the page, using default tab number 1.');
    }

    if (typeof htmx === 'undefined') {
        console.error('HTMX library not loaded. Please ensure htmx.min.js is included in the page.');
        return;
    } else {
        console.log('HTMX library loaded successfully');
        console.log('HTMX version:', htmx.version);
    }

    // Direct click listener for print-btn buttons
    document.querySelectorAll('.print-btn').forEach(button => {
        button.addEventListener('click', (event) => {
            console.log('Direct click on print-btn:', button);
            console.log('Event details:', event);
            const level = button.getAttribute('data-print-level');
            const id = button.getAttribute('data-print-id');
            console.log(`Print button clicked: level=${level}, id=${id}`);
            printTable(level, id);
        });
    });

    document.body.addEventListener('htmx:afterRequest', (event) => {
        console.log('HTMX request completed for target:', event.detail.target.id);
        console.log('Response:', event.detail.xhr.responseText);
        const targetId = event.detail.target.id;
        const catKey = targetId.replace('subcat-', '').replace('common-', '').replace('items-', '');
        hideLoading(catKey);
    });

    document.body.addEventListener('htmx:beforeRequest', (event) => {
        console.log('HTMX request initiated:', event.detail.elt.getAttribute('hx-get'));
    });

    document.body.addEventListener('htmx:responseError', (event) => {
        console.error('HTMX response error:', event.detail.xhr.status, event.detail.xhr.statusText, event.detail.xhr.responseText);
    });

    document.body.addEventListener('htmx:configRequest', (event) => {
        console.log('HTMX configRequest event:', event.detail);
    });

    document.body.addEventListener('htmx:load', (event) => {
        console.log('HTMX load event:', event.detail.elt);
    });
});

document.body.addEventListener('htmx:afterSwap', (event) => {
    console.log('HTMX afterSwap event for target:', event.detail.target.id, 'Response:', event.detail.xhr.responseText);
    const targetId = event.detail.target.id;
    if (targetId === 'category-table-body') {
        const container = document.getElementById('category-table-body');
        if (container) {
            if (typeof htmx !== 'undefined') {
                htmx.process(container);
                console.log('HTMX processed category table body');
                const buttons = container.querySelectorAll('button[hx-get]');
                console.log(`Found ${buttons.length} buttons with hx-get after processing`);
                buttons.forEach(button => {
                    console.log('HTMX-processed button:', {
                        text: button.textContent,
                        hxGet: button.getAttribute('hx-get'),
                        hxTarget: button.getAttribute('hx-target')
                    });
                });
            } else {
                console.error('HTMX not available when processing category table body');
            }
        }
    }
    if (targetId.startsWith('subcat-')) {
        const category = targetId.replace('subcat-', '');
        const data = JSON.parse(event.detail.xhr.responseText);
        loadSubcatData(category, data);
    } else if (targetId.startsWith('common-')) {
        const categoryMatch = event.detail.requestConfig.elt.getAttribute('hx-get').match(/category=([^&]+)/);
        const subcategoryMatch = event.detail.requestConfig.elt.getAttribute('hx-get').match(/subcategory=([^&]+)/);
        if (!categoryMatch || !subcategoryMatch) {
            console.error('Failed to parse category or subcategory from hx-get:', event.detail.requestConfig.elt.getAttribute('hx-get'));
            return;
        }
        const category = decodeURIComponent(categoryMatch[1]);
        const subcategory = decodeURIComponent(subcategoryMatch[1]);
        const data = JSON.parse(event.detail.xhr.responseText);
        loadCommonNames(category, subcategory, data);
    } else if (targetId.startsWith('items-')) {
        const container = document.getElementById(targetId);
        if (container) {
            container.style.display = 'block';
            const data = JSON.parse(event.detail.xhr.responseText);
            console.log(`Rendering items for target ${targetId}:`, data);
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
            if (typeof htmx !== 'undefined') {
                htmx.process(container);
                console.log('HTMX processed items container');
            } else {
                console.error('HTMX not available when processing items container');
            }
            applyFilters();
        } else {
            console.warn(`Container with ID '${targetId}' not found.`);
        }
    }
});