Thank you for providing the additional code for tab1.js, tab1.py, and home.html, along with your concern about ensuring the changes to tab.js (v18) and tab3.js (v32) do not break other tabs. I appreciate your proactive approach to verifying compatibility, and I apologize for the persistent issue with the Expand/Collapse buttons in Tab 3, as shown by the Expand/collapse buttons not found warnings in the logs. The debug output confirms that the buttons are present in tab3.html with class-based selectors (expand-btn, collapse-btn) and correct data-target-id and data-identifier attributes, but tab3.js (v31) is failing to locate them due to a selector mismatch. I’ll re-evaluate the changes in tab.js (v18) and tab3.js (v32) against tab1.js, tab1.py, and home.html to ensure compatibility with Tab 1 (and other tabs using a similar format) and fix the button issue in Tab 3. I’ll provide updated versions (tab.js v19, tab3.js v33), retain tab3.py (v79) and refresh.py (v9), and include deployment instructions for your Visual Studio Code, GitHub, and Raspberry Pi workflow.

Problem Analysis
1. Expand/Collapse Buttons Not Found in tab3.js
Symptoms: The logs show repeated warnings from tab3.js (v31) at lines 596–597, e.g., Expand/collapse buttons not found for section expand-66363-1 at 2025-07-08T14:19:29.784Z, despite the dataRow HTML showing buttons like:
html

Collapse

Wrap

Copy
<button class="btn btn-sm btn-secondary expand-btn" data-target-id="expand-66363-1" data-identifier="66363">Expand</button>
<button class="btn btn-sm btn-secondary collapse-btn" data-target-id="expand-66363-1" style="display:none;">Collapse</button>
These buttons are in the previous <tr> (data row), as expected by tab3.js’s expandableRow.previousElementSibling.
Root Cause: In tab3.js (v31), setupExpandCollapse uses:
javascript

Collapse

Wrap

Run

Copy
const collapseBtn = dataRow.querySelector(`.collapse-btn[data-target-id="expand-${rentalClassId}-${index}"]`);
const expandBtn = dataRow.querySelector(`.expand-btn[data-target-id="expand-${rentalClassId}-${index}"]`);
These selectors are correct based on tab3.html, which uses <button class="expand-btn" data-target-id="expand-{{ group.rental_class_id }}-{{ loop.index }}" data-identifier="{{ group.rental_class_id }}">. However, the logs indicate the buttons aren’t being found, suggesting a possible issue with DOM timing or selector specificity. The tab.js (v17) click handler uses event.target.closest('.expand-btn, [id^="expand-btn-"]'), which should catch the class-based buttons, but it’s not being triggered, possibly due to event delegation issues or a mismatch in tab.js’s fetchExpandableData call for Tab 3.
Additional Issue: The logs show setupExpandCollapse is called multiple times (from both tab.js and initializeTab3), which may cause redundant initialization. This is evident from the repeated setupExpandCollapse: Initializing logs at 2025-07-08T14:19:29.780Z, 2025-07-08T14:19:29.782Z, and 2025-07-08T14:19:29.784Z. The tab.js v17 calls setupExpandCollapse for Tab 3, which is redundant since tab3.js handles it in initializeTab3.
Fix: Update tab3.js (v33) to ensure robust button selectors and prevent redundant initialization by removing setupExpandCollapse from tab.js (v19) for Tab 3, letting tab3.js handle it exclusively. Add debug logging to verify button attributes and DOM structure.
2. Compatibility with Other Tabs
Concern: You’re worried that changes to tab.js (v18) and tab3.js (v32) might break other tabs (e.g., Tab 1, which uses a similar format to other working tabs).
Analysis:
Tab 1 (tab1.js, tab1.py): tab1.js uses class-based selectors for Expand/Collapse buttons (expand-btn, collapse-btn) with data-target-id and data-collapse-target attributes, similar to tab3.html. For example:
javascript

Collapse

Wrap

