console.log('tab.js version: 2025-05-23-v2 loaded');

/**
 * Tab.js: Initializes tab-specific logic and handles printing.
 * Dependencies: common.js (for formatDate, printTable).
 * Updated: Added robust tab detection and debug logging.
 */

/**
 * Format ISO date strings for consistency (fallback if common.js is not loaded)
 */
function formatDateTime(dateTimeStr) {
    console.log(`formatDateTime: dateTimeStr=${dateTimeStr}`);
    if (typeof formatDate === 'function') {
        return formatDate(dateTimeStr);
    }
    console.warn('formatDate not found, using fallback');
    if (!dateTimeStr || dateTimeStr === 'N/A') return 'N/A';
    try {
        const date = new Date(dateTimeStr);
        if (isNaN(date.getTime())) return 'N/A';
        return date.toLocaleString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        });
    } catch (error) {
        console.error('Error formatting date:', dateTimeStr, error);
        return 'N/A';
    }
}

/**
 * Refresh the current tab
 */
function refreshTab() {
    console.log('refreshTab: Reloading page');
    window.location.reload();
}

/**
 * Remove "Total Items in Inventory" column for Tabs 2 and 4
 */
function removeTotalItemsInventoryColumn(table, tabNum) {
    console.log(`removeTotalItemsInventoryColumn: tabNum=${tabNum}`);
    if (tabNum == 2 || tabNum == 4) {
        const headers = table.querySelectorAll('th');
        const rows = table.querySelectorAll('tbody tr');
        headers.forEach((th, index) => {
            if (th.textContent.trim() === 'Total Items in Inventory') {
                th.remove();
                rows.forEach(row => {
                    const cell = row.cells[index];
                    if (cell) cell.remove();
                });
            }
        });
    }
}

/**
 * Normalize common name by removing quotes and extra spaces
 */
