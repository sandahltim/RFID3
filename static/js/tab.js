console.log('tab.js loaded, cachedTabNum:', window.cachedTabNum);

// Define applyFilters immediately to ensure availability
window.applyFilters = function() {
    console.log('Applying filters');
    const textQuery = document.getElementById('category-filter') ? document.getElementById('category-filter').value.toLowerCase() : document.getElementById('searchInput') ? document.getElementById('searchInput').value.toLowerCase() : '';
    const categoryFilter = document.getElementById('categoryFilter') ? document.getElementById('categoryFilter').value.toLowerCase() : '';
    const statusFilter = document.getElementById('statusFilter') ? document.getElementById('statusFilter').value.toLowerCase() : '';
    const binLocationFilter = document.getElementById('binFilter') ? document.getElementById('binFilter').value.toLowerCase() : '';

    const tables = document.querySelectorAll('table');
    tables.forEach(table => {
        if (table.id !== 'category-table') {
            console.log(`Skipping filter application for table: ${table.id}`);
            return;
        }

        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            if (row.querySelector('.expandable')) {
                return;
            }

            const text = Array.from(row.children).map(cell => cell.textContent.toLowerCase()).join(' ');
            const categoryCell = row.querySelector('td:first-child') ? row.querySelector('td:first-child').textContent.toLowerCase() : '';
            const statusCell = row.cells[3] ? row.cells[3].textContent.toLowerCase() : '';
            const binLocationCell = row.cells[2] ? row.cells[2].textContent.toLowerCase() : '';

            const matchesText = text.includes(textQuery);
            const matchesCategory = !categoryFilter || categoryCell.includes(categoryFilter);
            const matchesStatus = !statusFilter || statusCell.includes(statusFilter);
            const matchesBinLocation = !binLocationFilter || binLocationCell.includes(binLocationFilter);

            row.style.display = (matchesText && matchesCategory && matchesStatus && matchesBinLocation) ? '' : 'none';
        });
    });
};

// Refresh table function
function refreshTab() {
    window.location.reload();
}

// Function to remove "Total Items in Inventory" column from a table
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

