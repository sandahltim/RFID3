console.log('tab1_5.js version: 2025-04-26-v9 loaded');

// Note: Common function for Tabs 1 and 5
function hideOtherSubcats(currentCategory, parentCategory) {
    const subcatDivs = document.querySelectorAll(`[id^="subcat-${parentCategory}_"]`);
    console.log('Found subcat divs for parent', parentCategory, ':', subcatDivs.length);
    subcatDivs.forEach(div => {
        const divId = div.id;
        if (divId !== `subcat-${currentCategory}`) {
            console.log('Collapsing subcat div:', divId);
            div.classList.remove('expanded');
            div.classList.add('collapsed');
            div.style.display = 'none';
            div.style.opacity = '0';
        }
    });
}

// Note: Common function for Tabs 1 and 5
function hideOtherCommonNames(currentTargetId, parentSubcategory) {
    const commonDivs = document.querySelectorAll(`[id^="common-${parentSubcategory}_"]`);
    console.log('Found common divs for parent', parentSubcategory, ':', commonDivs.length);
    commonDivs.forEach(div => {
        const divId = div.id;
        if (divId !== currentTargetId) {
            console.log('Collapsing common div:', divId);
            div.classList.remove('expanded');
            div.classList.add('collapsed');
            div.style.display = 'none';
        }
    });
}

// Note: Common function for Tabs 1 and 5
function hideOtherItems(currentTargetId, parentCommonName) {
    const itemDivs = document.querySelectorAll(`[id^="items-${parentCommonName}_"]`);
    console.log('Found item divs for parent', parentCommonName, ':', itemDivs.length);
    itemDivs.forEach(div => {
        const divId = div.id;
        if (divId !== currentTargetId) {
            console.log('Collapsing item div:', divId);
            div.classList.remove('expanded');
            div.classList.add('collapsed');
            div.style.display = 'none';
        }
    });
}

// Note: Common function for Tabs 1 and 5
function collapseSection(targetId) {
    if (!targetId) {
        console.error('collapseSection called with undefined or null targetId');
        return;
    }
    console.log('collapseSection called for targetId:', targetId);
    const section = document.getElementById(targetId);
    if (section) {
        section.classList.remove('expanded');
        section.classList.add('collapsed');
        section.style.display = 'none';
        section.style.opacity = '0';

        const collapseBtn = document.querySelector(`button[data-collapse-target="${targetId}"]`);
        const expandBtn = collapseBtn ? collapseBtn.previousElementSibling : null;
        if (expandBtn && collapseBtn) {
            expandBtn.style.display = 'inline-block';
            collapseBtn.style.display = 'none';
        } else {
            console.warn('Could not find expand/collapse buttons for targetId:', targetId);
        }

        // Remove from sessionStorage
        sessionStorage.removeItem(`expanded_${targetId}`);
        sessionStorage.removeItem(`expanded_common_${targetId}`);
        sessionStorage.removeItem(`expanded_items_${targetId}`);
    }
}

