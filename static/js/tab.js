// Cache the tab number globally to avoid repeated DOM queries
let cachedTabNum = '1'; // Default to '1' if h1 is not found or no number is present

function showLoading(key) {
    console.log(`Showing loading for key: ${key}`);
    const loading = document.getElementById(`loading-${key}`);
    if (loading) loading.style.display = 'block';
}

function hideLoading(key) {
    console.log(`Hiding loading for key: ${key}`);
    const loading = document.getElementById(`loading-${key}`);
    if (loading) loading.style.display = 'none';
}

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

function printTable(level, id) {
    console.log(`Printing table: ${level}, ID: ${id}`);
    const element = document.getElementById(id);
    if (!element) {
        console.warn(`Element with ID '${id}' not found for printing.`);
        return;
    }
    const printWindow = window.open('', '_blank');
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
                    window.onload = function() { window.print(); window.close(); }
                </script>
            </body>
        </html>
    `);
    printWindow.document.close();
}

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

function escapeHtmlAttribute(value) {
    return value
        .replace(/&/g, '&')
        .replace(/'/g, ''')
        .replace(/"/g, '"')
        .replace(/</g, '<')
        .replace(/>/g, '>');
}

function escapeJsString(value) {
    return value
        .replace(/\\/g, '\\\\')
        .replace(/'/g, '\\\'')
        .replace(/"/g, '\\"')
        .replace(/\n/g, '\\n')
        .replace(/\r/g, '\\r');
}

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
                            <button class="btn btn-sm btn-info print-btn" data-print-level="Subcategory" data-print-id="subcat-table-${subId}">Print</button>
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
                                <button class="btn btn-sm btn-info print-btn" data-print-level="Common Name" data-print-id="common-table-${cnId}">Print</button>
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

    // Debug button clicks and HTMX attributes
    document.querySelectorAll('button[hx-get]').forEach(button => {
        button.addEventListener('click', (event) => {
            console.log(`Button clicked: ${button.textContent}, hx-get: ${button.getAttribute('hx-get')}`);
            console.log('HTMX attributes on button:', {
                hxGet: button.getAttribute('hx-get'),
                hxTarget: button.getAttribute('hx-target'),
                hxSwap: button.getAttribute('hx-swap')
            });
            if (typeof htmx !== 'undefined') {
                htmx.process(button);
                console.log('Reprocessed HTMX attributes on button click');
                htmx.trigger(button, 'click');
                setTimeout(() => {
                    if (!button.classList.contains('htmx-request')) {
                        console.warn('HTMX did not initiate request, falling back to manual fetch');
                        const url = button.getAttribute('hx-get');
                        const targetId = button.getAttribute('hx-target').replace('#', '');
                        const swap = button.getAttribute('hx-swap');
                        fetch(url)
                            .then(response => response.json())
                            .then(data => {
                                console.log('Manual fetch response:', data);
                                if (swap === 'innerHTML') {
                                    const target = document.getElementById(targetId);
                                    if (target) {
                                        if (targetId.startsWith('subcat-')) {
                                            const category = targetId.replace('subcat-', '');
                                            loadSubcatData(category, data);
                                        } else if (targetId.startsWith('common-')) {
                                            const categoryMatch = url.match(/category=([^&]+)/);
                                            const subcategoryMatch = url.match(/subcategory=([^&]+)/);
                                            if (categoryMatch && subcategoryMatch) {
                                                const category = decodeURIComponent(categoryMatch[1]);
                                                const subcategory = decodeURIComponent(subcategoryMatch[1]);
                                                loadCommonNames(category, subcategory, data);
                                            }
                                        } else if (targetId.startsWith('items-')) {
                                            target.innerHTML = JSON.stringify(data);
                                        }
                                    }
                                }
                            })
                            .catch(error => {
                                console.error('Manual fetch error:', error);
                            });
                    }
                }, 500);
            } else {
                console.error('HTMX not available during button click');
            }
            const keyMatch = button.getAttribute('hx-target')?.match(/#subcat-(.+)$/);
            if (keyMatch) {
                showLoading(keyMatch[1]);
            }
        });
    });

    // Direct click listener for print-btn debugging
    document.querySelectorAll('.print-btn').forEach(button => {
        button.addEventListener('click', (event) => {
            console.log('Direct click on print-btn:', button);
            console.log('Event details:', event);
        });
    });

    // Event delegation for print buttons
    document.body.addEventListener('click', (event) => {
        console.log('Click event on body:', event.target);
        const button = event.target.closest('.print-btn');
        if (button) {
            const level = button.getAttribute('data-print-level');
            const id = button.getAttribute('data-print-id');
            console.log(`Print button clicked: level=${level}, id=${id}`);
            printTable(level, id);
        } else {
            console.log('No print-btn found for click event on body');
            const closestTd = event.target.closest('td');
            if (closestTd) {
                console.log('Closest td content:', closestTd.innerHTML);
                const printBtn = closestTd.querySelector('.print-btn');
                console.log('Print button in td:', printBtn ? printBtn.outerHTML : 'None');
            }
        }
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
        // Process HTMX attributes on the newly loaded category table content
        const container = document.getElementById('category-table-body');
        if (container) {
            if (typeof htmx !== 'undefined') {
                htmx.process(container);
                console.log('HTMX processed category table body');
                // Debug HTMX-processed elements
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
                                <button class="btn btn-sm btn-info print-btn" data-print-level="Item" data-print-id="items-table-${targetId}">
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
            // Process HTMX attributes on the newly added content
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