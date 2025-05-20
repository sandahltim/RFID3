console.log('tab3.js version: 2025-05-20-v6 loaded');

// Populate the common name dropdown for printing tags
function populateCommonNameDropdown() {
    const select = document.getElementById('commonNameSelect');
    if (!select) {
        console.warn('Common name dropdown not found');
        return;
    }

    fetch('/tab/3/pack_resale_common_names')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to fetch common names: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            select.innerHTML = '<option value="">Select Common Name</option>';
            data.common_names.forEach(name => {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = name;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error fetching common names for dropdown:', error);
            select.innerHTML = '<option value="">Error loading common names</option>';
        });
}

// Fetch and display CSV contents
function fetchCsvContents() {
    const tbody = document.getElementById('csvContentsBody');
    const updateStatusBtn = document.getElementById('updateStatusBtn');
    if (!tbody || !updateStatusBtn) {
        console.warn('CSV contents table or update status button not found');
        return;
    }

    fetch('/tab/3/csv_contents')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to fetch CSV contents: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            tbody.innerHTML = '';
            if (data.error) {
                tbody.innerHTML = `<tr><td colspan="5">${data.error}</td></tr>`;
                updateStatusBtn.disabled = true;
                return;
            }

            if (data.items.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5">No items in CSV</td></tr>';
                updateStatusBtn.disabled = true;
            } else {
                data.items.forEach(item => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${item.tag_id}</td>
                        <td>${item.common_name}</td>
                        <td>${item.status}</td>
                        <td>${item.bin_location}</td>
                        <td>
                            <button class="btn btn-sm btn-danger remove-btn" data-tag-id="${item.tag_id}">Remove</button>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
                updateStatusBtn.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error fetching CSV contents:', error);
            tbody.innerHTML = `<tr><td colspan="5">Error loading CSV: ${error.message}</td></tr>`;
            updateStatusBtn.disabled = true;
        });
}

// Handle sync to PC and status update for printing tags
function setupPrintTagsSection() {
    const syncBtn = document.getElementById('syncToPcBtn');
    const updateStatusBtn = document.getElementById('updateStatusBtn');
    const syncMessage = document.getElementById('syncMessage');

    if (!syncBtn || !updateStatusBtn || !syncMessage) {
        console.warn('Print tags section elements not found');
        return;
    }

    syncBtn.addEventListener('click', () => {
        const commonName = document.getElementById('commonNameSelect')?.value;
        const quantity = parseInt(document.getElementById('tagQuantity')?.value) || 0;

        if (!commonName) {
            alert('Please select a common name.');
            return;
        }
        if (quantity <= 0) {
            alert('Please enter a valid number of tags to print.');
            return;
        }

        syncBtn.disabled = true;
        syncMessage.textContent = 'Syncing to PC...';

        fetch('/tab/3/sync_to_pc', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                common_name: commonName,
                quantity: quantity
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Sync failed with status ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            syncMessage.textContent = `Successfully synced ${data.synced_items} items to PC.`;
            fetchCsvContents(); // Refresh CSV contents
        })
        .catch(error => {
            console.error('Sync error:', error);
            syncMessage.textContent = `Error syncing to PC: ${error.message}`;
        })
        .finally(() => {
            syncBtn.disabled = false;
        });
    });

    updateStatusBtn.addEventListener('click', () => {
        updateStatusBtn.disabled = true;
        syncMessage.textContent = 'Updating status...';

        fetch('/tab/3/update_synced_status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Status update failed with status ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            syncMessage.textContent = `Successfully updated status for ${data.updated_items} items.`;
            fetchCsvContents(); // Refresh CSV contents
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        })
        .catch(error => {
            console.error('Status update error:', error);
            syncMessage.textContent = `Error updating status: ${error.message}`;
            updateStatusBtn.disabled = false;
        });
    });

    // Handle remove buttons
    document.getElementById('csvContentsTable').addEventListener('click', (event) => {
        const removeBtn = event.target.closest('.remove-btn');
        if (!removeBtn) return;

        const tagId = removeBtn.getAttribute('data-tag-id');
        if (!tagId) {
            console.warn('No tag_id found for remove button');
            return;
        }

        if (!confirm(`Are you sure you want to remove item with Tag ID ${tagId}?`)) {
            return;
        }

        fetch('/tab/3/remove_csv_item', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ tag_id: tagId })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to remove item: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            syncMessage.textContent = data.message;
            fetchCsvContents(); // Refresh CSV contents
        })
        .catch(error => {
            console.error('Error removing item:', error);
            syncMessage.textContent = `Error removing item: ${error.message}`;
        });
    });
}

function applyTab3Filters() {
    const commonName = document.getElementById('commonNameFilterTab3').value;
    const date = document.getElementById('dateFilterTab3').value;
    const sort = document.getElementById('sortFilterTab3').value;

    const params = new URLSearchParams();
    if (commonName) params.append('common_name', commonName);
    if (date) params.append('date_last_scanned', date);
    if (sort) params.append('sort', sort);

    window.location.href = `/tab/3?${params.toString()}`;
}

function clearTab3Filters() {
    window.location.href = '/tab/3';
}

function updateStatusVisibility(tagId) {
    const select = document.getElementById(`status-${tagId}`);
    const saveBtn = select.closest('tr').querySelector('.save-btn');
    if (select.value !== select.options[0].value) {
        saveBtn.style.display = 'inline-block';
    } else {
        saveBtn.style.display = 'none';
    }
}

function updateStatus(tagId) {
    const newStatus = document.getElementById(`status-${tagId}`).value;

    fetch('/tab/3/update_status', {
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
            alert('Error: ' + data.error);
        } else {
            alert(data.message);
            window.location.reload();
        }
    })
    .catch(error => {
        console.error('Error updating status:', error);
        alert('Failed to update status');
    });
}