// Note: Common function for Tabs 1 and 5
function loadCommonNames(category, subcategory, targetId, page = 1, contractNumber = null) {
    console.log('loadCommonNames called with', { category, subcategory, targetId, page, contractNumber });

    if (!category || !targetId) {
        console.error('Invalid parameters for loadCommonNames:', { category, subcategory, targetId });
        return;
    }

    // Adjust containerId based on whether there's a subcategory (Tabs 1, 5) or not (Tabs 2, 4)
    const containerId = (window.cachedTabNum == 2 || window.cachedTabNum == 4) ? targetId : `common-${targetId}`;
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container with ID ${containerId} not found`);
        return;
    }

    const key = targetId; // Use targetId as the key to match the loading indicator
    showLoading(key);
    hideOtherCommonNames(containerId, targetId);

    let url = `/tab/${window.cachedTabNum}/common_names?page=${page}`;
    if (window.cachedTabNum == 2 || window.cachedTabNum == 4) {
        if (!contractNumber) {
            console.error('Contract number required for Tabs 2 and 4');
            return;
        }
        url += `&contract_number=${encodeURIComponent(contractNumber)}`;
    } else {
        url += `&category=${encodeURIComponent(category)}`;
    }
    if (subcategory) {
        url += `&subcategory=${encodeURIComponent(subcategory)}`;
    }

    const commonFilter = document.getElementById(`common-filter-${key}`)?.value || '';
    const commonSort = document.getElementById(`common-sort-${key}`)?.value || '';
    const statusFilter = document.getElementById('statusFilter')?.value || '';
    const binFilter = document.getElementById('binFilter')?.value || '';
    if (commonFilter) {
        url += `&filter=${encodeURIComponent(commonFilter)}`;
    }
    if (commonSort) {
        url += `&sort=${encodeURIComponent(commonSort)}`;
    }
    if (statusFilter) {
        url += `&statusFilter=${encodeURIComponent(statusFilter)}`;
    }
    if (binFilter) {
        url += `&binFilter=${encodeURIComponent(binFilter)}`;
    }

    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Common names fetch failed with status ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            let html = '';
            if (data.common_names && data.common_names.length > 0) {
                const headers = window.cachedTabNum == 2 || window.cachedTabNum == 4
                    ? ['Common Name', 'Items on Contract', 'Total Items in Inventory', 'Actions']
                    : ['Common Name', 'Total Items', 'Items on Contracts', 'Items in Service', 'Items Available', 'Actions'];

                html += `
                    <div class="common-level">
                        <div class="filter-sort-controls">
                            <input type="text" id="common-filter-${key}" placeholder="Filter common names..." value="${commonFilter}" oninput="loadCommonNames('${category}', '${subcategory || ''}', '${targetId}', 1, '${contractNumber || ''}')">
                            <select id="common-sort-${key}" onchange="loadCommonNames('${category}', '${subcategory || ''}', '${targetId}', 1, '${contractNumber || ''}')">
                                <option value="">Sort By...</option>
                                <option value="name_asc" ${commonSort === 'name_asc' ? 'selected' : ''}>Name (A-Z)</option>
                                <option value="name_desc" ${commonSort === 'name_desc' ? 'selected' : ''}>Name (Z-A)</option>
                                <option value="total_items_asc" ${commonSort === 'total_items_asc' ? 'selected' : ''}>Total Items (Low to High)</option>
                                <option value="total_items_desc" ${commonSort === 'total_items_desc' ? 'selected' : ''}>Total Items (High to Low)</option>
                            </select>
                `;

                if (window.cachedTabNum == 5) {
                    html += `
                        <div class="bulk-update-controls" style="margin-top: 10px;">
                            <select id="bulk-bin-location-${key}" onchange="updateBulkField('${key}', 'bin_location')">
                                <option value="">Update Bin Location...</option>
                                <option value="resale">resale</option>
                                <option value="sold">sold</option>
                                <option value="pack">pack</option>
                                <option value="burst">burst</option>
                            </select>
                            <select id="bulk-status-${key}" onchange="updateBulkField('${key}', 'status')">
                                <option value="">Update Status...</option>
                                <option value="Ready to Rent">Ready to Rent</option>
                            </select>
                            <button class="btn btn-sm btn-primary" onclick="bulkUpdateCommonName('${category}', '${subcategory || ''}', '${targetId}', '${key}')">Bulk Update</button>
                        </div>
                    `;
                }

                html += `
                        </div>
                        <table class="table table-bordered mt-2" id="common-table-${key}">
                            <thead>
                                <tr>
                                    ${headers.map(header => `<th>${header}</th>`).join('')}
                                </tr>
                            </thead>
                            <tbody>
                `;

                data.common_names.forEach(item => {
                    const rowId = `${key}_${item.name.replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '')}`;
                    if (window.cachedTabNum == 2 || window.cachedTabNum == 4) {
                        html += `
                            <tr>
                                <td>${item.name}</td>
                                <td>${item.items_on_contracts}</td>
                                <td>${item.total_items}</td>
                                <td>
                                    <button class="btn btn-sm btn-secondary expand-btn" data-category="${category}" data-subcategory="${subcategory || ''}" data-common-name="${item.name}" data-target-id="items-${rowId}">Expand</button>
                                    <button class="btn btn-sm btn-secondary collapse-btn" style="display:none;" data-collapse-target="items-${rowId}">Collapse</button>
                                    <button class="btn btn-sm btn-info print-btn" data-print-level="Common Name" data-print-id="common-table-${key}" data-common-name="${item.name}" data-category="${category}" data-subcategory="${subcategory || ''}">Print Aggregate</button>
                                    <button class="btn btn-sm btn-info print-full-btn" data-common-name="${item.name}" data-category="${category}" data-subcategory="${subcategory || ''}">Print Full List</button>
                                    <div id="loading-${rowId}" style="display:none;" class="loading">Loading...</div>
                                </td>
                            </tr>
                            <tr>
                                <td colspan="${headers.length}">
                                    <div id="items-${rowId}" class="expandable collapsed"></div>
                                </td>
                            </tr>
                        `;
                    } else {
                        html += `
                            <tr>
                                <td>${item.name}</td>
                                <td>${item.total_items}</td>
                                <td>${item.items_on_contracts}</td>
                                <td>${item.items_in_service}</td>
                                <td>${item.items_available}</td>
                                <td>
                                    <button class="btn btn-sm btn-secondary expand-btn" data-category="${category}" data-subcategory="${subcategory || ''}" data-common-name="${item.name}" data-target-id="items-${rowId}">Expand</button>
                                    <button class="btn btn-sm btn-secondary collapse-btn" style="display:none;" data-collapse-target="items-${rowId}">Collapse</button>
                                    <button class="btn btn-sm btn-info print-btn" data-print-level="Common Name" data-print-id="common-table-${key}" data-common-name="${item.name}" data-category="${category}" data-subcategory="${subcategory || ''}">Print Aggregate</button>
                                    <button class="btn btn-sm btn-info print-full-btn" data-common-name="${item.name}" data-category="${category}" data-subcategory="${subcategory || ''}">Print Full List</button>
                                    <div id="loading-${rowId}" style="display:none;" class="loading">Loading...</div>
                                </td>
                            </tr>
                            <tr>
                                <td colspan="${headers.length}">
                                    <div id="items-${rowId}" class="expandable collapsed"></div>
                                </td>
                            </tr>
                        `;
                    }
                });

                if (data.total_common_names > data.per_page) {
                    const totalPages = Math.ceil(data.total_common_names / data.per_page);
                    html += `
                        <tr>
                            <td colspan="${headers.length}" class="pagination-controls">
                                <button class="btn btn-sm btn-secondary" onclick="loadCommonNames('${category}', '${subcategory || ''}', '${targetId}', ${page - 1}, '${contractNumber || ''}')" ${page === 1 ? 'disabled' : ''}>Previous</button>
                                <span>Page ${page} of ${totalPages}</span>
                                <button class="btn btn-sm btn-secondary" onclick="loadCommonNames('${category}', '${subcategory || ''}', '${targetId}', ${page + 1}, '${contractNumber || ''}')" ${page === totalPages ? 'disabled' : ''}>Next</button>
                            </td>
                        </tr>
                    `;
                }

                html += `
                            </tbody>
                        </table>
                    </div>
                `;
            } else {
                html = `<div class="common-level"><p>No common names found for this ${subcategory ? 'subcategory' : 'category'}.</p></div>`;
            }

            container.innerHTML = html;
            container.classList.remove('collapsed');
            container.classList.add('expanded');
            container.style.display = 'block';
            container.style.opacity = '1';

            // Force reflow to ensure visibility
            container.offsetHeight; // Trigger reflow
            container.style.display = 'block';

            const expandBtn = document.querySelector(`button.expand-btn[data-target-id="${containerId}"]`);
            const collapseBtn = expandBtn ? expandBtn.nextElementSibling : null;
            if (expandBtn && collapseBtn) {
                expandBtn.style.display = 'none';
                collapseBtn.style.display = 'inline-block';
            }

            // Save expansion state
            sessionStorage.setItem(`expanded_common_${targetId}`, JSON.stringify({ category, subcategory, page, contractNumber }));
        })
        .catch(error => {
            console.error('Common names fetch error:', error);
            container.innerHTML = `<div class="common-level"><p>Error loading common names: ${error.message}</p></div>`;
            container.classList.remove('collapsed');
            container.classList.add('expanded');
            container.style.display = 'block';
            container.style.opacity = '1';
        })
        .finally(() => {
            hideLoading(key);
        });
}

// Note: Common function for Tabs 1 and 5
function loadSubcatData(originalCategory, normalizedCategory, targetId, page = 1) {
    console.log('loadSubcatData called with', { originalCategory, normalizedCategory, targetId, page });

    const container = document.getElementById(targetId);
    if (!container) {
        console.error(`Container with ID ${targetId} not found`);
        return;
    }

    // Check if the container is already loading to prevent double loading
    if (container.classList.contains('loading')) {
        console.log(`Container ${targetId} is already loading, skipping...`);
        return;
    }
    container.classList.add('loading');

    // Clear the container to prevent duplicate rendering
    container.innerHTML = '';
    hideOtherSubcats(normalizedCategory, normalizedCategory);
    showLoading(normalizedCategory);

    let url = `/tab/${window.cachedTabNum}/subcat_data?category=${encodeURIComponent(originalCategory)}&page=${page}`;
    const subcatFilter = document.getElementById(`subcat-filter-${normalizedCategory}`)?.value || '';
    const subcatSort = document.getElementById(`subcat-sort-${normalizedCategory}`)?.value || '';
    const statusFilter = document.getElementById('statusFilter')?.value || '';
    const binFilter = document.getElementById('binFilter')?.value || '';
    if (subcatFilter) {
        url += `&filter=${encodeURIComponent(subcatFilter)}`;
    }
    if (subcatSort) {
        url += `&sort=${encodeURIComponent(subcatSort)}`;
    }
    if (statusFilter) {
        url += `&statusFilter=${encodeURIComponent(statusFilter)}`;
    }
    if (binFilter) {
        url += `&binFilter=${encodeURIComponent(binFilter)}`;
    }

    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Subcategory fetch failed with status ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Subcategory data received:', data);
            let html = '';
            if (data.subcategories && data.subcategories.length > 0) {
                html += `
                    <div class="filter-sort-controls">
                        <input type="text" id="subcat-filter-${normalizedCategory}" placeholder="Filter subcategories..." value="${subcatFilter}" oninput="loadSubcatData('${originalCategory}', '${normalizedCategory}', '${targetId}', 1)">
                        <select id="subcat-sort-${normalizedCategory}" onchange="loadSubcatData('${originalCategory}', '${normalizedCategory}', '${targetId}', 1)">
                            <option value="">Sort By...</option>
                            <option value="subcategory_asc" ${subcatSort === 'subcategory_asc' ? 'selected' : ''}>Subcategory (A-Z)</option>
                            <option value="subcategory_desc" ${subcatSort === 'subcategory_desc' ? 'selected' : ''}>Subcategory (Z-A)</option>
                            <option value="total_items_asc" ${subcatSort === 'total_items_asc' ? 'selected' : ''}>Total Items (Low to High)</option>
                            <option value="total_items_desc" ${subcatSort === 'total_items_desc' ? 'selected' : ''}>Total Items (High to Low)</option>
                        </select>
                    </div>
                    <div class="subcat-level">
                        <table class="table table-bordered subcat-table mt-2" id="subcat-table-${normalizedCategory}">
                            <thead>
                                <tr>
                                    <th>Subcategory</th>
                                    <th>Total Items</th>
                                    <th>Items on Contracts</th>
                                    <th>Items in Service</th>
                                    <th>Items Available</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                `;

                data.subcategories.forEach(subcat => {
                    const subcatKey = `${normalizedCategory}_${subcat.subcategory.toLowerCase().replace(/[^a-z0-9]/g, '_')}`;
                    html += `
                        <tr class="subcat-row">
                            <td>${subcat.subcategory}</td>
                            <td>${subcat.total_items}</td>
                            <td>${subcat.items_on_contracts}</td>
                            <td>${subcat.items_in_service}</td>
                            <td>${subcat.items_available}</td>
                            <td>
                                <button class="btn btn-sm btn-secondary expand-btn" data-category="${originalCategory}" data-subcategory="${subcat.subcategory}" data-subcat-target-id="${subcatKey}">Expand</button>
                                <button class="btn btn-sm btn-secondary collapse-btn" style="display:none;" data-collapse-target="common-${subcatKey}">Collapse</button>
                                <button class="btn btn-sm btn-info print-btn" data-print-level="Subcategory" data-print-id="subcat-table-${subcatKey}">Print</button>
                                <div id="loading-${subcatKey}" style="display:none;" class="loading">Loading...</div>
                            </td>
                        </tr>
                        <tr>
                            <td colspan="6">
                                <div id="common-${subcatKey}" class="expandable collapsed"></div>
                            </td>
                        </tr>
                    `;
                });

                html += `
                            </tbody>
                        </table>
                    </div>
                `;

                if (data.total_subcats > data.per_page) {
                    const totalPages = Math.ceil(data.total_subcats / data.per_page);
                    html += `
                        <div class="pagination-controls">
                            <button class="btn btn-sm btn-secondary" onclick="loadSubcatData('${originalCategory}', '${normalizedCategory}', '${targetId}', ${page - 1})" ${page === 1 ? 'disabled' : ''}>Previous</button>
                            <span>Page ${page} of ${totalPages}</span>
                            <button class="btn btn-sm btn-secondary" onclick="loadSubcatData('${originalCategory}', '${normalizedCategory}', '${targetId}', ${page + 1})" ${page === totalPages ? 'disabled' : ''}>Next</button>
                        </div>
                    `;
                }
            } else {
                html = `<div class="subcat-level"><p>No subcategories found for this category.</p></div>`;
            }

            container.innerHTML = html;
            console.log('Rendered HTML for subcategories:', container.innerHTML); // Debug log to inspect DOM

            container.classList.remove('collapsed');
            container.classList.add('expanded');
            container.style.display = 'block';
            container.style.opacity = '1';
            container.classList.remove('loading');

            // Force reflow to ensure visibility
            container.offsetHeight; // Trigger reflow
            container.style.display = 'block';

            // Ensure the table body is visible
            const tableBody = container.querySelector('table.subcat-table tbody');
            if (tableBody) {
                tableBody.style.display = 'table-row-group';
                tableBody.style.visibility = 'visible';
                tableBody.style.opacity = '1';

                // Ensure all rows are visible
                const rows = tableBody.querySelectorAll('tr.subcat-row');
                rows.forEach(row => {
                    row.style.display = 'table-row';
                    row.style.visibility = 'visible';
                    row.style.opacity = '1';
                });
            } else {
                console.warn('Table body not found in container:', container);
            }

            // Debug: Log the parent row to inspect the expand/collapse buttons
            const parentRow = container.closest('tr');
            if (parentRow) {
                console.log('Parent row HTML:', parentRow.outerHTML);
            } else {
                console.warn('Parent row not found for container:', container);
            }

            // Fix selector to handle expand/collapse buttons
            const expandBtn = parentRow ? parentRow.querySelector(`button.expand-btn[data-target-id="subcat-${normalizedCategory}"]`) : null;
            const collapseBtn = expandBtn ? expandBtn.nextElementSibling : null;
            if (expandBtn && collapseBtn) {
                expandBtn.style.display = 'none';
                collapseBtn.style.display = 'inline-block';
            } else {
                console.warn('Expand/Collapse buttons not found in parent row for selector:', `button.expand-btn[data-target-id="subcat-${normalizedCategory}"]`);
            }

            // Save expansion state
            sessionStorage.setItem(`expanded_${targetId}`, JSON.stringify({ category: originalCategory, page }));
        })
        .catch(error => {
            console.error('Subcategory fetch error:', error);
            container.innerHTML = `<div class="subcat-level"><p>Error loading subcategories: ${error.message}</p></div>`;
            container.classList.remove('collapsed');
            container.classList.add('expanded');
            container.style.display = 'block';
            container.style.opacity = '1';
            container.classList.remove('loading');
        })
        .finally(() => {
            hideLoading(normalizedCategory);
        });
}

// Note: Tab 5 specific - Bulk update for all items under a common name
function bulkUpdateCommonName(category, subcategory, targetId, key) {
    const binLocation = document.getElementById(`bulk-bin-location-${key}`).value;
    const status = document.getElementById(`bulk-status-${key}`).value;

    if (!binLocation && !status) {
        alert('Please select a Bin Location or Status to update.');
        return;
    }

    fetch('/tab/5/bulk_update_common_name', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            category: category,
            subcategory: subcategory,
            common_name: document.querySelector(`#common-table-${key} tbody tr td:first-child`).textContent,
            bin_location: binLocation || undefined,
            status: status || undefined
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Bulk update error:', data.error);
            alert('Failed to bulk update: ' + data.error);
        } else {
            console.log('Bulk update successful:', data);
            alert('Bulk update successful!');
            loadItems(category, subcategory, document.querySelector(`#common-table-${key} tbody tr td:first-child`).textContent, targetId);
        }
    })
    .catch(error => {
        console.error('Bulk update error:', error);
        alert('Error during bulk update: ' + error.message);
    });
}

