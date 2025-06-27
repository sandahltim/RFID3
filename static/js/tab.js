// app/static/js/tab.js
// tab.js version: 2025-06-27-v12
console.log('tab.js version: 2025-06-27-v12 loaded');

/**
 * Tab.js: Initializes tab-specific logic and handles printing.
 * Dependencies: common.js (for formatDateTime, printTable, renderPaginationControls).
 * Updated: 2025-06-27-v12
 * - Fixed SyntaxError in setupExpandCollapse (removed invalid characters).
 * - Ensured correct window.cachedTabNum setting for Tab 3 initialization.
 * - Modified fetchExpandableData to call fetchCommonNames for Tab 3.
 * - Preserved all existing functionality (printing, expandable sections).
 * - Line count: ~480 lines (+~10 lines for new logic, comments).
 */

/**
 * Format ISO date strings for consistency (fallback if common.js is not loaded)
 */
function formatDateTime(dateTimeStr) {
    console.log(`formatDateTime: Processing ${dateTimeStr} at ${new Date().toISOString()}`);
    if (typeof formatDate === 'function') {
        return formatDate(dateTimeStr);
    }
    console.warn(`formatDate not available, using fallback at ${new Date().toISOString()}`);
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
        console.error('formatDateTime error:', error, `at ${new Date().toISOString()}`);
        return 'N/A';
    }
}

/**
 * Fetch paginated data for expandable sections (Tabs 1, 3, 5)
 */
async function fetchExpandableData(tabNum, identifier, page, perPage) {
    console.log(`fetchExpandableData: tabNum=${tabNum}, identifier=${identifier}, page=${page}, perPage=${perPage} at ${new Date().toISOString()}`);
    if (tabNum === 3 && typeof fetchCommonNames === 'function') {
        console.log(`Calling fetchCommonNames for Tab 3, identifier=${identifier}, page=${page} at ${new Date().toISOString()}`);
        return fetchCommonNames(identifier, `common-table-${identifier.replace(/[^a-z0-9]/gi, '_')}-${page}`, page);
    }
    let url;
    if (tabNum === 3) {
        url = `/tab/${tabNum}/common_names?rental_class_id=${encodeURIComponent(identifier)}&page=${page}&per_page=${perPage}`;
    } else {
        url = `/tab/${tabNum}/common_names?contract_number=${encodeURIComponent(identifier)}&page=${page}&per_page=${perPage}`;
    }
    try {
        const response = await fetch(url);
        console.log(`fetchExpandableData: Fetch ${url}, status: ${response.status} at ${new Date().toISOString()}`);
        if (!response.ok) {
            throw new Error(`fetchExpandableData failed: ${response.status}`);
        }
        const data = await response.json();
        console.log('fetchExpandableData: Data received', JSON.stringify(data, null, 2), `at ${new Date().toISOString()}`);
        return data;
    } catch (error) {
        console.error('fetchExpandableData error:', error, `at ${new Date().toISOString()}`);
        return { common_names: [], total_items: 0 };
    }
}

/**
 * Update expandable table with new data
 */
