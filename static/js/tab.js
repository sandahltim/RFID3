console.log('tab.js loaded, cachedTabNum:', window.cachedTabNum);

// ... (previous code unchanged) ...

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
                        min-width: 80px; /* Reduced for print */
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
                            min-width: 60px;
                            padding: 6px;
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