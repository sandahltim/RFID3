console.log('common.js version: 2025-05-29-v22 loaded');

/**
 * Common.js: Shared utilities for all tabs.
 * Dependencies: None (self-contained for printing, formatting, and pagination).
 */

/**
 * Format ISO date strings into "Thurs, Aug 21 2025 4:55 pm"
 * Used by: All tabs (for printing and display)
 */
function formatDate(isoDateString) {
    if (!isoDateString || isoDateString === 'N/A') return 'N/A';
    try {
        const date = new Date(isoDateString);
        if (isNaN(date.getTime())) return 'N/A';

        const days = ['Sun', 'Mon', 'Tues', 'Wed', 'Thurs', 'Fri', 'Sat'];
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

        const dayName = days[date.getDay()];
        const monthName = months[date.getMonth()];
        const day = date.getDate();
        const year = date.getFullYear();

        let hours = date.getHours();
        const minutes = date.getMinutes().toString().padStart(2, '0');
        const ampm = hours >= 12 ? 'pm' : 'am';
        hours = hours % 12 || 12;

        return `${dayName}, ${monthName} ${day} ${year} ${hours}:${minutes} ${ampm}`;
    } catch (error) {
        console.error('Error formatting date:', isoDateString, error);
        return 'N/A';
    }
}

/**
 * Wrapper for formatDate to maintain consistency
 * Used by: All tabs
 */
function formatDateTime(dateTimeStr) {
    return formatDate(dateTimeStr);
}

/**
 * Refresh the current tab
 * Used by: All tabs (via refresh buttons)
 */
function refreshTab() {
    window.location.reload();
}

/**
 * Normalize common name by removing quotes and extra spaces
 * Used by: All tabs (via printFullItemList)
 */
function normalizeCommonName(commonName) {
    return commonName.replace(/['"]/g, '').replace(/\s+/g, ' ').trim();
}

/**
 * Render pagination controls
 * Used by: All tabs for parent and expanded layers
 * @param {HTMLElement} container - The container to render pagination controls
 * @param {number} totalItems - Total number of items
 * @param {number} currentPage - Current page number
 * @param {number} perPage - Items per page
 * @param {function} onPageChange - Callback to handle page changes
 */
function renderPaginationControls(container, totalItems, currentPage, perPage, onPageChange) {
    if (!container) return;

    const totalPages = Math.ceil(totalItems / perPage);
    container.innerHTML = '';

    if (totalPages <= 1) return;

    const nav = document.createElement('nav');
    nav.setAttribute('aria-label', 'Pagination');
    const ul = document.createElement('ul');
    ul.className = 'pagination justify-content-center';

    // Previous button
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
    const prevLink = document.createElement('a');
    prevLink.className = 'page-link';
    prevLink.href = '#';
    prevLink.textContent = 'Previous';
    prevLink.addEventListener('click', (e) => {
        e.preventDefault();
        if (currentPage > 1) onPageChange(currentPage - 1);
    });
    prevLi.appendChild(prevLink);
    ul.appendChild(prevLi);

    // Page numbers (show up to 5 pages around current)
    const maxPagesToShow = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxPagesToShow / 2));
    let endPage = Math.min(totalPages, startPage + maxPagesToShow - 1);
    if (endPage - startPage + 1 < maxPagesToShow) {
        startPage = Math.max(1, endPage - maxPagesToShow + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
        const li = document.createElement('li');
        li.className = `page-item ${i === currentPage ? 'active' : ''}`;
        const link = document.createElement('a');
        link.className = 'page-link';
        link.href = '#';
        link.textContent = i;
        link.addEventListener('click', (e) => {
            e.preventDefault();
            onPageChange(i);
        });
        li.appendChild(link);
        ul.appendChild(li);
    }

    // Next button
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
    const nextLink = document.createElement('a');
    nextLink.className = 'page-link';
    nextLink.href = '#';
    nextLink.textContent = 'Next';
    nextLink.addEventListener('click', (e) => {
        e.preventDefault();
        if (currentPage < totalPages) onPageChange(currentPage + 1);
    });
    nextLi.appendChild(nextLink);
    ul.appendChild(nextLi);

    nav.appendChild(ul);
    container.appendChild(nav);
}

/**
 * Print a table (Contract, Common Name, or Item level)
 * Used by: All tabs
 * Dependency: formatDateTime, removeTotalItemsInventoryColumn
 */
async function printTable(level, id, commonName = null, category = null, subcategory = null) {
    console.log(`Printing table: ${level}, ID: ${id}, Common Name: ${commonName}, Category: ${category}, Subcategory: ${subcategory}`);
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
                <!-- Removed reference to non-existent style.css -->
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
 * Remove "Total Items in Inventory" column for Tabs 2 and 4
 * Used by: Tabs 2, 4 (via printTable)
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
 * Used by: All tabs
 * Dependency: normalizeCommonName, formatDateTime
 */
async function printFullItemList(category, subcategory, commonName) {
    console.log(`Printing full item list for Category: ${category}, Subcategory: ${subcategory}, Common Name: ${commonName}`);
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
                <!-- Removed reference to non-existent style.css -->
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