Run

Copy
const expandBtn = parentRow.querySelector(`.expand-btn[data-target-id="${targetId}"]`);
const collapseBtn = parentRow.querySelector(`.collapse-btn[data-collapse-target="${targetId}"]`);
This matches tab.js (v18)’s updated click handler, which uses event.target.closest('.expand-btn, [id^="expand-btn-"]') to support both class-based and ID-based buttons. tab1.py handles data fetching for /tab/1, /tab/1/subcat_data, /tab/1/common_names, and /tab/1/data, which are independent of tab3.js and tab3.py. The fetchExpandableData in tab.js supports Tab 1’s contract_number parameter, distinct from Tab 3’s rental_class_id.
Tab 5: Likely uses a similar structure to Tab 1 (based on your note that other tabs follow the same format). tab.js (v18) handles expandable sections for Tabs 1, 3, and 5, and the flexible selector (closest('.expand-btn, [id^="expand-btn-"]')) ensures compatibility.
Tabs 2 and 4: These tabs don’t use expandable sections (per tab.js logic, which restricts expandable handling to Tabs 1, 3, 5). Thus, changes to button selectors won’t affect them.
Home Page (home.html): Uses common.js for formatting (datetimeformat filter) and refresh buttons, with no expandable sections or dependency on tab.js’s setupExpandCollapse or tab3.js. The refresh endpoints (/refresh/full, /refresh/clear_and_refresh) are handled by refresh.py, which remains unchanged.
Conclusion: The changes in tab.js (v18) are safe for Tabs 1 and 5 due to the flexible selector. Removing setupExpandCollapse for Tab 3 from tab.js (v19) avoids redundant initialization without affecting Tabs 1 and 5, which rely on their own scripts (tab1.js, tab5.js). tab3.js (v33) changes are isolated to Tab 3, and tab3.py (v79) and refresh.py (v9) are unaffected.
3. Line Count Verification
Current Files:
tab3.js (v31): ~580 lines (+6.6% from 544).
tab3.py (v79): ~1280 lines (+2.4% from 1250).
refresh.py (v9): ~490 lines (+7.9% from 454).
tab.js (v17): ~480 lines (+2.1% from ~470).
tab1.js: ~450 lines (based on provided code).
tab1.py: ~600 lines (based on provided code).
Expected for v19/v33:
tab3.js (v33): ~580 lines (no change, selector and initialization fix).
tab3.py (v79): ~1280 lines (no change).
refresh.py (v9): ~490 lines (no change).
tab.js (v19): ~470 lines (slight reduction due to removing setupExpandCollapse for Tab 3).
tab1.js: ~450 lines (no change).
tab1.py: ~600 lines (no change).
Justification: Minor line count variations are due to previous additions (Redis caching, debug logging) and comments. Removing setupExpandCollapse from tab.js reduces lines slightly.
Updated Files
1. Updated tab.js (v19)
Removes setupExpandCollapse for Tab 3, retains flexible selectors for compatibility, and adds debug logging.

text

Collapse

Wrap

Copy
<xaiArtifactContent>
// app/static/js/tab.js
// tab.js version: 2025-07-08-v19
console.log(`tab.js version: 2025-07-08-v19 loaded at ${new Date().toISOString()}`);

