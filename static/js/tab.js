// tab.js - Handles tab functionality for RFID Dashboard
// Version: 2025-04-20 v2 - Added print button listeners and refresh functionality

console.log('tab.js loaded, cachedTabNum:', window.cachedTabNum);

// Refresh table function
function refreshTable(tabNum) {
    const tableBody = document.getElementById('category-table-body');
    if (tableBody) {
        console.log('Refreshing table for tab:', tabNum);
        htmx.trigger(tableBody, 'refresh');
    } else {
        console.warn('Table body not found for refresh');
    }
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

    // Get the stylesheets
    const stylesheets = Array.from(document.styleSheets)
        .map(sheet => {
            try {
                return Array.from(sheet.cssRules)
                    .map(rule => rule.cssText)
                    .join('\n');
            } catch (e) {
                console.warn('Cannot access stylesheet rules:', e);
                return '';
            }
        })
        .filter(style => style)
        .join('\n');

    // Prepare the print content
    const printContent = `
        <html>
            <head>
                <title>Print ${level}</title>
                <style>
                    ${stylesheets}
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    table { border-collapse: collapse; width: 100%; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; }
                    @media print {
                        .btn, .loading { display: none; }
                    }
                </style>
            </head>
            <body>
                <h1>${level}</h1>
                ${element.outerHTML}
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

    // Restore original content (in case of any DOM manipulation)
    console.log('Original content restored after print');
}

// Initialize script on document load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Document loaded, initializing script');

    // Extract tab number from h1 element
    let tabNum;
    const h1 = document.querySelector('h1');
    if (h1) {
        const match = h1.textContent.match(/Tab (\d+)/);
        if (match) {
            tabNum = parseInt(match[1], 10);
            console.log('Extracted tab number:', tabNum);
        } else if (window.location.pathname === '/') {
            console.log('Homepage detected, defaulting tab number to 1');
            tabNum = 1; // Default for homepage
        } else {
            console.warn('No tab number found in h1 element, using default tab number 1.');
            tabNum = 1; // Default if not found
        }
    } else {
        console.warn('No h1 element found, using default tab number 1.');
        tabNum = 1;
    }

    window.cachedTabNum = tabNum;

    // Set up print button listeners
    const printButtons = document.querySelectorAll('.print-btn');
    console.log('Found', printButtons.length, 'print buttons');
    printButtons.forEach(button => {
        console.log('Setting up print button listener for:', button);
        button.addEventListener('click', (event) => {
            console.log('Direct click on print-btn:', button);
            console.log('Event details:', event);
            const level = button.getAttribute('data-print-level');
            const id = button.getAttribute('data-print-id');
            console.log(`Print button clicked: level=${level}, id=${id}`);
            printTable(level, id);
        });
    });

    // Apply filters to all tables based on user input
    window.applyFilters = function() {
        console.log('Applying filters');
        const textQuery = document.getElementById('filter-input') ? document.getElementById('filter-input').value.toLowerCase() : '';
        const categoryFilter = document.getElementById('category-filter') ? document.getElementById('category-filter').value.toLowerCase() : '';
        const statusFilter = document.getElementById('status-filter') ? document.getElementById('status-filter').value.toLowerCase() : '';
        const binLocationFilter = document.getElementById('bin-location-filter') ? document.getElementById('bin-location-filter').value.toLowerCase() : '';

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
    };
});