// Note: Tab 5 specific - Bulk update for selected items
function bulkUpdateSelectedItems(key) {
    const selectedItems = Array.from(document.querySelectorAll(`#item-table-${key} tbody input[type="checkbox"]:checked`))
        .map(checkbox => checkbox.value);

    if (selectedItems.length === 0) {
        alert('Please select at least one item to update.');
        return;
    }

    const binLocation = document.getElementById(`bulk-item-bin-location-${key}`).value;
    const status = document.getElementById(`bulk-item-status-${key}`).value;

    if (!binLocation && !status) {
        alert('Please select a Bin Location or Status to update.');
        return;
    }

    fetch('/tab/5/bulk_update_items', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            tag_ids: selectedItems,
            bin_location: binLocation || undefined,
            status: status || undefined
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Bulk update error:', data.error);
            alert('Failed to bulk update: ' + data.error);
        } else {
            console.log('Bulk update successful:', data);
            alert('Bulk update successful!');
            const category = document.querySelector(`#item-table-${key}`).closest('.common-level').querySelector('button[data-category]').getAttribute('data-category');
            const subcategory = document.querySelector(`#item-table-${key}`).closest('.common-level').querySelector('button[data-subcategory]').getAttribute('data-subcategory');
            const commonName = document.querySelector(`#common-table-${key} tbody tr td:first-child`).textContent;
            const targetId = document.querySelector(`#item-table-${key}`).closest('.expandable').id;
            loadItems(category, subcategory, commonName, targetId);
        }
    })
    .catch(error => {
        console.error('Bulk update error:', error);
        alert('Error during bulk update: ' + error.message);
    });
}

