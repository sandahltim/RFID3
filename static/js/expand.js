console.log('expand.js version: 2025-04-27-v66 loaded');

// Note: Common function - will be moved to common.js during split
function showLoading(key) {
    const loadingDiv = document.getElementById(`loading-${key}`);
    if (loadingDiv) {
        console.log('Loading indicator found, displaying:', loadingDiv);
        loadingDiv.style.display = 'block';
    } else {
        console.warn(`Loading indicator with ID loading-${key} not found`);
    }
}

// Note: Common function - will be moved to common.js during split
function hideLoading(key) {
    const loadingDiv = document.getElementById(`loading-${key}`);
    if (loadingDiv) {
        console.log('Loading indicator found, hiding:', loadingDiv);
        loadingDiv.style.display = 'none';
    } else {
        console.warn(`Loading indicator with ID loading-${key} not found`);
    }
}

// Note: Common function - will be moved to common.js during split
function toggleCollapseButton(targetId) {
    const expandBtn = document.querySelector(`[data-target-id="${targetId}"]`);
    const collapseBtn = document.querySelector(`[data-collapse-target="${targetId}"]`);
    if (expandBtn && collapseBtn) {
        expandBtn.style.display = expandBtn.style.display === 'none' ? 'inline-block' : 'none';
        collapseBtn.style.display = collapseBtn.style.display === 'none' ? 'inline-block' : 'none';
    }
}

