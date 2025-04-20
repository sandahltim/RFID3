// Global variable to cache the tab number, extracted from the h1 element
if (typeof window.cachedTabNum === 'undefined') {
    window.cachedTabNum = '1'; // Default to '1' if h1 is not found or no number is present
}

// Log script loading
console.log('tab.js loaded, cachedTabNum:', window.cachedTabNum);

// Sort a table by a specified column
function sortTable(column, tableId) {
    console.log('Sorting table ' + tableId + ' by column: ' + column);
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

// Print the table content in the current window
function printTable(level, id) {
    console.log('Printing table: ' + level + ', ID: ' + id);
    const element = document.getElementById(id);
    if (!element) {
        console.warn('Element with ID "' + id + '" not found for printing.');
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
    printContainer.innerHTML = [
        '<div class="print-header">',
            '<h1>RFID Dashboard Report</h1>',
            '<p>Generated on ' + new Date().toLocaleString() + '</p>',
            '<h2>' + level + '</h2>',
        '</div>',
        element.outerHTML,
        '<style>',
            'body { font-family: Arial, sans-serif; margin: 20px; }',
            'h2 { text-align: center; }',
            'table { width: 100%; border-collapse: collapse; margin-top: 20px; }',
            'th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }',
            'th { background-color: #f2f2f2; }',
            '.print-header { text-align: center; margin-bottom: 20px; }',
        '</style>'
    ].join('');

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
if (typeof window.isRefreshing === 'undefined') {
    window.isRefreshing = false;
}

function refreshTable(tabNum) {
    if (window.isRefreshing) return;
    window.isRefreshing = true;
    console.log('Refreshing table for tab ' + tabNum);
    const categoryTableBody = document.getElementById('category-table-body');
    if (!categoryTableBody) {
        console.warn('Category table body not found for refresh.');
        setTimeout(() => { window.isRefreshing = false; }, 1000);
        return;
    }

    // Manually fetch the categories
    fetch('/tab/' + tabNum + '/categories')
        .then(response => {
            console.log('Refresh fetch status:', response.status, response.statusText);
            if (!response.ok) {
                throw new Error('Refresh fetch failed with status ' + response.status);
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
            setTimeout(() => { window.isRefreshing = false; }, 1000);
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
                window.cachedTabNum = tabNumMatch[1];
                console.log('Extracted tab number: ' + window.cachedTabNum);
                // Only set up the refresh interval on tab pages
                if (window.location.pathname.startsWith('/tab/')) {
                    setInterval(() => refreshTable(window.cachedTabNum), 30000);
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
            console.log('Print button clicked: level=' + level + ', id=' + id);
            printTable(level, id);
        });
    });
});