// Note: Tab 5 specific - Update dropdown visibility for bulk update
function updateBulkField(key, field) {
    const select = document.getElementById(`bulk-${field}-${key}`);
    if (select && select.value) {
        const otherField = field === 'bin_location' ? 'status' : 'bin_location';
        const otherSelect = document.getElementById(`bulk-${otherField}-${key}`);
        if (otherSelect) {
            otherSelect.value = '';
        }
    }
}

// Note: Tab 5 specific - Update individual item
function updateItem(tagId, key) {
    const binLocation = document.getElementById(`bin-location-${tagId}`).value;
    const status = document.getElementById(`status-${tagId}`).value;

    if (!binLocation && !status) {
        alert('Please select a Bin Location or Status to update.');
        return;
    }

    fetch('/tab/5/update_item', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            tag_id: tagId,
            bin_location: binLocation || undefined,
            status: status || undefined
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Update error:', data.error);
            alert('Failed to update item: ' + data.error);
        } else {
            console.log('Update successful:', data);
            alert('Update successful!');
            const category = document.querySelector(`#item-table-${key}`).closest('.common-level').querySelector('button[data-category]').getAttribute('data-category');
            const subcategory = document.querySelector(`#item-table-${key}`).closest('.common-level').querySelector('button[data-subcategory]').getAttribute('data-subcategory');
            const commonName = document.querySelector(`#common-table-${key} tbody tr td:first-child`).textContent;
            const targetId = document.querySelector(`#item-table-${key}`).closest('.expandable').id;
            loadItems(category, subcategory, commonName, targetId);
        }
    })
    .catch(error => {
        console.error('Update error:', error);
        alert('Error during update: ' + error.message);
    });
}

