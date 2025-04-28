console.log('tab.js loaded, cachedTabNum:', window.cachedTabNum);

// Note: Common function - will be moved to common.js during split
function formatDateTime(dateTimeStr) {
    return formatDate(dateTimeStr); // Use formatDate from common.js for consistency
}

// Note: Common function - will be moved to common.js during split
function refreshTab() {
    window.location.reload();
}

// Note: Common function - will be moved to tab1_5.js during split
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

// Normalize common name by removing quotes and extra spaces
function normalizeCommonName(commonName) {
    return commonName.replace(/['"]/g, '').replace(/\s+/g, ' ').trim();
}

// Note: Common function - will be moved to tab1_5.js during split
async function printTable(level, id, commonName = null, category = null, subcategory = null) {
    console.log(`Printing table: ${level}, ID: ${id}, Common Name: ${commonName}, Category: ${category}, Subcategory: ${subcategory}`);
    const element = document.getElementById(id);
    if (!element) {
        console.error(`Element with ID ${id} not found for printing`);
        return;
    }

    const tabNum = window.cachedTabNum || 1;
    const tabName = tabNum == 2 ? 'Open Contracts' : tabNum == 4 ? 'Laundry Contracts' : tabNum == 5 ? 'Resale/Rental Packs' : `Tab ${tabNum}`;

    let contractNumber = '';
    if (level === 'Contract') {
        // For contract level, the ID might be 'category-table' or 'common-<contract_number>'
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
    } else {
        printElement = element.cloneNode(true);

        if (level === 'Contract') {
            let commonTable;
            if (id.startsWith('common-')) {
                // Check if the common table is expanded
                if (printElement.classList.contains('expanded')) {
                    commonTable = printElement.querySelector('.common-table');
                }
            } else {
                // Find the corresponding expandable section
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
                // Fetch the common names data if not expanded
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

        // Remove buttons and other interactive elements
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
                            font-size: 8pt; /* Reduced font size for print */
                            padding: 4px 8px; /* Reduced padding for print */
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

// Note: Common function - will be moved to tab1_5.js during split
async function printFullItemList(category, subcategory, commonName) {
    console.log(`Printing full item list for Category: ${category}, Subcategory: ${subcategory}, Common Name: ${commonName}`);
    const tabNum = window.cachedTabNum || 1;
    const tabName = tabNum == 2 ? 'Open Contracts' : tabNum == 4 ? 'Laundry Contracts' : tabNum == 5 ? 'Resale/Rental Packs' : `Tab ${tabNum}`;

    // Normalize the commonName to remove quotes and extra spaces
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
                            font-size: 8pt; /* Reduced font size for print */
                            padding: 4px 8px; /* Reduced padding for print */
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

// Note: Common function - will be moved to tab1_5.js during split
document.addEventListener('DOMContentLoaded', () => {
    console.log('Document loaded, initializing script');

    let tabNum;
    const pathMatch = window.location.pathname.match(/\/tab\/(\d+)/);
    if (pathMatch) {
        tabNum = parseInt(pathMatch[1], 10);
    } else if (window.location.pathname === '/') {
        tabNum = 1;
    } else {
        console.warn('No tab number found in URL, using default tab number 1.');
        tabNum = 1;
    }

    window.cachedTabNum = tabNum;

    document.addEventListener('click', (event) => {
        const printBtn = event.target.closest('.print-btn');
        const printFullBtn = event.target.closest('.print-full-btn');

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
    });
});