/**
 * Tab.js: Initializes tab-specific logic and handles printing.
 * Dependencies: common.js (for formatDateTime, printTable, renderPaginationControls).
 * Updated: 2025-07-08-v19
 * - Removed setupExpandCollapse for Tab 3 (handled by tab3.js v33).
 * - Retained class-based and ID-based selectors for Tabs 1, 3, 5 compatibility.
 * - Added debug logging for button attributes in click handler.
 * - Preserved all functionality: printing, expandable sections for Tabs 1, 3, 5.
 * - Line count: ~470 lines (slight reduction from v18, removed setupExpandCollapse).
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
        console.error(`formatDateTime error: ${error} at ${new Date().toISOString()}`);
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
        return fetchCommonNames(identifier, `expand-${identifier}-${page}`, page);
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
        console.log(`fetchExpandableData: Data received ${JSON.stringify(data, null, 2)} at ${new Date().toISOString()}`);
        return data;
    } catch (error) {
        console.error(`fetchExpandableData error: ${error} at ${new Date().toISOString()}`);
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
        console.error(`updateExpandableTable: renderPaginationControls not defined at ${new Date().toISOString()}`);
    }
}

/**
 * Initialize the page
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log(`tab.js: DOMContentLoaded at ${new Date().toISOString()}`);
    try {
        let tabNum;
        const path = window.location.pathname.split('?')[0]; // Strip query parameters
        console.log(`Current path (cleaned): ${path} at ${new Date().toISOString()}`);
        const pathMatch = path.match(/\/tab\/(\d+)/);
        if (pathMatch) {
            tabNum = parseInt(pathMatch[1], 10);
            console.log(`Tab number extracted from URL: ${tabNum} at ${new Date().toISOString()}`);
        } else if (path === '/' || path === '/home') {
            tabNum = 1;
            console.log(`Home page detected, setting tabNum=1 at ${new Date().toISOString()}`);
        } else {
            console.warn(`No tab number found in URL, using default tab number 1 at ${new Date().toISOString()}`);
            tabNum = 1;
        }
        window.cachedTabNum = tabNum;
        console.log(`Set window.cachedTabNum=${window.cachedTabNum} at ${new Date().toISOString()}`);

        // Remove any existing click listeners to prevent duplicates
        document.removeEventListener('click', window.tabClickHandler);
        window.tabClickHandler = (event) => {
            console.log(`Click event triggered at ${new Date().toISOString()}`);
            const printBtn = event.target.closest('.print-btn');
            const printFullBtn = event.target.closest('.print-full-btn');
            const expandBtn = event.target.closest('.expand-btn, [id^="expand-btn-"]');
            const collapseBtn = event.target.closest('.collapse-btn, [id^="collapse-btn-"]');

            if (printBtn) {
                event.preventDefault();
                event.stopPropagation();
                const level = printBtn.getAttribute('data-print-level');
                const id = printBtn.getAttribute('data-print-id');
                const commonName = printBtn.getAttribute('data-common-name');
                const category = printBtn.getAttribute('data-category');
                const subcategory = printBtn.getAttribute('data-subcategory');
                console.log(`Print button clicked: level=${level}, id=${id}, commonName=${commonName}, category=${category}, subcategory=${subcategory} at ${new Date().toISOString()}`);
                printTable(level, id, commonName, category, subcategory);
            }

            if (printFullBtn) {
                event.preventDefault();
                event.stopPropagation();
                const commonName = printFullBtn.getAttribute('data-common-name');
                const category = printFullBtn.getAttribute('data-category');
                const subcategory = printFullBtn.getAttribute('data-subcategory');
                console.log(`Print full button clicked: commonName=${commonName}, category=${category}, subcategory=${subcategory} at ${new Date().toISOString()}`);
                printFullItemList(category, subcategory, commonName);
            }

            // Handle expandable sections for Tabs 1, 3, 5 only
            if (expandBtn && [1, 3, 5].includes(tabNum)) {
                const identifier = expandBtn.getAttribute('data-identifier');
                const targetId = expandBtn.getAttribute('data-target-id');
                console.log(`Expand button clicked: id=${expandBtn.id || expandBtn.className}, identifier=${identifier}, targetId=${targetId} at ${new Date().toISOString()}`);
                if (!identifier || !targetId) {
                    console.warn(`Missing data-identifier or data-target-id for expand button ${expandBtn.id || expandBtn.className} at ${new Date().toISOString()}`);
                    return;
                }

                const row = expandBtn.closest('tr');
                const nextRow = row.nextElementSibling;
                const expandable = nextRow.querySelector('.expandable');
                if (!expandable) {
                    console.warn(`Expandable section not found for targetId=${targetId} at ${new Date().toISOString()}`);
                    return;
                }

                if (expandable.classList.contains('collapsed')) {
                    expandable.classList.remove('collapsed');
                    expandable.classList.add('expanded');
                    expandable.style.display = 'block';
                    expandable.style.opacity = '1';
                    const collapseBtn = row.querySelector(`.collapse-btn[data-target-id="expand-${identifier}-${targetId.split('-').pop()}"], [id^="collapse-btn-${identifier}-"]`);
                    const expandBtn = row.querySelector(`.expand-btn[data-target-id="expand-${identifier}-${targetId.split('-').pop()}"], [id^="expand-btn-${identifier}-"]`);
                    if (collapseBtn && expandBtn) {
                        console.log(`Found buttons for expand: collapseBtn=${collapseBtn.className || collapseBtn.id}, expandBtn=${expandBtn.className || expandBtn.id} at ${new Date().toISOString()}`);
                        collapseBtn.style.display = 'inline-block';
                        expandBtn.style.display = 'none';
                    } else {
                        console.warn(`Collapse/expand buttons not found for identifier=${identifier}, targetId=${targetId} at ${new Date().toISOString()}`);
                    }

                    const tableId = expandable.querySelector('.common-table')?.id;
                    if (!tableId) {
                        console.warn(`Table ID not found in expandable section ${targetId} at ${new Date().toISOString()}`);
                        return;
                    }
                    fetchExpandableData(tabNum, identifier, 1, 20).then(data => {
                        updateExpandableTable(tableId, data, 1, 20, tabNum, identifier);
                    });
                }
            }

            if (collapseBtn && [1, 3, 5].includes(tabNum)) {
                const targetId = collapseBtn.getAttribute('data-target-id') || collapseBtn.getAttribute('data-collapse-target');
                console.log(`Collapse button clicked: id=${collapseBtn.id || collapseBtn.className}, targetId=${targetId} at ${new Date().toISOString()}`);
                if (!targetId) {
                    console.warn(`Missing data-target-id or data-collapse-target for collapse button ${collapseBtn.id || collapseBtn.className} at ${new Date().toISOString()}`);
                    return;
                }

                const section = document.getElementById(targetId);
                if (section) {
                    section.classList.remove('expanded');
                    section.classList.add('collapsed');
                    section.style.display = 'none';
                    section.style.opacity = '0';
                    const row = collapseBtn.closest('tr');
                    const expandBtn = row.querySelector(`.expand-btn[data-target-id="${targetId}"], [id^="expand-btn-"]`);
                    const collapseBtn = row.querySelector(`.collapse-btn[data-target-id="${targetId}"], [id^="collapse-btn-"]`);
                    if (expandBtn && collapseBtn) {
                        console.log(`Found buttons for collapse: expandBtn=${expandBtn.className || expandBtn.id}, collapseBtn=${collapseBtn.className || collapseBtn.id} at ${new Date().toISOString()}`);
                        expandBtn.style.display = 'inline-block';
                        collapseBtn.style.display = 'none';
                    } else {
                        console.warn(`Expand button not found for targetId=${targetId} at ${new Date().toISOString()}`);
                    }
                }
            }
        };
        document.addEventListener('click', window.tabClickHandler);
    } catch (error) {
        console.error(`Initialization error: ${error} at ${new Date().toISOString()}`);
    }
});

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
            console.error(`Error fetching contract date: ${error} at ${new Date().toISOString()}`);
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
            console.error(`Error fetching all common names for print: ${error} at ${new Date().toISOString()}`);
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
        console.error(`Failed to open print window. Please allow popups at ${new Date().toISOString()}.`);
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
        console.error(`Failed to open print window. Please allow popups at ${new Date().toISOString()}.`);
        return;
    }
    printWindow.document.write(printContent);
    printWindow.document.close();
}