function normalizeCommonName(commonName) {
    console.log(`normalizeCommonName: commonName=${commonName}`);
    return commonName.replace(/['"]/g, '').replace(/\s+/g, ' ').trim();
}

/**
 * Initialize pagination for a table
 */
function initializePagination(tableId, totalItems, page = 1, perPage = 20, fetchFunction) {
    console.log(`initializePagination: tableId=${tableId}, totalItems=${totalItems}, page=${page}, perPage=${perPage}`);
    const table = document.getElementById(tableId);
    const paginationContainer = document.querySelector(`#pagination-${tableId}`);
    if (!table || !paginationContainer) {
        console.warn(`Pagination elements not found for table: ${tableId}`);
        return;
    }

    renderPaginationControls(paginationContainer, totalItems, page, perPage, (newPage) => {
        fetchFunction(newPage, perPage);
    });
}

/**
 * Fetch paginated data for expandable sections (Tabs 1, 2, 4, 5)
 */
async function fetchExpandableData(tabNum, contractNumber, page, perPage) {
    console.log(`fetchExpandableData: tabNum=${tabNum}, contractNumber=${contractNumber}, page=${page}, perPage=${perPage}`);
    const url = `/tab/${tabNum}/common_names?contract_number=${encodeURIComponent(contractNumber)}&page=${page}&per_page=${perPage}`;
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Failed to fetch expandable data: ${response.status}`);
        }
        const data = await response.json();
        console.log(`fetchExpandableData: Data received`, data);
        return data;
    } catch (error) {
        console.error(`Error fetching expandable data for tab ${tabNum}:`, error);
        return { common_names: [], total_items: 0 };
    }
}

/**
 * Update expandable table with new data
 */
function updateExpandableTable(tableId, data, page, perPage, tabNum, contractNumber) {
    console.log(`updateExpandableTable: tableId=${tableId}, page=${page}, perPage=${perPage}, tabNum=${tabNum}, contractNumber=${contractNumber}`);
    const table = document.getElementById(tableId);
    if (!table) {
        console.warn(`Table not found: ${tableId}`);
        return;
    }

    const tbody = table.querySelector('tbody');
    tbody.innerHTML = data.common_names.map(common => `
        <tr>
            <td>${common.name}</td>
            <td>${common.on_contracts}</td>
            <td>${common.is_hand_counted ? 'N/A' : common.total_items_inventory}</td>
        </tr>
    `).join('');

    initializePagination(tableId, data.total_items, page, perPage, (newPage) => {
        fetchExpandableData(tabNum, contractNumber, newPage, perPage).then(newData => {
            updateExpandableTable(tableId, newData, newPage, perPage, tabNum, contractNumber);
        });
    });
}

/**
 * Print a table (Contract, Common Name, or Item level)
 */
async function printTable(level, id, commonName = null, category = null, subcategory = null) {
    console.log(`printTable: level=${level}, id=${id}, commonName=${commonName}, category=${category}, subcategory=${subcategory}`);
    const element = document.getElementById(id);
    if (!element) {
        console.error(`Element with ID ${id} not found for printing`);
        return;
    }

    const tabNum = window.cachedTabNum || 1;
    const tabName = tabNum == 2 ? 'Open Contracts' : tabNum == 4 ? 'Laundry Contracts' : tabNum == 5 ? 'Resale/Rental Packs' : tabNum == 3 ? 'Service' : `Tab ${tabNum}`;

    let contractNumber = '';
    if (level === 'Contract') {
        if (id.startsWith('common-')) {
            contractNumber = id.replace('common-', '');
        } else {
            const contractCell = element.querySelector('td:first-child');
            contractNumber = contractCell ? contractCell.textContent.trim() : '';
        }
    } else {
        contractNumber = category || '';
    }

    let contractDate = 'N/A';
    if (contractNumber && (tabNum == 2 || tabNum == 4)) {
        try {
            const response = await fetch(`/get_contract_date?contract_number=${encodeURIComponent(contractNumber)}`);
            const data = await response.json();
            contractDate = data.date ? formatDateTime(data.date) : 'N/A';
        } catch (error) {
            console.error('Error fetching contract date:', error);
        }
    }

    let printElement;
    let tableWrapper;

    if (level === 'Common Name' && commonName && category) {
        let url = `/tab/${tabNum}/data?common_name=${encodeURIComponent(commonName)}`;
        if (tabNum == 2 || tabNum == 4) {
            url += `&contract_number=${encodeURIComponent(category)}`;
        } else {
            url += `&category=${encodeURIComponent(category)}`;
        }
        if (subcategory) {
            url += `&subcategory=${encodeURIComponent(subcategory)}`;
        }
        const response = await fetch(url);
        const data = await response.json();
        const items = data.items || [];

        const statusCounts = {};
        items.forEach(item => {
            const status = item.status || 'Unknown';
            statusCounts[status] = (statusCounts[status] || 0) + 1;
        });

        tableWrapper = document.createElement('table');
        tableWrapper.className = 'table table-bordered';
        tableWrapper.innerHTML = `
            <thead>
                <tr>
                    <th>Common Name</th>
                    <th>Status</th>
                    <th>Count</th>
                </tr>
            </thead>
            <tbody>
                ${Object.entries(statusCounts).map(([status, count]) => `
                    <tr>
                        <td>${commonName}</td>
                        <td>${status}</td>
                        <td>${count}</td>
                    </tr>
                `).join('')}
            </tbody>
        `;
    } else if (level === 'Contract' && tabNum === 4) {
        const url = `/tab/4/common_names?contract_number=${encodeURIComponent(contractNumber)}&all=true`;
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`Failed to fetch all common names: ${response.status}`);
            }
            const data = await response.json();
            const commonNames = data.common_names || [];

            tableWrapper = document.createElement('table');
            tableWrapper.className = 'table table-bordered';
            tableWrapper.innerHTML = `
                <thead>
                    <tr>
                        <th>Common Name</th>
                        <th>Items on Contract</th>
                        <th>Total Items in Inventory</th>
                    </tr>
                </thead>
                <tbody>
                    ${commonNames.map(common => `
                        <tr>
                            <td>${common.name}</td>
                            <td>${common.on_contracts}</td>
                            <td>${common.is_hand_counted ? 'N/A' : common.total_items_inventory}</td>
                        </tr>
                    `).join('')}
                </tbody>
            `;
        } catch (error) {
            console.error('Error fetching all common names for print:', error);
            tableWrapper = document.createElement('table');
            tableWrapper.className = 'table table-bordered';
            tableWrapper.innerHTML = `<tr><td colspan="3">Error loading common names: ${error.message}</td></tr>`;
        }
    } else {
        printElement = element.cloneNode(true);

        if (level === 'Contract') {
            let commonTable;
            if (id.startsWith('common-')) {
                if (printElement.classList.contains('expanded')) {
                    commonTable = printElement.querySelector('.common-table');
                }
            } else {
                const row = element.closest('tr');
                if (row) {
                    const nextRow = row.nextElementSibling;
                    if (nextRow) {
                        const expandedContent = nextRow.querySelector('.expandable.expanded');
                        if (expandedContent) {
                            commonTable = expandedContent.querySelector('.common-table');
                        }
                    }
                }
            }

            if (commonTable) {
                tableWrapper = commonTable.cloneNode(true);
            } else {
                const url = `/tab/${tabNum}/common_names?contract_number=${encodeURIComponent(contractNumber)}`;
                const response = await fetch(url);
                const data = await response.json();
                const commonNames = data.common_names || [];

                tableWrapper = document.createElement('table');
                tableWrapper.className = 'table table-bordered';
                tableWrapper.innerHTML = `
                    <thead>
                        <tr>
                            <th>Common Name</th>
                            <th>Items on Contract</th>
                            <th>Total Items in Inventory</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${commonNames.map(common => `
                            <tr>
                                <td>${common.name}</td>
                                <td>${common.on_contracts}</td>
                                <td>${common.total_items_inventory}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                `;
            }
        } else {
            tableWrapper = printElement;
        }

        removeTotalItemsInventoryColumn(tableWrapper, tabNum);

        tableWrapper.querySelectorAll('.btn, .loading, .expandable.collapsed, .pagination-controls, .filter-sort-controls, .filter-row').forEach(el => el.remove());
    }

    tableWrapper.querySelectorAll('br').forEach(br => br.remove());

    const printContent = `
        <html>
            <head>
                <title>Broadway Tent and Event - ${tabName} - ${level}</title>
                <link href="/static/css/style.css" rel="stylesheet">
                <style>
                    body {
                        font-family: 'Roboto', sans-serif;
                        margin: 20px;
                        color: #333;
                    }
                    .print-header {
                        text-align: center;
                        margin-bottom: 40px;
                    }
                    .print-header h1 {
                        font-size: 28px;
                        margin: 0;
                    }
                    .print-header h2 {
                        font-size: 20px;
                        margin: 5px 0;
                    }
                    .print-header p {
                        font-size: 14px;
                        color: #666;
                        margin: 5px 0;
                    }
                    table {
                        border-collapse: collapse;
                        width: 100%;
                        margin-top: 20px;
                    }
                    th, td {
                        border: 1px solid #ccc;
                        padding: 12px;
                        text-align: center;
                        font-size: 14px;
                        white-space: normal;
                        word-wrap: break-word;
                    }
                    th {
                        background-color: #f2f2f2;
                        font-weight: bold;
                    }
                    td {
                        vertical-align: middle;
                    }
                    .hidden {
                        display: none;
                    }
                    .common-level {
                        margin-left: 1rem;
                        background-color: #e9ecef;
                        padding: 0.5rem;
                        border-left: 3px solid #28a745;
                        margin-top: 10px;
                    }
                    .item-level-wrapper {
                        margin-left: 1rem;
                        background-color: #dee2e6;
                        padding: 0.5rem;
                        border-left: 3px solid #dc3545;
                        margin-top: 10px;
                    }
                    .signature-line {
                        margin-top: 40px;
                        border-top: 1px solid #000;
                        width: 300px;
                        text-align: center;
                        padding-top: 10px;
                        font-size: 14px;
                    }
                    @media print {
                        body {
                            margin: 0;
                        }
                        .print-header {
                            position: static;
                            width: 100%;
                            margin-bottom: 20px;
                        }
                        table {
                            page-break-inside: auto;
                        }
                        tr {
                            page-break-inside: avoid;
                            page-break-after: auto;
                        }
                        th, td {
                            font-size: 8pt;
                            padding: 4px 8px;
                            word-break: break-word;
                            text-align: center;
                        }
                    }
                </style>
            </head>
            <body>
                <div class="print-header">
                    <h1>Broadway Tent and Event</h1>
                    <h2>${tabName}</h2>
                    ${contractNumber ? `<p>Contract Number: ${contractNumber}</p>` : ''}
                    ${contractDate !== 'N/A' ? `<p>Contract Created: ${contractDate}</p>` : ''}
                    ${commonName ? `<p>Common Name: ${commonName}</p>` : ''}
                    <p>Printed on: ${new Date().toLocaleString()}</p>
                </div>
                <div>
                    ${tableWrapper.outerHTML}
                </div>
                <div class="signature-line">
                    Signature: _______________________________
                </div>
                <script>
                    window.onload = function() {
                        window.print();
                        window.onafterprint = function() {
                            window.close();
                        };
                    };
                </script>
            </body>
        </html>
    `;

    const printWindow = window.open('', '_blank');
    if (!printWindow) {
        console.error('Failed to open print window. Please allow popups.');
        return;
    }
    printWindow.document.write(printContent);
    printWindow.document.close();
}

/**
 * Print full item list
 */
async function printFullItemList(category, subcategory, commonName) {
    console.log(`printFullItemList: category=${category}, subcategory=${subcategory}, commonName=${commonName}`);
    const tabNum = window.cachedTabNum || 1;
    const tabName = tabNum == 2 ? 'Open Contracts' : tabNum == 4 ? 'Laundry Contracts' : tabNum == 5 ? 'Resale/Rental Packs' : tabNum == 3 ? 'Service' : `Tab ${tabNum}`;

    const normalizedCommonName = normalizeCommonName(commonName);
    console.log(`Normalized Common Name: ${normalizedCommonName}`);

    const url = `/tab/${tabNum}/full_items_by_rental_class?category=${encodeURIComponent(category)}&subcategory=${subcategory ? encodeURIComponent(subcategory) : 'null'}&common_name=${encodeURIComponent(normalizedCommonName)}`;
    const response = await fetch(url);
    const data = await response.json();
    const items = data.items || [];

    const tableWrapper = document.createElement('table');
    tableWrapper.className = 'table table-bordered';
    const headers = ['Tag ID', 'Common Name', 'Rental Class Num', 'Bin Location', 'Status', 'Last Contract', 'Last Scanned Date', 'Quality', 'Notes'];
    tableWrapper.innerHTML = `
        <thead>
            <tr>
                ${headers.map(header => `<th>${header}</th>`).join('')}
            </tr>
        </thead>
        <tbody>
            ${items.map(item => `
                <tr>
                    <td>${item.tag_id}</td>
                    <td>${item.common_name}</td>
                    <td>${item.rental_class_num || 'N/A'}</td>
                    <td>${item.bin_location || 'N/A'}</td>
                    <td>${item.status}</td>
                    <td>${item.last_contract_num || 'N/A'}</td>
                    <td>${formatDateTime(item.last_scanned_date)}</td>
                    <td>${item.quality || 'N/A'}</td>
                    <td>${item.notes || 'N/A'}</td>
                </tr>
            `).join('')}
        </tbody>
    `;

    const printContent = `
        <html>
            <head>
                <title>Broadway Tent and Event - ${tabName} - Full Item List</title>
                <link href="/static/css/style.css" rel="stylesheet">
                <style>
                    body {
                        font-family: 'Roboto', sans-serif;
                        margin: 20px;
                        color: #333;
                    }
                    .print-header {
                        text-align: center;
                        margin-bottom: 40px;
                    }
                    .print-header h1 {
                        font-size: 28px;
                        margin: 0;
                    }
                    .print-header h2 {
                        font-size: 20px;
                        margin: 5px 0;
                    }
                    .print-header p {
                        font-size: 14px;
                        color: #666;
                        margin: 5px 0;
                    }
                    table {
                        border-collapse: collapse;
                        width: 100%;
                        margin-top: 20px;
                    }
                    th, td {
                        border: 1px solid #ccc;
                        padding: 8px;
                        text-align: center;
                        font-size: 12px;
                        white-space: normal;
                        word-wrap: break-word;
                    }
                    th {
                        background-color: #f2f2f2;
                        font-weight: bold;
                    }
                    td {
                        vertical-align: middle;
                    }
                    .signature-line {
                        margin-top: 40px;
                        border-top: 1px solid #000;
                        width: 300px;
                        text-align: center;
                        padding-top: 10px;
                        font-size: 14px;
                    }
                    @media print {
                        body {
                            margin: 0;
                        }
                        .print-header {
                            position: static;
                            width: 100%;
                            margin-bottom: 20px;
                        }
                        table {
                            page-break-inside: auto;
                        }
                        tr {
                            page-break-inside: avoid;
                            page-break-after: auto;
                        }
                        th, td {
                            font-size: 8pt;
                            padding: 4px 8px;
                            word-break: break-word;
                            text-align: center;
                        }
                    }
                </style>
            </head>
            <body>
                <div class="print-header">
                    <h1>Broadway Tent and Event</h1>
                    <h2>${tabName}</h2>
                    <p>Common Name: ${commonName}</p>
                    <p>Printed on: ${new Date().toLocaleString()}</p>
                </div>
                <div>
                    ${tableWrapper.outerHTML}
                </div>
                <div class="signature-line">
                    Signature: _______________________________
                </div>
                <script>
                    window.onload = function() {
                        window.print();
                        window.onafterprint = function() {
                            window.close();
                        };
                    };
                </script>
            </body>
        </html>
    `;

    const printWindow = window.open('', '_blank');
    if (!printWindow) {
        console.error('Failed to open print window. Please allow popups.');
        return;
    }
    printWindow.document.write(printContent);
    printWindow.document.close();
}

/**
 * Initialize the page
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('tab.js: DOMContentLoaded');
    try {
        let tabNum;
        const path = window.location.pathname;
        console.log(`Current path: ${path}`);
        const pathMatch = path.match(/\/tab\/(\d+)/);
        if (pathMatch) {
            tabNum = parseInt(pathMatch[1], 10);
            console.log(`Tab number extracted from URL: ${tabNum}`);
        } else if (path === '/' || path === '/home') {
            tabNum = 1;
            console.log('Home page detected, setting tabNum=1');
        } else {
            console.warn('No tab number found in URL, using default tab number 1.');
            tabNum = 1;
        }
        window.cachedTabNum = tabNum;
        console.log(`Set window.cachedTabNum=${window.cachedTabNum}`);

        document.addEventListener('click', (event) => {
            console.log('Click event triggered');
            const printBtn = event.target.closest('.print-btn');
            const printFullBtn = event.target.closest('.print-full-btn');
            const expandBtn = event.target.closest('.expand-btn');

            if (printBtn) {
                const level = printBtn.getAttribute('data-print-level');
                const id = printBtn.getAttribute('data-print-id');
                const commonName = printBtn.getAttribute('data-common-name');
                const category = printBtn.getAttribute('data-category');
                const subcategory = printBtn.getAttribute('data-subcategory');
                printTable(level, id, commonName, category, subcategory);
            }

            if (printFullBtn) {
                const commonName = printFullBtn.getAttribute('data-common-name');
                const category = printFullBtn.getAttribute('data-category');
                const subcategory = printFullBtn.getAttribute('data-subcategory');
                printFullItemList(category, subcategory, commonName);
            }

            // Handle expandable sections for Tabs 1, 2, 4, 5 (not Tab 3)
            if (expandBtn && tabNum !== 3) {
                console.log('Expand button clicked:', {
                    contractNumber: expandBtn.getAttribute('data-contract-number'),
                    targetId: expandBtn.getAttribute('data-target-id')
                });
                const row = expandBtn.closest('tr');
                const nextRow = row.nextElementSibling;
                const expandable = nextRow.querySelector('.expandable');
                if (!expandable) {
                    console.warn('Expandable section not found for row');
                    return;
                }
                const tableId = expandable.querySelector('.common-table')?.id;
                const contractNumber = expandBtn.getAttribute('data-contract-number');

                if (!tableId || !contractNumber) {
                    console.warn('Table ID or contract number missing for expandable section');
                    return;
                }

                if (expandable.classList.contains('collapsed')) {
                    expandable.classList.remove('collapsed');
                    expandable.classList.add('expanded');
                    fetchExpandableData(tabNum, contractNumber, 1, 20).then(data => {
                        updateExpandableTable(tableId, data, 1, 20, tabNum, contractNumber);
                    });
                } else {
                    expandable.classList.remove('expanded');
                    expandable.classList.add('collapsed');
                }
            }
        });
    } catch (error) {
        console.error('Error initializing tab.js:', error);
    }
});