// Note: Common function for Tabs 1 and 5
function loadItems(category, subcategory, commonName, targetId, page = 1) {
    console.log('loadItems called with', { category, subcategory, commonName, targetId, page });

    if (!category || !subcategory || !commonName || !targetId) {
        console.error('Invalid parameters for loadItems:', { category, subcategory, commonName, targetId });
        return;
    }

    const container = document.getElementById(targetId);
    if (!container) {
        console.error(`Container with ID ${targetId} not found`);
        return;
    }

    // Check if the container is already loading to prevent double loading
    if (container.classList.contains('loading')) {
        console.log(`Container ${targetId} is already loading, skipping...`);
        return;
    }
    container.classList.add('loading');

    // Use the correct key for the loading indicator
    const key = targetId.split('-').slice(1).join('-'); // Match the loading indicator ID (e.g., "resale_testing_resale_test_resale")
    showLoading(key);
    hideOtherItems(targetId, targetId);

    let url = `/tab/${window.cachedTabNum}/data?common_name=${encodeURIComponent(commonName)}&page=${page}`;
    if (subcategory) {
        url += `&subcategory=${encodeURIComponent(subcategory)}`;
    }
    if (window.cachedTabNum == 2 || window.cachedTabNum == 4) {
        url += `&contract_number=${encodeURIComponent(category)}`;
    } else {
        url += `&category=${encodeURIComponent(category)}`;
    }

    const itemFilter = document.getElementById(`item-filter-${key}`)?.value || '';
    const itemSort = document.getElementById(`item-sort-${key}`)?.value || '';
    const statusFilter = document.getElementById('statusFilter')?.value || '';
    const binFilter = document.getElementById('binFilter')?.value || '';
    if (itemFilter) {
        url += `&filter=${encodeURIComponent(itemFilter)}`;
    }
    if (itemSort) {
        url += `&sort=${encodeURIComponent(itemSort)}`;
    }
    if (statusFilter) {
        url += `&statusFilter=${encodeURIComponent(statusFilter)}`;
    }
    if (binFilter) {
        url += `&binFilter=${encodeURIComponent(binFilter)}`;
    }

    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Items fetch failed with status ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            let html = '';
            if (data.items && data.items.length > 0) {
                let headers = [];
                if (window.cachedTabNum == 5) {
                    headers = ['Select', 'Tag ID', 'Common Name', 'Bin Location', 'Status', 'Last Contract', 'Last Scanned Date', 'Quality', 'Notes', 'Actions'];
                } else if (window.cachedTabNum == 1) {
                    headers = ['Tag ID', 'Common Name', 'Bin Location', 'Status', 'Last Contract', 'Last Scanned Date', 'Quality', 'Notes'];
                } else {
                    headers = ['Tag ID', 'Common Name', 'Bin Location', 'Status', 'Last Contract', 'Last Scanned Date'];
                }

                html += `
                    <div class="item-level-wrapper">
                        <div class="filter-sort-controls">
                            <input type="text" id="item-filter-${key}" placeholder="Filter items..." value="${itemFilter}" oninput="loadItems('${category}', '${subcategory || ''}', '${commonName}', '${targetId}', 1)">
                            <select id="item-sort-${key}" onchange="loadItems('${category}', '${subcategory || ''}', '${commonName}', '${targetId}', 1)">
                                <option value="">Sort By...</option>
                                <option value="tag_id_asc" ${itemSort === 'tag_id_asc' ? 'selected' : ''}>Tag ID (A-Z)</option>
                                <option value="tag_id_desc" ${itemSort === 'tag_id_desc' ? 'selected' : ''}>Tag ID (Z-A)</option>
                                <option value="last_scanned_date_desc" ${itemSort === 'last_scanned_date_desc' ? 'selected' : ''}>Last Scanned (Newest)</option>
                                <option value="last_scanned_date_asc" ${itemSort === 'last_scanned_date_asc' ? 'selected' : ''}>Last Scanned (Oldest)</option>
                            </select>
                `;

                if (window.cachedTabNum == 5) {
                    html += `
                        <div class="bulk-update-controls" style="margin-top: 10px;">
                            <select id="bulk-item-bin-location-${key}" onchange="updateBulkField('${key}', 'item-bin-location')">
                                <option value="">Update Bin Location...</option>
                                <option value="resale">resale</option>
                                <option value="sold">sold</option>
                                <option value="pack">pack</option>
                                <option value="burst">burst</option>
                            </select>
                            <select id="bulk-item-status-${key}" onchange="updateBulkField('${key}', 'item-status')">
                                <option value="">Update Status...</option>
                                <option value="Ready to Rent">Ready to Rent</option>
                            </select>
                            <button class="btn btn-sm btn-primary" onclick="bulkUpdateSelectedItems('${key}')">Bulk Update Selected</button>
                        </div>
                    `;
                }

                html += `
                        </div>
                        <table class="table table-bordered item-level mt-2" id="item-table-${key}">
                            <thead>
                                <tr>
                                    ${headers.map(header => `<th>${header}</th>`).join('')}
                                </tr>
                            </thead>
                            <tbody>
                `;

                data.items.forEach(item => {
                    const lastScanned = item.last_scanned_date ? new Date(item.last_scanned_date).toLocaleString() : 'N/A';
                    if (window.cachedTabNum == 5) {
                        html += `
                            <tr data-item-id="${item.tag_id}">
                                <td><input type="checkbox" value="${item.tag_id}" class="item-select"></td>
                                <td>${item.tag_id}</td>
                                <td>${item.common_name}</td>
                                <td>
                                    <select id="bin-location-${item.tag_id}">
                                        <option value="" ${!item.bin_location ? 'selected' : ''}>Select Bin Location</option>
                                        <option value="resale" ${item.bin_location === 'resale' ? 'selected' : ''}>resale</option>
                                        <option value="sold" ${item.bin_location === 'sold' ? 'selected' : ''}>sold</option>
                                        <option value="pack" ${item.bin_location === 'pack' ? 'selected' : ''}>pack</option>
                                        <option value="burst" ${item.bin_location === 'burst' ? 'selected' : ''}>burst</option>
                                    </select>
                                </td>
                                <td>
                                    <select id="status-${item.tag_id}">
                                        <option value="" ${!item.status ? 'selected' : ''}>Select Status</option>
                                        <option value="Ready to Rent" ${item.status === 'Ready to Rent' ? 'selected' : ''} ${item.status !== 'On Rent' && item.status !== 'Delivered' ? 'disabled' : ''}>Ready to Rent</option>
                                    </select>
                                </td>
                                <td>${item.last_contract_num || 'N/A'}</td>
                                <td>${lastScanned}</td>
                                <td>${item.quality || 'N/A'}</td>
                                <td>${item.notes || 'N/A'}</td>
                                <td>
                                    <button class="btn btn-sm btn-primary save-btn" onclick="updateItem('${item.tag_id}', '${key}')">Save</button>
                                </td>
                            </tr>
                        `;
                    } else if (window.cachedTabNum == 1) {
                        html += `
                            <tr data-item-id="${item.tag_id}">
                                <td>${item.tag_id}</td>
                                <td>${item.common_name}</td>
                                <td class="editable" onclick="showDropdown(event, this, 'bin-location', '${item.tag_id}', '${item.bin_location || ''}')">${item.bin_location || 'N/A'}</td>
                                <td class="editable" onclick="showDropdown(event, this, 'status', '${item.tag_id}', '${item.status}')">${item.status}</td>
                                <td>${item.last_contract_num || 'N/A'}</td>
                                <td>${lastScanned}</td>
                                <td>${item.quality || 'N/A'}</td>
                                <td>${item.notes || 'N/A'}</td>
                                <div id="dropdown-bin-location-${item.tag_id}" class="dropdown-menu">
                                    <a class="dropdown-item" href="#" onclick="selectOption(event, this, 'bin-location', '${item.tag_id}', 'resale')">resale</a>
                                    <a class="dropdown-item" href="#" onclick="selectOption(event, this, 'bin-location', '${item.tag_id}', 'sold')">sold</a>
                                    <a class="dropdown-item" href="#" onclick="selectOption(event, this, 'bin-location', '${item.tag_id}', 'pack')">pack</a>
                                    <a class="dropdown-item" href="#" onclick="selectOption(event, this, 'bin-location', '${item.tag_id}', 'burst')">burst</a>
                                </div>
                                <div id="dropdown-status-${item.tag_id}" class="dropdown-menu">
                                    <a class="dropdown-item" href="#" onclick="selectOption(event, this, 'status', '${item.tag_id}', 'Ready to Rent')" ${item.status !== 'On Rent' && item.status !== 'Delivered' ? 'style="pointer-events: none; color: #ccc;"' : ''}>Ready to Rent</a>
                                </div>
                            </tr>
                        `;
                    } else {
                        html += `
                            <tr>
                                <td>${item.tag_id}</td>
                                <td>${item.common_name}</td>
                                <td>${item.bin_location || 'N/A'}</td>
                                <td>${item.status}</td>
                                <td>${item.last_contract_num || 'N/A'}</td>
                                <td>${lastScanned}</td>
                            </tr>
                        `;
                    }
                });

                html += `
                            </tbody>
                        </table>
                    </div>
                `;
            } else {
                html = `<div class="item-level-wrapper"><p>No items found for this common name.</p></div>`;
            }

            container.innerHTML = html;
            container.classList.remove('collapsed');
            container.classList.add('expanded');
            container.style.display = 'block';
            container.style.opacity = '1';
            container.classList.remove('loading');

            // Force reflow to ensure visibility
            container.offsetHeight; // Trigger reflow
            container.style.display = 'block';

            const expandBtn = document.querySelector(`button.expand-btn[data-target-id="${targetId}"]`);
            const collapseBtn = expandBtn ? expandBtn.nextElementSibling : null;
            if (expandBtn && collapseBtn) {
                expandBtn.style.display = 'none';
                collapseBtn.style.display = 'inline-block';
            }

            // Save expansion state
            sessionStorage.setItem(`expanded_items_${targetId}`, JSON.stringify({ category, subcategory, commonName, page }));
        })
        .catch(error => {
            console.error('Items fetch error:', error);
            container.innerHTML = `<div class="item-level-wrapper"><p>Error loading items: ${error.message}</p></div>`;
            container.classList.remove('collapsed');
            container.classList.add('expanded');
            container.style.display = 'block';
            container.style.opacity = '1';
            container.classList.remove('loading');
        })
        .finally(() => {
            hideLoading(key);
        });
}

