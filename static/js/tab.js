console.log('tab.js version: 2025-05-29-v6 loaded');

/**
 * Tab.js: Initializes tab-specific logic and handles printing.
 * Dependencies: common.js (for formatDateTime, printTable, renderPaginationControls).
 * Updated: Prevented handling of Tab 2 expands to avoid double invocation.
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

    if (typeof renderPaginationControls === 'function') {
        const paginationContainer = document.querySelector(`#pagination-${tableId}`);
        if (paginationContainer) {
            renderPaginationControls(paginationContainer, data.total_items, page, perPage, (newPage) => {
                fetchExpandableData(tabNum, contractNumber, newPage, perPage).then(newData => {
                    updateExpandableTable(tableId, newData, newPage, perPage, tabNum, contractNumber);
                });
            });
        }
    } else {
        console.error('renderPaginationControls is not defined');
    }
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

            // Handle expandable sections for Tabs 1, 3, 4, 5 (skip Tab 2)
            if (expandBtn && tabNum !== 2) {
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

                const contractNumber = expandBtn.getAttribute('data-contract-number');
                const targetId = expandBtn.getAttribute('data-target-id');

                if (!contractNumber || !targetId) {
                    console.warn('Contract number or target ID missing for expandable section');
                    return;
                }

                if (expandable.classList.contains('collapsed')) {
                    expandable.classList.remove('collapsed');
                    expandable.classList.add('expanded');

                    // For other tabs, fetch data and update table
                    const tableId = expandable.querySelector('.common-table')?.id;
                    if (!tableId) {
                        console.warn('Table ID not found in expandable section; proceeding without it');
                    }
                    fetchExpandableData(tabNum, contractNumber, 1, 20).then(data => {
                        if (tableId) {
                            updateExpandableTable(tableId, data, 1, 20, tabNum, contractNumber);
                        } else {
                            console.log('No table ID; expandable content should be populated by tab-specific script');
                        }
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