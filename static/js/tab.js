console.log('tab.js loaded, cachedTabNum:', window.cachedTabNum);

// Refresh table function
function refreshTab() {
    window.location.reload(); // Updated to match static rendering in tab2.html and tab4.html
}

// Print table function
function printTable(level, id) {
    console.log(`Printing table: ${level}, ID: ${id}`);
    const element = document.getElementById(id);
    if (!element) {
        console.error(`Element with ID ${id} not found for printing`);
        return;
    }

    // Create a new window for printing
    const printWindow = window.open('', '_blank');
    if (!printWindow) {
        console.error('Failed to open print window. Please allow popups.');
        return;
    }

    // Get the tab name based on the current tab number
    const tabNum = window.cachedTabNum || 1;
    const tabName = tabNum == 2 ? 'Open Contracts' : tabNum == 4 ? 'Laundry Contracts' : `Tab ${tabNum}`;

    // Clone the element and include all expanded sections
    const printElement = element.cloneNode(true);
    const row = element.closest('tr');
    if (row) {
        // Find the corresponding expanded content (e.g., subcat-, common-, items- divs)
        const nextRow = row.nextElementSibling;
        if (nextRow) {
            const expandedContent = nextRow.querySelector('.expandable.expanded');
            if (expandedContent) {
                const expandedClone = expandedContent.cloneNode(true);
                // Remove buttons and loading indicators from expanded content
                expandedClone.querySelectorAll('.btn, .loading, .expandable.collapsed').forEach(el => el.remove());
                const expandedWrapper = document.createElement('div');
                expandedWrapper.appendChild(expandedClone);
                printElement.appendChild(expandedWrapper);
            }
        }
    }

    // Remove non-printable elements from the main element
    printElement.querySelectorAll('.btn, .loading, .expandable.collapsed').forEach(el => el.remove());

    // Prepare the print content with custom header and styles
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
                        margin-bottom: 20px;
                    }
                    .print-header h1 {
                        font-size: 24px;
                        margin: 0;
                    }
                    .print-header p {
                        font-size: 14px;
                        color: #666;
                        margin: 5px 0;
                    }
                    table {
                        border-collapse: collapse;
                        width: 100%;
                        margin-top: 10px;
                    }
                    th, td {
                        border: 1px solid #ccc;
                        padding: 8px;
                        text-align: left;
                        font-size: 12px;
                    }
                    th {
                        background-color: #f2f2f2;
                        font-weight: bold;
                    }
                    .hidden {
                        display: none;
                    }
                    .subcat-level {
                        margin-left: 1.5rem;
                        background-color: #f8f9fa;
                        padding: 0.5rem;
                        border-left: 3px solid #007bff;
                    }
                    .common-level {
                        margin-left: 1rem;
                        background-color: #e9ecef;
                        padding: 0.5rem;
                        border-left: 3px solid #28a745;
                    }
                    .item-level {
                        margin-left: 1rem;
                        background-color: #dee2e6;
                        padding: 0.5rem;
                        border-left: 3px solid #dc3545;
                    }
                    @media print {
                        body {
                            margin: 0;
                        }
                        .print-header {
                            position: fixed;
                            top: 0;
                            width: 100%;
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
                    <h1>RFID Dashboard - ${tabName}</h1>
                    <p>${level}</p>
                    <p>Printed on: ${new Date().toLocaleString()}</p>
                </div>
                <div style="margin-top: 60px;">
                    ${printElement.outerHTML}
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

    printWindow.document.write(printContent);
    printWindow.document.close();
    console.log('Print triggered successfully');
}

// Initialize script on document load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Document loaded, initializing script');

    // Extract tab number from URL path
    let tabNum;
    const pathMatch = window.location.pathname.match(/\/tab\/(\d+)/);
    if (pathMatch) {
        tabNum = parseInt(pathMatch[1], 10);
        console.log('Extracted tab number from URL:', tabNum);
    } else if (window.location.pathname === '/') {
        console.log('Homepage detected, defaulting tab number to 1');
        tabNum = 1; // Default for homepage
    } else {
        console.warn('No tab number found in URL, using default tab number 1.');
        tabNum = 1; // Default if not found
    }

    window.cachedTabNum = tabNum;

    // Set up print button listeners using event delegation
    document.addEventListener('click', (event) => {
        const button = event.target.closest('.print-btn');
        if (button) {
            console.log('Print button clicked:', button);
            const level = button.getAttribute('data-print-level');
            const id = button.getAttribute('data-print-id');
            console.log(`Print button clicked: level=${level}, id=${id}`);
            printTable(level, id);
        }
    });

    // Apply filters to all tables based on user input
    window.applyFilters = function() {
        console.log('Applying filters');
        const textQuery = document.getElementById('searchInput') ? document.getElementById('searchInput').value.toLowerCase() : '';
        const categoryFilter = document.getElementById('categoryFilter') ? document.getElementById('categoryFilter').value.toLowerCase() : '';
        const statusFilter = document.getElementById('statusFilter') ? document.getElementById('statusFilter').value.toLowerCase() : '';
        const binLocationFilter = document.getElementById('binFilter') ? document.getElementById('binFilter').value.toLowerCase() : '';

        const tables = document.querySelectorAll('table');
        tables.forEach(table => {
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const text = Array.from(row.children).map(cell => cell.textContent.toLowerCase()).join(' ');
                const categoryCell = row.querySelector('td:first-child') ? row.querySelector('td:first-child').textContent.toLowerCase() : '';
                const statusCell = row.querySelector('td:nth-child(4)') ? row.querySelector('td:nth-child(4)').textContent.toLowerCase() : '';
                const binLocationCell = row.querySelector('td:nth-child(3)')
                    ? row.querySelector('td:nth-child(3)').textContent.toLowerCase()
                    : row.querySelector('td:nth-child(2)')  // Adjust for Tab 2 with Customer Name
                      ? row.querySelector('td:nth-child(2)').textContent.toLowerCase()
                      : '';

                const matchesText = text.includes(textQuery);
                const matchesCategory = !categoryFilter || categoryCell.includes(categoryFilter);
                const matchesStatus = !statusFilter || statusCell.includes(statusFilter);
                const matchesBinLocation = !binLocationFilter || binLocationCell.includes(binLocationFilter);

                row.style.display = (matchesText && matchesCategory && matchesStatus && matchesBinLocation) ? '' : 'none';
            });
        });
    };
});