// Note: Used only in Tab 1
function showDropdown(event, cell, type, tagId, currentValue) {
    event.stopPropagation();
    console.log('showDropdown called with', { cell, type, tagId, currentValue });
    const dropdown = document.getElementById(`dropdown-${type}-${tagId}`);
    if (dropdown) {
        document.querySelectorAll('.dropdown-menu').forEach(d => {
            if (d !== dropdown) {
                d.classList.remove('show');
                d.style.display = 'none';
            }
        });
        dropdown.classList.add('show');
        dropdown.style.display = 'block';
        const rect = cell.getBoundingClientRect();
        dropdown.style.position = 'absolute';
        dropdown.style.left = `${rect.left + window.scrollX}px`;
        dropdown.style.top = `${rect.bottom + window.scrollY}px`;
        dropdown.style.zIndex = '1000';
        cell.setAttribute(`data-${type}`, currentValue);
    } else {
        console.error(`Dropdown not found for ${type} with tagId ${tagId}`);
    }
}

// Note: Used only in Tab 1
function selectOption(event, element, type, tagId, value) {
    event.preventDefault();
    event.stopPropagation();
    console.log('selectOption called with', { type, tagId, value });
    const cell = document.querySelector(`tr[data-item-id="${tagId}"] td.editable[onclick*="showDropdown(event, this, '${type}', '${tagId}'"]`);
    if (cell) {
        cell.textContent = value;
        cell.setAttribute(`data-${type}`, value);
        const dropdown = document.getElementById(`dropdown-${type}-${tagId}`);
        if (dropdown) {
            dropdown.classList.remove('show');
            dropdown.style.display = 'none';
        }
    }
}

