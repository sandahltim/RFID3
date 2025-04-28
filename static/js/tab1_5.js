console.log('tab1_5.js version: 2025-04-27-v21 loaded');

// Note: Common function for Tabs 1 and 5
function showLoading(targetId) {
    const loadingDiv = document.createElement('div');
    loadingDiv.id = `loading-${targetId}`;
    loadingDiv.className = 'loading-indicator';
    loadingDiv.textContent = 'Loading...';
    loadingDiv.style.display = 'block';
    const container = document.getElementById(targetId);
    if (container) {
        container.appendChild(loadingDiv);
    }
}

// Note: Common function for Tabs 1 and 5
function hideLoading(targetId) {
    const loadingDiv = document.getElementById(`loading-${targetId}`);
    if (loadingDiv) {
        loadingDiv.remove();
    }
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

        sessionStorage.removeItem(`expanded_${targetId}`);
    }
}

// Note: Common function for Tabs 1 and 5
function loadCommonNames(selectElement, page = 1) {
    const subcategory = selectElement.value;
    const category = selectElement.getAttribute('data-category');
    const targetId = selectElement.closest('tr').nextElementSibling.querySelector('.common-level').id;
    const categoryRow = selectElement.closest('tr');

    if (!subcategory) {
        collapseSection(targetId);
        // Reset category row data to original totals
        fetch(`/tab/${window.cachedTabNum}/subcat_data?category=${encodeURIComponent(category)}`)
            .then(response => response.json())
            .then(data => {
                const totalItems = data.subcategories.reduce((sum, subcat) => sum + subcat.total_items, 0);
                const itemsOnContracts = data.subcategories.reduce((sum, subcat) => sum + subcat.items_on_contracts, 0);
                const itemsInService = data.subcategories.reduce((sum, subcat) => sum + subcat.items_in_service, 0);
                const itemsAvailable = data.subcategories.reduce((sum, subcat) => sum + subcat.items_available, 0);
                categoryRow.cells[2].textContent = totalItems;
                categoryRow.cells[3].textContent = itemsOnContracts;
                categoryRow.cells[4].textContent = itemsInService;
                categoryRow.cells[5].textContent = itemsAvailable;
            })
            .catch(error => console.error('Error resetting category totals:', error));
        return;
    }

    console.log('loadCommonNames called with', { category, subcategory, targetId, page });

    if (!category || !subcategory || !targetId) {
        console.error('Invalid parameters for loadCommonNames:', { category, subcategory, targetId });
        return;
    }

    const container = document.getElementById(targetId);
    if (!container) {
        console.error(`Container with ID ${targetId} not found`);
        return;
    }

    showLoading(targetId);
    container.innerHTML = ''; // Clear previous content

    let url = `/tab/${window.cachedTabNum}/common_names?category=${encodeURIComponent(category)}&subcategory=${encodeURIComponent(subcategory)}&page=${page}`;

    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Common names fetch failed with status ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Common names data received:', data); // Debug log
            let html = '';
            if (data.common_names && data.common_names.length > 0) {
                // Calculate subcategory totals
                const totalItems = data.common_names.reduce((sum, item) => sum + item.total_items, 0);
                const itemsOnContracts = data.common_names.reduce((sum, item) => sum + item.items_on_contracts, 0);
                const itemsInService = data.common_names.reduce((sum, item) => sum + item.items_in_service, 0);
                const itemsAvailable = data.common_names.reduce((sum, item) => sum + item.items_available, 0);

                // Update category row with subcategory totals
                categoryRow.cells[2].textContent = totalItems;
                categoryRow.cells[3].textContent = itemsOnContracts;
                categoryRow.cells[4].textContent = itemsInService;
                categoryRow.cells[5].textContent = itemsAvailable;

                html += `
                    <table class="common-table" id="common-table-${targetId}">
                        <thead>
                            <tr>
                                <th>Common Name</th>
                                <th>Total Items</th>
                                <th>Items on Contracts</th>
                                <th>Items in Service</th>
                                <th>Items Available</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

                data.common_names.forEach(item => {
                    const rowId = `${targetId}_${item.name.replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '')}`;
                    html += `
                        <tr>
                            <td>${item.name}</td>
                            <td>${item.total_items}</td>
                            <td>${item.items_on_contracts}</td>
                            <td>${item.items_in_service}</td>
                            <td>${item.items_available}</td>
                            <td>
                                <div class="btn-group">
                                    <button class="btn btn-sm btn-secondary expand-btn" data-category="${category}" data-subcategory="${subcategory}" data-common-name="${item.name}" data-target-id="items-${rowId}">Expand Items</button>
                                    <button class="btn btn-sm btn-secondary collapse-btn" style="display:none;" data-collapse-target="items-${rowId}">Collapse</button>
                                    <button class="btn btn-sm btn-info print-btn" data-print-level="Common Name" data-print-id="common-table-${targetId}" data-common-name="${item.name}" data-category="${category}" data-subcategory="${subcategory}">Print Aggregate</button>
                                    <button class="btn btn-sm btn-info print-full-btn" data-common-name="${item.name}" data-category="${category}" data-subcategory="${subcategory}">Print Full List</button>
                                </div>
                            </td>
                        </tr>
                        <tr>
                            <td colspan="6">
                                <div id="items-${rowId}" class="expandable collapsed"></div>
                            </td>
                        </tr>
                    `;
                });

                html += `
                        </tbody>
                    </table>
                `;

                if (data.total_common_names > data.per_page) {
                    const totalPages = Math.ceil(data.total_common_names / data.per_page);
                    html += `
                        <div class="pagination-controls">
                            <button class="btn btn-sm btn-secondary" onclick="loadCommonNames(this.closest('.common-level').previousElementSibling.querySelector('.subcategory-select'), ${data.page - 1})" ${data.page === 1 ? 'disabled' : ''}>Previous</button>
                            <span>Page ${data.page} of ${totalPages}</span>
                            <button class="btn btn-sm btn-secondary" onclick="loadCommonNames(this.closest('.common-level').previousElementSibling.querySelector('.subcategory-select'), ${data.page + 1})" ${data.page === totalPages ? 'disabled' : ''}>Next</button>
                        </div>
                    `;
                }
            } else {
                html = `<p>No common names found for this subcategory.</p>`;
            }

            container.innerHTML = html;
            container.classList.remove('collapsed');
            container.classList.add('expanded');
            container.style.display = 'block';
            container.style.opacity = '1';

            // Apply global filter to the newly loaded table
            applyFilterToAllLevels();
        })
        .catch(error => {
            console.error('Common names fetch error:', error);
            container.innerHTML = `<p>Error loading common names: ${error.message}</p>`;
            container.classList.remove('collapsed');
            container.classList.add('expanded');
            container.style.display = 'block';
            container.style.opacity = '1';
        })
        .finally(() => {
            hideLoading(targetId);
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
function updateItem(tagId, key, category, subcategory, commonName, targetId) {
    const binLocation = document.getElementById(`bin-location-${tagId}`).value;
    const status = document.getElementById(`status-${tagId}`).value;

    if (!binLocation && !status) {
        alert('Please select a Bin Location or Status to update.');
        return;
    }

    const promises = [];

    // Update bin location if provided
    if (binLocation) {
        promises.push(
            fetch('/tab/5/update_bin_location', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    tag_id: tagId,
                    bin_location: binLocation
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(`Failed to update bin location: ${data.error}`);
                }
                return { field: 'bin_location', data };
            })
        );
    }

    // Update status if provided
    if (status) {
        promises.push(
            fetch('/tab/5/update_status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    tag_id: tagId,
                    status: status
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(`Failed to update status: ${data.error}`);
                }
                return { field: 'status', data };
            })
        );
    }

    Promise.all(promises)
        .then(results => {
            console.log('Update successful:', results);
            alert('Update successful!');
            loadItems(category, subcategory, commonName, targetId);
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

    if (container.classList.contains('loading')) {
        console.log(`Container ${targetId} is already loading, skipping...`);
        return;
    }
    container.classList.add('loading');

    const key = targetId;
    showLoading(key);

    let url = `/tab/${window.cachedTabNum}/data?common_name=${encodeURIComponent(commonName)}&page=${page}&subcategory=${encodeURIComponent(subcategory)}&category=${encodeURIComponent(category)}`;

    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Items fetch failed with status ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Items data received:', data); // Debug log
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
                        <table class="item-table" id="item-table-${key}">
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
                        const currentStatus = item.status || 'N/A';
                        const canSetReadyToRent = currentStatus === 'On Rent' || currentStatus === 'Delivered' || currentStatus === 'Sold';
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
                                        <option value="${currentStatus}" selected>${currentStatus}</option>
                                        <option value="Ready to Rent" ${canSetReadyToRent ? '' : 'disabled'}>Ready to Rent</option>
                                        <option value="Sold">Sold</option>
                                        <option value="On Rent" disabled>On Rent</option>
                                        <option value="Delivered" disabled>Delivered</option>
                                    </select>
                                </td>
                                <td>${item.last_contract_num || 'N/A'}</td>
                                <td>${lastScanned}</td>
                                <td>${item.quality || 'N/A'}</td>
                                <td>${item.notes || 'N/A'}</td>
                                <td>
                                    <button class="btn btn-sm btn-primary save-btn" onclick="updateItem('${item.tag_id}', '${key}', '${category}', '${subcategory}', '${item.common_name}', '${targetId}')">Save</button>
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
                `;

                // Add pagination for items if total_items exceeds per_page
                if (data.total_items > data.per_page) {
                    const totalPages = Math.ceil(data.total_items / data.per_page);
                    html += `
                        <div class="pagination-controls">
                            <button class="btn btn-sm btn-secondary" onclick="loadItems('${category}', '${subcategory}', '${commonName}', '${targetId}', ${data.page - 1})" ${data.page === 1 ? 'disabled' : ''}>Previous</button>
                            <span>Page ${data.page} of ${totalPages}</span>
                            <button class="btn btn-sm btn-secondary" onclick="loadItems('${category}', '${subcategory}', '${commonName}', '${targetId}', ${data.page + 1})" ${data.page === totalPages ? 'disabled' : ''}>Next</button>
                        </div>
                    `;
                }

                html += `
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

            const expandBtn = document.querySelector(`button.expand-btn[data-target-id="${targetId}"]`);
            const collapseBtn = expandBtn ? expandBtn.nextElementSibling : null;
            if (expandBtn && collapseBtn) {
                expandBtn.style.display = 'none';
                collapseBtn.style.display = 'inline-block';
            }

            sessionStorage.setItem(`expanded_items_${targetId}`, JSON.stringify({ category, subcategory, commonName, page }));

            // Apply global filter to the newly loaded table
            applyFilterToAllLevels();
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

    if (window.cachedTabNum !== 1 && window.cachedTabNum !== 5) {
        console.log('Not Tab 1 or Tab 5, skipping event listeners');
        return;
    }

    document.removeEventListener('click', handleClick);
    document.addEventListener('click', handleClick);

    function handleClick(event) {
        const expandBtn = event.target.closest('.expand-btn');
        if (expandBtn) {
            event.stopPropagation();
            const category = expandBtn.getAttribute('data-category');
            const subcategory = expandBtn.getAttribute('data-subcategory');
            const commonName = expandBtn.getAttribute('data-common-name');
            const targetId = expandBtn.getAttribute('data-target-id');

            if (commonName && targetId) {
                loadItems(category, subcategory, commonName, targetId);
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
});