// Note: Event listener for Tabs 2, 3, 4, Categories, and Home
document.addEventListener('DOMContentLoaded', function() {
    console.log('expand.js: DOMContentLoaded event fired');

    // Ensure window.cachedTabNum is set
    if (!window.cachedTabNum) {
        const pathMatch = window.location.pathname.match(/\/tab\/(\d+)/);
        window.cachedTabNum = pathMatch ? parseInt(pathMatch[1], 10) : 1;
        console.log('Set window.cachedTabNum:', window.cachedTabNum);
    }

    // Skip if we're on Tab 1 or Tab 5, as they use tab1_5.js
    if (window.cachedTabNum === 1 || window.cachedTabNum === 5) {
        console.log('Tab 1 or Tab 5 detected, skipping expand.js event listeners');
        return;
    }

    // Clear outdated sessionStorage entries that don't match current tab
    Object.keys(sessionStorage).forEach(key => {
        if (key.startsWith('expanded_') || key.startsWith('expanded_common_') || key.startsWith('expanded_items_')) {
            try {
                const state = JSON.parse(sessionStorage.getItem(key));
                const targetId = key.replace(/^(expanded_|expanded_common_|expanded_items_)/, '');
                if (!document.getElementById(targetId) && !document.getElementById(`common-${targetId}`) && !document.getElementById(`items-${targetId}`)) {
                    console.log(`Removing outdated sessionStorage entry: ${key}`);
                    sessionStorage.removeItem(key);
                }
            } catch (e) {
                console.error('Error parsing sessionStorage for', key, ':', e);
                sessionStorage.removeItem(key);
            }
        }
    });

    // Do not automatically expand any sections on load
    console.log('Skipping automatic expansion on load');

    // Remove any existing click event listeners to prevent duplicates
    document.removeEventListener('click', handleClick);
    document.addEventListener('click', handleClick);

    function handleClick(event) {
        const expandBtn = event.target.closest('.expand-btn');
        if (expandBtn) {
            event.stopPropagation();
            const category = expandBtn.getAttribute('data-category');
            const commonName = expandBtn.getAttribute('data-common-name');
            const targetId = expandBtn.getAttribute('data-target-id');
            const contractNumber = expandBtn.getAttribute('data-contract-number');

            if (commonName) {
                // Expand to items level
                expandItems(contractNumber, commonName, targetId);
            } else {
                // Expand to common names level (Tabs 2 and 4)
                expandCategory(contractNumber, targetId, contractNumber);
            }
            return;
        }

        const collapseBtn = event.target.closest('.collapse-btn');
        if (collapseBtn) {
            event.stopPropagation();
            const targetId = collapseBtn.getAttribute('data-collapse-target');
            collapseSection(targetId);
            return;
        }
    }

    // Define expandCategory for Tabs 2 and 4 (load common names directly under contract)
    window.expandCategory = function(category, targetId, contractNumber, page = 1) {
        console.log('expandCategory called with', { category, targetId, contractNumber, page });

        const targetElement = document.getElementById(targetId);
        if (!targetElement) {
            console.error(`Target element with ID ${targetId} not found`);
            return;
        }

        // Check if already expanded
        if (targetElement.classList.contains('expanded')) {
            console.log(`Section ${targetId} is already expanded, collapsing instead`);
            collapseSection(targetId);
            return;
        }

        // Show loading indicator
        showLoading(contractNumber);

        // Fetch common names for the contract
        fetch(`/tab/${window.cachedTabNum}/common_names?contract_number=${encodeURIComponent(contractNumber)}&page=${page}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Error fetching common names:', data.error);
                    targetElement.innerHTML = `<p>Error: ${data.error}</p>`;
                    return;
                }

                const commonNames = data.common_names || [];
                const totalCommonNames = data.total_common_names || 0;
                const perPage = data.per_page || 10;
                const currentPage = data.page || 1;

                // Build the common names table
                let html = `
                    <table class="common-table">
                        <thead>
                            <tr>
                                <th>Common Name</th>
                                <th>Items on Contract</th>
                                <th>Total Items in Inventory</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

                commonNames.forEach(common => {
                    const commonId = `${contractNumber}-${common.name.replace(/[^a-zA-Z0-9]/g, '_')}`;
                    html += `
                        <tr>
                            <td>${common.name}</td>
                            <td>${common.on_contracts}</td>
                            <td>${common.total_items_inventory}</td>
                            <td>
                                <button class="btn btn-sm btn-secondary expand-btn" data-common-name="${common.name}" data-target-id="items-${commonId}" data-contract-number="${contractNumber}">Expand</button>
                                <button class="btn btn-sm btn-secondary collapse-btn" data-collapse-target="items-${commonId}" style="display:none;">Collapse</button>
                                <button class="btn btn-sm btn-info print-btn" data-print-level="Common Name" data-print-id="items-${commonId}" data-common-name="${common.name}" data-category="${contractNumber}">Print</button>
                                <button class="btn btn-sm btn-info print-full-btn" data-common-name="${common.name}" data-category="${contractNumber}">Print Full List</button>
                                <div id="loading-${commonId}" style="display:none;" class="loading">Loading...</div>
                            </td>
                        </tr>
                        <tr>
                            <td colspan="4">
                                <div id="items-${commonId}" class="expandable collapsed item-level"></div>
                            </td>
                        </tr>
                    `;
                });

                html += `
                        </tbody>
                    </table>
                `;

                // Add pagination controls if needed
                if (totalCommonNames > perPage) {
                    const totalPages = Math.ceil(totalCommonNames / perPage);
                    html += `
                        <div class="pagination-controls">
                            <button class="btn btn-sm btn-secondary" onclick="window.expandCategory('${category}', '${targetId}', '${contractNumber}', ${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>
                            <span>Page ${currentPage} of ${totalPages}</span>
                            <button class="btn btn-sm btn-secondary" onclick="window.expandCategory('${category}', '${targetId}', '${contractNumber}', ${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>
                        </div>
                    `;
                }

                targetElement.innerHTML = html;
                targetElement.classList.remove('collapsed');
                targetElement.classList.add('expanded');
                toggleCollapseButton(targetId);

                // Save expanded state
                sessionStorage.setItem(`expanded_${targetId}`, JSON.stringify({ expanded: true }));
            })
            .catch(error => {
                console.error('Error fetching common names:', error);
                targetElement.innerHTML = '<p>Failed to load common names</p>';
            })
            .finally(() => {
                hideLoading(contractNumber);
            });
    };

    // Function to expand items under a common name
    function expandItems(contractNumber, commonName, targetId, page = 1) {
        console.log('expandItems called with', { contractNumber, commonName, targetId, page });

        const targetElement = document.getElementById(targetId);
        if (!targetElement) {
            console.error(`Target element with ID ${targetId} not found`);
            return;
        }

        // Check if already expanded
        if (targetElement.classList.contains('expanded')) {
            console.log(`Section ${targetId} is already expanded, collapsing instead`);
            collapseSection(targetId);
            return;
        }

        // Show loading indicator
        const commonId = targetId.replace('items-', '');
        showLoading(commonId);

        // Fetch items for the common name
        fetch(`/tab/${window.cachedTabNum}/data?contract_number=${encodeURIComponent(contractNumber)}&common_name=${encodeURIComponent(commonName)}&page=${page}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Error fetching items:', data.error);
                    targetElement.innerHTML = `<p>Error: ${data.error}</p>`;
                    return;
                }

                const items = data.items || [];
                const totalItems = data.total_items || 0;
                const perPage = data.per_page || 10;
                const currentPage = data.page || 1;

                // Build the items table
                let html = `
                    <div class="item-level-wrapper">
                        <table class="item-table">
                            <thead>
                                <tr>
                                    <th>Tag ID</th>
                                    <th>Common Name</th>
                                    <th>Bin Location</th>
                                    <th>Status</th>
                                    <th>Last Contract</th>
                                    <th>Last Scanned Date</th>
                                </tr>
                            </thead>
                            <tbody>
                `;

                items.forEach(item => {
                    html += `
                        <tr>
                            <td>${item.tag_id}</td>
                            <td>${item.common_name}</td>
                            <td>${item.bin_location || 'N/A'}</td>
                            <td>${item.status}</td>
                            <td>${item.last_contract_num || 'N/A'}</td>
                            <td>${item.last_scanned_date || 'N/A'}</td>
                        </tr>
                    `;
                });

                html += `
                            </tbody>
                        </table>
                    </div>
                `;

                // Add pagination controls if needed
                if (totalItems > perPage) {
                    const totalPages = Math.ceil(totalItems / perPage);
                    html += `
                        <div class="pagination-controls">
                            <button class="btn btn-sm btn-secondary" onclick="expandItems('${contractNumber}', '${commonName}', '${targetId}', ${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>
                            <span>Page ${currentPage} of ${totalPages}</span>
                            <button class="btn btn-sm btn-secondary" onclick="expandItems('${contractNumber}', '${commonName}', '${targetId}', ${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>
                        </div>
                    `;
                }

                targetElement.innerHTML = html;
                targetElement.classList.remove('collapsed');
                targetElement.classList.add('expanded');
                toggleCollapseButton(targetId);

                // Save expanded state
                sessionStorage.setItem(`expanded_items_${targetId}`, JSON.stringify({ expanded: true }));
            })
            .catch(error => {
                console.error('Error fetching items:', error);
                targetElement.innerHTML = '<p>Failed to load items</p>';
            })
            .finally(() => {
                hideLoading(commonId);
            });
    }

    // Function to collapse a section
    function collapseSection(targetId) {
        const targetElement = document.getElementById(targetId);
        if (targetElement) {
            targetElement.classList.remove('expanded');
            targetElement.classList.add('collapsed');
            targetElement.innerHTML = '';
            toggleCollapseButton(targetId);
            sessionStorage.removeItem(`expanded_${targetId}`);
            sessionStorage.removeItem(`expanded_items_${targetId}`);
        }
    }
});