// Note: Used only in Tab 1
function saveChanges(tagId) {
    console.log('saveChanges called for tagId:', tagId);
    const binLocationCell = document.querySelector(`tr[data-item-id="${tagId}"] td.editable[onclick*="showDropdown(event, this, 'bin-location', '${tagId}'"]`);
    const statusCell = document.querySelector(`tr[data-item-id="${tagId}"] td.editable[onclick*="showDropdown(event, this, 'status', '${tagId}'"]`);

    const newBinLocation = binLocationCell ? binLocationCell.getAttribute('data-bin-location') : null;
    const newStatus = statusCell ? statusCell.getAttribute('data-status') : null;

    if (newBinLocation) {
        fetch('/tab/5/update_bin_location', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                tag_id: tagId,
                bin_location: newBinLocation
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error updating bin location:', data.error);
                alert('Failed to update bin location: ' + data.error);
            } else {
                console.log('Bin location updated successfully:', data);
                alert('Bin location updated successfully!');
            }
        })
        .catch(error => {
            console.error('Error updating bin location:', error);
            alert('Error updating bin location: ' + error.message);
        });
    }

    if (newStatus) {
        fetch('/tab/5/update_status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                tag_id: tagId,
                status: newStatus
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error updating status:', data.error);
                alert('Failed to update status: ' + data.error);
            } else {
                console.log('Status updated successfully:', data);
                alert('Status updated successfully!');
                const itemsContainer = document.getElementById(`items-${tagId.split('-')[0]}`);
                if (itemsContainer) {
                    const category = itemsContainer.closest('.common-level').querySelector('button[data-category]').getAttribute('data-category');
                    const subcategory = itemsContainer.closest('.common-level').querySelector('button[data-subcategory]').getAttribute('data-subcategory');
                    const commonName = itemsContainer.closest('tr').querySelector('td:first-child').textContent;
                    loadItems(category, subcategory, commonName, `items-${tagId.split('-')[0]}`);
                }
            }
        })
        .catch(error => {
            console.error('Error updating status:', error);
            alert('Error updating status: ' + error.message);
        });
    }
}