function updateExpandableTable(tableId, data, page, perPage, tabNum, identifier) {
    console.log(`updateExpandableTable: tableId=${tableId}, page=${page}, perPage=${perPage}, tabNum=${tabNum}, identifier=${identifier} at ${new Date().toISOString()}`);
    const table = document.getElementById(tableId);
    if (!table) {
        console.warn(`updateExpandableTable: Table not found ${tableId} at ${new Date().toISOString()}`);
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

    if (typeof renderPaginationControls === 'function') {
        const paginationContainer = document.querySelector(`#pagination-${tableId}`);
        if (paginationContainer) {
            renderPaginationControls(paginationContainer, data.total_items, page, perPage, (newPage) => {
                fetchExpandableData(tabNum, identifier, newPage, perPage).then(newData => {
                    updateExpandableTable(tableId, newData, newPage, perPage, tabNum, identifier);
                });
            });
        }
    } else {
        console.error('updateExpandableTable: renderPaginationControls not defined at ${new Date().toISOString()}');
    }
}

/**
 * Handle expand/collapse for Tab 3 summary table
 */
function setupExpandCollapse() {
    console.log(`setupExpandCollapse: Initializing at ${new Date().toISOString()}`);
    document.querySelectorAll('.expandable').forEach(section => {
        section.classList.remove('expanded');
        section.classList.add('collapsed');
        section.style.display = 'none';
        section.style.opacity = '0';
        const row = section.closest('tr');
        const collapseBtn = row.querySelector('.collapse-btn');
        const expandBtn = row.querySelector('.expand-btn');
        if (collapseBtn && expandBtn) {
            collapseBtn.style.display = 'none';
            expandBtn.style.display = 'inline-block';
        } else {
            console.warn(`Expand/collapse buttons not found for section ${section.id} at ${new Date().toISOString()}`);
        }
    });
}

/**
 * Initialize the page
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log(`tab.js: DOMContentLoaded at ${new Date().toISOString()}`);
    try {
        let tabNum;
        const path = window.location.pathname;
        console.log(`Current path: ${path} at ${new Date().toISOString()}`);
        const pathMatch = path.match(/\/tab\/(\d+)/);
        if (pathMatch) {
            tabNum = parseInt(pathMatch[1], 10);
            console.log(`Tab number extracted from URL: ${tabNum} at ${new Date().toISOString()}`);
        } else if (path === '/' || path === '/home') {
            tabNum = 1;
            console.log('Home page detected, setting tabNum=1 at ${new Date().toISOString()}');
        } else {
            console.warn('No tab number found in URL, using default tab number 1 at ${new Date().toISOString()}');
            tabNum = 1;
        }
        window.cachedTabNum = tabNum;
        console.log(`Set window.cachedTabNum=${window.cachedTabNum} at ${new Date().toISOString()}`);

        // Initialize expand/collapse for Tab 3
        if (tabNum === 3) {
            setupExpandCollapse();
        }

        // Remove any existing click listeners to prevent duplicates
        document.removeEventListener('click', window.tabClickHandler);
        window.tabClickHandler = (event) => {
            console.log('Click event triggered at ${new Date().toISOString()}');
            const printBtn = event.target.closest('.print-btn');
            const printFullBtn = event.target.closest('.print-full-btn');
            const expandBtn = event.target.closest('.expand-btn');
            const collapseBtn = event.target.closest('.collapse-btn');

            if (printBtn) {
                event.preventDefault();
                event.stopPropagation();
                const level = printBtn.getAttribute('data-print-level');
                const id = printBtn.getAttribute('data-print-id');
                const commonName = printBtn.getAttribute('data-common-name');
                const category = printBtn.getAttribute('data-category');
                const subcategory = printBtn.getAttribute('data-subcategory');
                printTable(level, id, commonName, category, subcategory);
            }

            if (printFullBtn) {
                event.preventDefault();
                event.stopPropagation();
                const commonName = printFullBtn.getAttribute('data-common-name');
                const category = printFullBtn.getAttribute('data-category');
                const subcategory = printFullBtn.getAttribute('data-subcategory');
                printFullItemList(category, subcategory, commonName);
            }

            // Handle expandable sections for Tabs 1, 3, 5 only
            if (expandBtn && [1, 3, 5].includes(tabNum)) {
                console.log('Expand button clicked:', {
                    identifier: expandBtn.getAttribute('data-identifier'),
                    targetId: expandBtn.getAttribute('data-target-id')
                }, `at ${new Date().toISOString()}`);
                const row = expandBtn.closest('tr');
                const nextRow = row.nextElementSibling;
                const expandable = nextRow.querySelector('.expandable');
                if (!expandable) {
                    console.warn('Expandable section not found at ${new Date().toISOString()}');
                    return;
                }

                const identifier = expandBtn.getAttribute('data-identifier');
                const targetId = expandBtn.getAttribute('data-target-id');

                if (!identifier || !targetId) {
                    console.warn('Identifier or target ID missing at ${new Date().toISOString()}');
                    return;
                }

                if (expandable.classList.contains('collapsed')) {
                    expandable.classList.remove('collapsed');
                    expandable.classList.add('expanded');
                    expandable.style.display = 'block';
                    expandable.style.opacity = '1';
                    const collapseBtn = row.querySelector('.collapse-btn');
                    const expandBtn = row.querySelector('.expand-btn');
                    if (collapseBtn && expandBtn) {
                        collapseBtn.style.display = 'inline-block';
                        expandBtn.style.display = 'none';
                    }

                    const tableId = expandable.querySelector('.common-table')?.id;
                    if (!tableId) {
                        console.warn('Table ID not found in expandable section at ${new Date().toISOString()}');
                    }
                    fetchExpandableData(tabNum, identifier, 1, 20).then(data => {
                        if (tableId) {
                            updateExpandableTable(tableId, data, 1, 20, tabNum, identifier);
                        }
                    });
                }
            }

            if (collapseBtn && [1, 3, 5].includes(tabNum)) {
                console.log('Collapse button clicked:', {
                    targetId: collapseBtn.getAttribute('data-collapse-target')
                }, `at ${new Date().toISOString()}`);
                const targetId = collapseBtn.getAttribute('data-collapse-target');
                const section = document.getElementById(targetId);
                if (section) {
                    section.classList.remove('expanded');
                    section.classList.add('collapsed');
                    section.style.display = 'none';
                    section.style.opacity = '0';
                    const row = collapseBtn.closest('tr');
                    const expandBtn = row.querySelector('.expand-btn');
                    if (expandBtn && collapseBtn) {
                        expandBtn.style.display = 'inline-block';
                        collapseBtn.style.display = 'none';
                    }
                }
            }
        };
        document.addEventListener('click', window.tabClickHandler);
    } catch (error) {
        console.error('Initialization error:', error, `at ${new Date().toISOString()}`);
    }
}

/**
 * Print a table (Contract, Common Name, or Item level)
 */
async function printTable(level, id, commonName = null, category = null, subcategory = null) {
    console.log(`Printing table: ${level}, ID: ${id}, Common Name: ${commonName}, Category: ${category}, Subcategory: ${subcategory} at ${new Date().toISOString()}`);
    const element = document.getElementById(id);
    if (!element) {
        console.error(`Element with ID ${id} not found for printing at ${new Date().toISOString()}`);
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
            console.error('Error fetching contract date:', error, `at ${new Date().toISOString()}`);
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
        if (!response.ok) {
            console.error(`Failed to fetch data for printing: ${response.status} at ${new Date().toISOString()}`);
            return;
        }
        const data = await response.json();
        const items = data.items || [];

        const statusCounts = {};
        items.forEach(item => {
            const status = item.status || 'Unknown';
            statusCounts[status] = (statusCounts[status] || 0) + 1;
        });

        const readyToRentCount = statusCounts['Ready to Rent'] || 0;

        tableWrapper = document.createElement('table');
        tableWrapper.className = 'table table-bordered';
        if (tabNum == 1 || tabNum == 5) {
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
                    <tr>
                        <td>${commonName}</td>
                        <td>Ready to Rent (Total Available)</td>
                        <td>${readyToRentCount}</td>
                    </tr>
                </tbody>
            `;
        } else {
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
        }
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
            console.error('Error fetching all common names for print:', error, `at ${new Date().toISOString()}`);
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
                const url = `/tab/${tabNum}/common_names?${tabNum === 3 ? 'rental_class_id' : 'contract_number'}=${encodeURIComponent(contractNumber)}`;
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
                                <td>${common.is_hand_counted ? 'N/A' : common.total_items_inventory}</td>
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
        console.error('Failed to open print window. Please allow popups at ${new Date().toISOString()}.');
        return;
    }
    printWindow.document.write(printContent);
    printWindow.document.close();
}

/**
 * Remove "Total Items in Inventory" column for Tabs 2 and 4
 */
function removeTotalItemsInventoryColumn(table, tabNum) {
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
 * Print full item list
 */
async function printFullItemList(category, subcategory, commonName) {
    console.log(`Printing full item list for Category: ${category}, Subcategory: ${subcategory}, Common Name: ${commonName} at ${new Date().toISOString()}`);
    const tabNum = window.cachedTabNum || 1;
    const tabName = tabNum == 2 ? 'Open Contracts' : tabNum == 4 ? 'Laundry Contracts' : tabNum == 5 ? 'Resale/Rental Packs' : tabNum == 3 ? 'Service' : `Tab ${tabNum}`;

    const normalizedCommonName = normalizeCommonName(commonName);
    console.log(`Normalized Common Name: ${normalizedCommonName} at ${new Date().toISOString()}`);

    const url = `/tab/${tabNum}/full_items_by_rental_class?category=${encodeURIComponent(category)}&subcategory=${subcategory ? encodeURIComponent(subcategory) : 'null'}&common_name=${encodeURIComponent(normalizedCommonName)}`;
    const response = await fetch(url);
    if (!response.ok) {
        console.error(`Failed to fetch full item list: ${response.status} at ${new Date().toISOString()}`);
        return;
    }
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
        console.error('Failed to open print window. Please allow popups at ${new Date().toISOString()}.');
        return;
    }
    printWindow.document.write(printContent);
    printWindow.document.close();
}