// Cache the tab number globally to avoid repeated DOM queries
let cachedTabNum = '1'; // Default to '1' if h1 is not found or no number is present

function showLoading(key) {
    const loading = document.getElementById(`loading-${key}`);
    if (loading) loading.style.display = 'block';
}

function hideLoading(key) {
    const loading = document.getElementById(`loading-${key}`);
    if (loading) loading.style.display = 'none';
}

function sortTable(column, tableId) {
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
    const categoryTable = document.getElementById('category-table');
    if (categoryTable) {
        htmx.trigger('#category-table', 'htmx:load');
    } else {
        console.warn('Category table not found for refresh.');
    }
    setTimeout(() => { isRefreshing = false; }, 1000);
}

document.addEventListener('DOMContentLoaded', () => {
    // Cache the tab number on page load, but only on tab pages
    const h1Element = document.querySelector('h1');
    if (h1Element && window.location.pathname.startsWith('/tab/')) {
        const h1Text = h1Element.textContent.trim();
        const tabNumMatch = h1Text.match(/Tab\s+(\d+)/i); // Match "Tab 1", "Tab 2", etc.
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

    // Handle htmx:afterRequest to hide loading indicators
    document.body.addEventListener('htmx:afterRequest', (event) => {
        const targetId = event.detail.target.id;
        const catKey = targetId.replace('subcat-', '').replace('items-', '');
        hideLoading(catKey);
    });
});

document.body.addEventListener('htmx:afterSwap', (event) => {
    if (event.detail.target.id.startsWith('subcat-')) {
        const category = event.detail.target.id.replace('subcat-', '');
        const data = JSON.parse(event.detail.xhr.responseText);
        loadSubcatData(category, data);
    } else if (event.detail.target.id.startsWith('items-')) {
        const container = document.getElementById(event.detail.target.id);
        if (container) {
            container.style.display = 'block';
            const data = JSON.parse(event.detail.xhr.responseText);
            let html = `
                <table class="table table-bordered ms-3 mt-2" id="items-table-${event.detail.target.id}">
                    <thead>
                        <tr>
                            <th>Tag ID</th>
                            <th>Common Name</th>
                            <th>Bin Location</th>
                            <th>Status</th>
                            <th>Last Contract</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            if (data.length === 0) {
                html += `
                    <tr>
                        <td colspan="6">No items found for this subcategory.</td>
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
                            <td>
                                <button class="btn btn-sm btn-info" onclick="printTable('Item', 'items-table-${event.detail.target.id}')">
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
            applyFilters();
        } else {
            console.warn(`Container with ID '${event.detail.target.id}' not found.`);
        }
    }
});

function loadSubcatData(category, subcatData) {
    const container = document.getElementById(`subcat-${category.toLowerCase().replace(/[^a-z0-9-]/g, '_')}`);
    if (!container) {
        console.warn(`Container with ID 'subcat-${category.toLowerCase().replace(/[^a-z0-9-]/g, '_')}' not found.`);
        return;
    }
    container.style.display = 'block';
    let html = '<div class="ms-3">';
    
    subcatData.forEach(sub => {
        console.debug(`Rendering subcategory for ${category}: ${sub.subcategory}`); // Debug log
        const subId = `${category}_${sub.subcategory}`.toLowerCase().replace(/[^a-z0-9-]/g, '_');
        html += `
            <table class="table table-bordered mt-2" id="subcat-table-${subId}">
                <thead>
                    <tr>
                        <th>Subcategory</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>${sub.subcategory}</td>
                        <td>
                            <button class="btn btn-sm btn-secondary"
                                    hx-get="/tab/${cachedTabNum}/data?category=${encodeURIComponent(category)}&subcategory=${encodeURIComponent(sub.subcategory)}"
                                    hx-target="#items-${subId}"
                                    hx-swap="innerHTML"
                                    onclick="showLoading('${subId}')">
                                Load Items
                            </button>
                            <button class="btn btn-sm btn-info" onclick="printTable('Subcategory', 'subcat-table-${subId}')">
                                Print
                            </button>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="2">
                            <div id="common-${subId}" style="display:none;"></div>
                            <div id="items-${subId}" style="display:none;"></div>
                            <div id="loading-${subId}" style="display:none;" class="loading">Loading...</div>
                        </td>
                    </tr>
                </tbody>
            </table>
        `;
        
        sub.common_names.forEach(cn => {
            const cnId = `${subId}_${cn}`.toLowerCase().replace(/[^a-z0-9-]/g, '_');
            html += `
                <table class="table table-bordered ms-3 mt-2" id="common-table-${cnId}">
                    <thead>
                        <tr>
                            <th>Common Name</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>${cn}</td>
                            <td>
                                <button class="btn btn-sm btn-secondary"
                                        hx-get="/tab/${cachedTabNum}/data?category=${encodeURIComponent(category)}&subcategory=${encodeURIComponent(sub.subcategory)}&common_name=${encodeURIComponent(cn)}"
                                        hx-target="#items-${cnId}"
                                        hx-swap="innerHTML"
                                        onclick="showLoading('${cnId}')">
                                    Load Items
                                </button>
                                <button class="btn btn-sm btn-info" onclick="printTable('Common Name', 'common-table-${cnId}')">
                                    Print
                                </button>
                            </td>
                        </tr>
                        <tr>
                            <td colspan="2">
                                <div id="items-${cnId}" style="display:none;"></div>
                                <div id="loading-${cnId}" style="display:none;" class="loading">Loading...</div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            `;
        });
    });
    
    html += '</div>';
    container.innerHTML = html;
    applyFilters();
}