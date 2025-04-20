// Global variable to cache the tab number, extracted from the h1 element
if (typeof cachedTabNum === 'undefined') {
    var cachedTabNum = '1'; // Default to '1' if h1 is not found or no number is present
}

// Log script loading
console.log('tab.js loaded, cachedTabNum:', cachedTabNum);

// Sort a table by a specified column
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

// Apply filters to all tables based on user input (text, category, status, bin location)
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

// Print the table content in the current window
function printTable(level, id) {
    console.log(`Printing table: ${level}, ID: ${id}`);
    const element = document.getElementById(id);
    if (!element) {
        console.warn(`Element with ID '${id}' not found for printing.`);
        return;
    }

    // Inform the user that printing will occur in the current window due to popup blockers
    alert('Printing will occur in the current window.\n\nNote: If you prefer a new window, please allow popups for this site:\n1. Click the lock icon in the address bar (left of "pi5:3607")\n2. Click "Site settings"\n3. Find "Pop-ups and redirects" and set to "Allow"\n4. Reload the page and try again');

    // Create a temporary container for the print content
    const printContainer = document.createElement('div');
    printContainer.style.position = 'absolute';
    printContainer.style.top = '0';
    printContainer.style.left = '0';
    printContainer.style.width = '100%';
    printContainer.style.background = 'white';
    printContainer.style.zIndex = '1000';
    printContainer.innerHTML = `
        <div class="print-header">
            <h1>RFID Dashboard Report</h1>
            <p>Generated on ${new Date().toLocaleString()}</p>
            <h2>${level}</h2>
        </div>
        ${element.outerHTML}
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h2 { text-align: center; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .print-header { text-align: center; margin-bottom: 20px; }
        </style>
    `;

    // Hide the main content and show the print content
    const originalContent = document.body.innerHTML;
    document.body.innerHTML = '';
    document.body.appendChild(printContainer);

    // Trigger print and restore original content
    try {
        window.print();
        console.log('Print triggered successfully');
    } catch (error) {
        console.error('Error during print:', error);
    } finally {
        document.body.innerHTML = originalContent;
        console.log('Original content restored after print');
    }
}

// Refresh the category table by triggering a manual fetch
let isRefreshing = false;
function refreshTable(tabNum) {
    if (isRefreshing) return;
    isRefreshing = true;
    console.log(`Refreshing table for tab ${tabNum}`);
    const categoryTableBody = document.getElementById('category-table-body');
    if (!categoryTableBody) {
        console.warn('Category table body not found for refresh.');
        setTimeout(() => { isRefreshing = false; }, 1000);
        return;
    }

    // Manually fetch the categories
    fetch(`/tab/${tabNum}/categories`)
        .then(response => {
            console.log('Refresh fetch status:', response.status, response.statusText);
            if (!response.ok) {
                throw new Error(`Refresh fetch failed with status ${response.status}`);
            }
            return response.text();
        })
        .then(html => {
            console.log('Refresh fetch response:', html.slice(0, 100) + '...');
            categoryTableBody.innerHTML = html;
        })
        .catch(error => {
            console.error('Refresh fetch error:', error);
        })
        .finally(() => {
            setTimeout(() => { isRefreshing = false; }, 1000);
        });
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('Document loaded, initializing script');
    
    // Safely extract the tab number from the h1 element
    const h1Element = document.querySelector('h1');
    if (h1Element) {
        try {
            const h1Text = h1Element.textContent.trim();
            const tabNumMatch = h1Text.match(/Tab\s+(\d+)/i);
            if (tabNumMatch && tabNumMatch[1]) {
                cachedTabNum = tabNumMatch[1];
                console.log(`Extracted tab number: ${cachedTabNum}`);
                // Only set up the refresh interval on tab pages
                if (window.location.pathname.startsWith('/tab/')) {
                    setInterval(() => refreshTable(cachedTabNum), 30000);
                }
            } else {
                console.warn('No tab number found in h1 element, using default tab number 1.');
            }
        } catch (error) {
            console.error('Error extracting tab number from h1:', error);
        }
    } else {
        console.warn('No h1 element found on the page, using default tab number 1.');
    }

    // Skip tab-specific logic on non-tab pages
    if (!window.location.pathname.startsWith('/tab/')) {
        console.debug('Not a tab page, skipping tab-specific logic.');
    }

    // Direct click listener for print-btn buttons
    document.querySelectorAll('.print-btn').forEach(button => {
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
});