// Toggle crew section visibility
function toggleCrewSection(crewId) {
    console.log(`toggleCrewSection called for crewId: ${crewId}`);
    const content = document.getElementById(`crew-content-${crewId}`);
    const button = document.querySelector(`.toggle-crew[data-crew-id="${crewId}"]`);
    if (!content || !button) {
        console.warn(`Crew section elements not found for crewId: ${crewId}`);
        return;
    }
    if (content.classList.contains('collapsed')) {
        content.classList.remove('collapsed');
        content.classList.add('expanded');
        button.textContent = 'Show Less';
    } else {
        content.classList.remove('expanded');
        content.classList.add('collapsed');
        button.textContent = 'Show More';
    }
}

// Initialize pagination for a crew table
function initializeCrewPagination(crewId, totalItems, page = 1, perPage = 20) {
    const table = document.getElementById(`crew-table-${crewId}`);
    const paginationContainer = document.getElementById(`pagination-${crewId}`);
    const rowCount = document.getElementById(`row-count-${crewId}`);

    if (!table || !paginationContainer || !rowCount) {
        console.warn(`Pagination elements not found for crew: ${crewId}`);
        return;
    }

    // Update row count
    const start = (page - 1) * perPage + 1;
    const end = Math.min(page * perPage, totalItems);
    rowCount.textContent = `Showing ${start} to ${end} of ${totalItems} items`;

    // Render pagination controls
    renderPaginationControls(paginationContainer, totalItems, page, perPage, (newPage) => {
        fetchCrewItems(crewId, newPage, perPage);
    });
}

// Fetch paginated items for a crew
async function fetchCrewItems(crewId, page, perPage) {
    const commonName = document.getElementById('commonNameFilterTab3').value;
    const date = document.getElementById('dateFilterTab3').value;
    const sort = document.getElementById('sortFilterTab3').value;

    const params = new URLSearchParams({
        crew_id: crewId,
        page: page,
        per_page: perPage
    });
    if (commonName) params.append('common_name', commonName);
    if (date) params.append('date_last_scanned', date);
    if (sort) params.append('sort', sort);

    try {
        const response = await fetch(`/tab/3/crew_items?${params.toString()}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch crew items: ${response.status}`);
        }
        const data = await response.json();
        updateCrewTable(crewId, data.items, data.total_items, page, perPage);
    } catch (error) {
        console.error(`Error fetching crew items for ${crewId}:`, error);
    }
}

// Update crew table with new items
function updateCrewTable(crewId, items, totalItems, page, perPage) {
    const table = document.getElementById(`crew-table-${crewId}`);
    const tbody = table.querySelector('tbody');
    tbody.innerHTML = '';

    items.forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${item.tag_id}</td>
            <td>${item.common_name}</td>
            <td>
                <select id="status-${item.tag_id}" onchange="updateStatusVisibility('${item.tag_id}')">
                    <option value="${item.status}" selected>${item.status}</option>
                    <option value="Ready to Rent">Ready to Rent</option>
                    <option value="Sold">Sold</option>
                    <option value="Repair">Repair</option>
                    <option value="Needs to be Inspected">Needs to be Inspected</option>
                    <option value="Staged">Staged</option>
                    <option value="Wash">Wash</option>
                    <option value="Wet">Wet</option>
                </select>
            </td>
            <td>${item.bin_location}</td>
            <td>${item.last_contract_num}</td>
            <td class="date-last-scanned">${item.date_last_scanned}</td>
            <td>${item.location_of_repair}</td>
            <td>${item.repair_types.join(', ')}</td>
            <td>
                <button class="btn btn-sm btn-primary save-btn" onclick="updateStatus('${item.tag_id}')">Save</button>
            </td>
        `;
        tbody.appendChild(row);
    });

    // Reformat dates
    tbody.querySelectorAll('.date-last-scanned').forEach(cell => {
        const rawDate = cell.textContent.trim();
        cell.textContent = formatDate(rawDate);
    });

    // Update save button visibility
    tbody.querySelectorAll('select').forEach(select => {
        const tagId = select.id.replace('status-', '');
        updateStatusVisibility(tagId);
    });

    // Reinitialize pagination
    initializeCrewPagination(crewId, totalItems, page, perPage);
}

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    // Format timestamps in the crew tables
    document.querySelectorAll('.crew-table').forEach(table => {
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const dateCell = row.querySelector('.date-last-scanned');
            if (dateCell) {
                const rawDate = dateCell.textContent.trim();
                const formattedDate = formatDate(rawDate);
                dateCell.textContent = formattedDate;
            }
        });

        // Initialize pagination
        const crewId = table.getAttribute('data-crew-id');
        const rowCountElement = table.closest('.crew-section').querySelector('.row-count');
        if (rowCountElement) {
            const totalItemsMatch = rowCountElement.textContent.match(/of (\d+) items/);
            if (totalItemsMatch) {
                const totalItems = parseInt(totalItemsMatch[1]);
                initializeCrewPagination(crewId, totalItems);
            } else {
                console.warn(`Failed to parse total items for crew: ${crewId}`);
            }
        }
    });

    // Initialize save button visibility for status updates
    document.querySelectorAll('.crew-table select').forEach(select => {
        const tagId = select.id.replace('status-', '');
        updateStatusVisibility(tagId);
    });

    // Initialize toggle buttons
    document.querySelectorAll('.toggle-crew').forEach(button => {
        button.addEventListener('click', () => {
            const crewId = button.getAttribute('data-crew-id');
            toggleCrewSection(crewId);
        });
    });

    // Initialize the print tags section
    populateCommonNameDropdown();
    setupPrintTagsSection();
    fetchCsvContents(); // Initial CSV contents load
});