// Note: Event listener for Tabs 1 and 5
document.addEventListener('DOMContentLoaded', function() {
    console.log('tab1_5.js: DOMContentLoaded event fired');

    // Only proceed if we're on Tab 1 or Tab 5
    if (window.cachedTabNum !== 1 && window.cachedTabNum !== 5) {
        console.log('Not Tab 1 or Tab 5, skipping event listeners');
        return;
    }

    // Remove any existing click event listeners to prevent duplicates
    document.removeEventListener('click', handleClick);
    document.addEventListener('click', handleClick);

    function handleClick(event) {
        const expandBtn = event.target.closest('.expand-btn');
        if (expandBtn) {
            event.stopPropagation();
            const category = expandBtn.getAttribute('data-category') || window.cachedTabNum;
            const subcategory = expandBtn.getAttribute('data-subcategory');
            const targetId = expandBtn.getAttribute('data-target-id');
            const subcatTargetId = expandBtn.getAttribute('data-subcat-target-id');
            const commonName = expandBtn.getAttribute('data-common-name');

            if (commonName && targetId) {
                loadItems(category, subcategory, commonName, targetId);
            } else if (subcategory && subcatTargetId) {
                loadCommonNames(category, subcategory, subcatTargetId);
            } else if (targetId) {
                const normalizedCategory = targetId.replace('subcat-', '');
                loadSubcatData(category, normalizedCategory, targetId);
            } else {
                console.error('Invalid parameters for handleClick: missing targetId or subcatTargetId', { category, targetId, subcatTargetId });
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

    // Hide dropdowns when clicking outside (used only in Tab 1)
    if (window.cachedTabNum === 1) {
        document.removeEventListener('click', handleDropdownClick);
        document.addEventListener('click', handleDropdownClick);

        function handleDropdownClick(event) {
            if (!event.target.closest('.editable') && !event.target.closest('.dropdown-menu')) {
                document.querySelectorAll('.dropdown-menu').forEach(dropdown => {
                    dropdown.classList.remove('show');
                    dropdown.style.display = 'none';
                });
            }
        }
    }

    // Define expandCategory for Tabs 1 and 5
    window.expandCategory = function(category, targetId, contractNumber = null, page = 1) {
        console.log('expandCategory called with', { category, targetId, contractNumber, page });
        if (!category || !targetId) {
            console.error('Invalid parameters for expandCategory:', { category, targetId });
            return;
        }
        const normalizedCategory = targetId.replace('subcat-', '');
        if (window.cachedTabNum == 2 || window.cachedTabNum == 4) {
            loadCommonNames(category, null, targetId, page, contractNumber);
        } else {
            loadSubcatData(category, normalizedCategory, targetId, page);
        }
    };
});