// Print table function
async function printTable(level, id, commonName = null, category = null, subcategory = null) {
    console.log(`Printing table: ${level}, ID: ${id}, Common Name: ${commonName}, Category: ${category}, Subcategory: ${subcategory}`);
    const element = document.getElementById(id);
    if (!element) {
        console.error(`Element with ID ${id} not found for printing`);
        return;
    }

    const tabNum = window.cachedTabNum || 1;
    const tabName = tabNum == 2 ? 'Open Contracts' : tabNum == 4 ? 'Laundry Contracts' : `Tab ${tabNum}`;

    let contractNumber = '';
    if (level === 'Contract') {
        const contractCell = element.querySelector('td:first-child');
        contractNumber = contractCell ? contractCell.textContent.trim() : '';
    }

    let contractDate = 'N/A';
    if (contractNumber && (tabNum == 2 || tabNum == 4)) {
        try {
            const response = await fetch(`/get_contract_date?contract_number=${encodeURIComponent(contractNumber)}`);
            const data = await response.json();
            contractDate = data.date ? new Date(data.date).toLocaleString() : 'N/A';
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
        console.log('Fetching items for print aggregate:', url);
        const response = await fetch(url);
        const data = await response.json();
        console.log('Print aggregate items response:', data);
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
            const header = document.getElementById('category-table-header');
            if (header) {
                tableWrapper = document.createElement('table');
                tableWrapper.className = 'table table-bordered';
                tableWrapper.appendChild(header.cloneNode(true));
                const tbody = document.createElement('tbody');
                tbody.appendChild(printElement);
                tableWrapper.appendChild(tbody);
            } else {
                tableWrapper = printElement;
            }
        } else {
            tableWrapper = printElement;
        }

        removeTotalItemsInventoryColumn(tableWrapper, tabNum);

        const row = element.closest('tr');
        if (row) {
            const nextRow = row.nextElementSibling;
            if (nextRow) {
                const expandedContent = nextRow.querySelector('.expandable.expanded');
                if (expandedContent) {
                    const expandedClone = expandedContent.cloneNode(true);
                    expandedClone.querySelectorAll('.btn, .loading, .expandable.collapsed, .pagination-controls, .filter-sort-controls').forEach(el => el.remove());
                    const nestedTables = expandedClone.querySelectorAll('table');
                    nestedTables.forEach(nestedTable => {
                        removeTotalItemsInventoryColumn(nestedTable, tabNum);
                    });
                    const expandedWrapper = document.createElement('div');
                    expandedWrapper.appendChild(expandedClone);
                    tableWrapper.appendChild(expandedWrapper);
                }
            }
        }

        tableWrapper.querySelectorAll('.btn, .loading, .expandable.collapsed, .pagination-controls, .filter-sort-controls').forEach(el => el.remove());
    }

    tableWrapper.querySelectorAll('br').forEach(br => br.remove());

    const printContent = `
        <html>
            <head>
                <title>RFID Dashboard - ${tabName} - ${level}</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        margin: 20px;
                        color: #333;
                    }
                    .print-header {
                        text-align: center;
                        margin-bottom: 40px;
                    }
                    .EDF {
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
                        text-align: left;
                        font-size: 14px;
                        white-space: normal;
                        word-wrap: break-word;
                        min-width: 150px;
                    }
                    th {
                        background-color: #f2f2f2;
                        font-weight: bold;
                    }
                    td {
                        vertical-align: top;
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
                        console.log('Print window loaded, content:', document.body.innerHTML);
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
    console.log('Print triggered successfully');
}

async function printFullItemList(category, subcategory, commonName) {
    console.log(`Printing full item list for Category: ${category}, Subcategory: ${subcategory}, Common Name: ${commonName}`);
    const tabNum = window.cachedTabNum || 1;
    const tabName = tabNum == 2 ? 'Open Contracts' : tabNum == 4 ? 'Laundry Contracts' : `Tab ${tabNum}`;

    const url = `/tab/${tabNum}/full_items_by_rental_class?category=${encodeURIComponent(category)}&subcategory=${encodeURIComponent(subcategory)}&common_name=${encodeURIComponent(commonName)}`;
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
                    <td>${item.last_scanned_date || 'N/A'}</td>
                    <td>${item.quality || 'N/A'}</td>
                    <td>${item.notes || 'N/A'}</td>
                </tr>
            `).join('')}
        </tbody>
    `;

    const printContent = `
        <html>
            <head>
                <title>RFID Dashboard - ${tabName} - Full Item List</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
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
                        text-align: left;
                        font-size: 12px;
                        white-space: normal;
                        word-wrap: break-word;
                        min-width: 80px; /* Reduced base width */
                        max-width: 150px; /* Allow wrapping for long data */
                    }
                    th {
                        background-color: #f2f2f2;
                        font-weight: bold;
                    }
                    td {
                        vertical-align: top;
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
                            font-size: 10px;
                            min-width: 50px; /* Further reduced for print */
                            max-width: 100px; /* Ensure wrapping */
                            padding: 4px;
                            word-break: break-word;
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
                        console.log('Full item list print window loaded, content:', document.body.innerHTML);
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
    console.log('Full item list print triggered successfully');
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('Document loaded, initializing script');

    let tabNum;
    const pathMatch = window.location.pathname.match(/\/tab\/(\d+)/);
    if (pathMatch) {
        tabNum = parseInt(pathMatch[1], 10);
        console.log('Extracted tab number from URL:', tabNum);
    } else if (window.location.pathname === '/') {
        console.log('Homepage detected, defaulting tab number to 1');
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
            console.log('Print button clicked:', printBtn);
            const level = printBtn.getAttribute('data-print-level');
            const id = printBtn.getAttribute('data-print-id');
            const commonName = printBtn.getAttribute('data-common-name');
            const category = printBtn.getAttribute('data-category');
            const subcategory = printBtn.getAttribute('data-subcategory');
            console.log(`Print button clicked: level=${level}, id=${id}, commonName=${commonName}, category=${category}, subcategory=${subcategory}`);
            printTable(level, id, commonName, category, subcategory);
        }

        if (printFullBtn) {
            console.log('Print full button clicked:', printFullBtn);
            const commonName = printFullBtn.getAttribute('data-common-name');
            const category = printFullBtn.getAttribute('data-category');
            const subcategory = printFullBtn.getAttribute('data-subcategory');
            console.log(`Print full button clicked: commonName=${commonName}, category=${category}, subcategory=${subcategory}`);
            printFullItemList(category, subcategory, commonName);
        }
    });

    const searchInput = document.getElementById('category-filter') || document.getElementById('searchInput');
    const categoryFilter = document.getElementById('categoryFilter');
    const statusFilter = document.getElementById('statusFilter');
    const binFilter = document.getElementById('binFilter');

    if (searchInput) searchInput.addEventListener('input', window.applyFilters);
    if (categoryFilter) categoryFilter.addEventListener('change', window.applyFilters);
    if (statusFilter) statusFilter.addEventListener('change', window.applyFilters);
    if (binFilter) binFilter.addEventListener('change', window.applyFilters);

    window.applyFilters();
});