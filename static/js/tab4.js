import { getCachedTabNum, setCachedTabNum } from './state.js';
console.log('tab4.js version: 2025-05-29-v7 loaded');

/**
 * Tab4.js: Logic for Tab 4 (Laundry Contracts).
 * Dependencies: common.js (for formatDate, showLoading, hideLoading, collapseSection, applyFilterToTable).
 * Updated: Fixed item dropdown population for hand-counted item removal.
 */

// Expand category for Tab 4
window.expandCategory = function(category, targetId, contractNumber, page = 1, tabNum = 4) {
    console.log('expandCategory:', { category, targetId, contractNumber, page, tabNum });

    const targetElement = document.getElementById(targetId);
    if (!targetElement) {
        console.error(`Target ${targetId} not found`);
        return;
    }

    const parentRow = targetElement.closest('tr').previousElementSibling;
    const expandBtn = parentRow.querySelector('.expand-btn');
    const collapseBtn = parentRow.querySelector('.collapse-btn');

    if (targetElement.classList.contains('expanded') && page === 1) {
        console.log(`Collapsing ${targetId}`);
        collapseSection(targetId);
        if (expandBtn && collapseBtn) {
            expandBtn.style.display = 'inline-block';
            collapseBtn.style.display = 'none';
        }
        return;
    }

    const loadingSuccess = showLoading(targetId);
    const url = `/tab/4/common_names?contract_number=${encodeURIComponent(contractNumber)}&page=${page}`;
    console.log(`Fetching common names: ${url}`);

    fetch(url)
        .then(response => {
            console.log(`Common names fetch status: ${response.status}`);
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`Common names fetch failed: ${response.status} - ${text}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Common names data:', data);
            if (data.error) {
                console.error('Common names error:', data.error);
                targetElement.innerHTML = `<p>Error: ${data.error}</p>`;
                return;
            }

            const commonNames = data.common_names || [];
            const totalCommonNames = data.total_common_names || 0;
            const perPage = data.per_page || 10;
            const currentPage = data.page || 1;

            let html = `
                <div class="subcategory-container">
                    <table class="table table-bordered table-hover common-table">
                        <thead class="thead-dark">
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
                const commonId = `${contractNumber}-${common.name.replace(/[^a-z0-9]/g, '_')}`;
                const escapedCommonName = common.name.replace(/'/g, "\\'").replace(/"/g, '\\"');
                html += `
                    <tr>
                        <td class="expandable-cell" onclick="window.expandItems('${contractNumber}', '${escapedCommonName}', 'items-${commonId}', 1, 4)">${common.name}</td>
                        <td>${common.on_contracts}</td>
                        <td>${common.is_hand_counted ? 'N/A' : common.total_items_inventory}</td>
                        <td>
                            <button class="btn btn-sm btn-secondary expand-btn" data-common-name="${escapedCommonName}" data-target-id="items-${commonId}" data-contract-number="${contractNumber}">Expand</button>
                            <button class="btn btn-sm btn-secondary collapse-btn" data-collapse-target="items-${commonId}" style="display:none;">Collapse</button>
                            <button class="btn btn-sm btn-info print-common-name-btn" data-print-level="Common Name" data-print-id="items-${commonId}" data-common-name="${escapedCommonName}" data-category="${contractNumber}">Print</button>
                            <button class="btn btn-sm btn-info print-full-btn" data-common-name="${escapedCommonName}" data-category="${contractNumber}">Print Full List</button>
                            <div id="loading-items-${commonId}" style="display:none;" class="loading-indicator">Loading...</div>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="4">
                            <div id="items-${commonId}" class="expandable collapsed item-level"></div>
                        </td>
                    </tr>
                `;
            });

            html += `</tbody></table></div>`;

            if (totalCommonNames > perPage) {
                const totalPages = Math.ceil(totalCommonNames / perPage);
                const escapedCategory = category ? category.replace(/'/g, "\\'").replace(/"/g, '\\"') : '';
                html += `
                    <div class="pagination-controls mt-2">
                        <button class="btn btn-sm btn-secondary" onclick="window.expandCategory('${escapedCategory}', '${targetId}', '${contractNumber}', ${currentPage - 1}, 4)" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>
                        <span class="mx-2">Page ${currentPage} of ${totalPages}</span>
                        <button class="btn btn-sm btn-secondary" onclick="window.expandCategory('${escapedCategory}', '${targetId}', '${contractNumber}', ${currentPage + 1}, 4)" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>
                    </div>
                `;
            }

            targetElement.innerHTML = html;
            targetElement.classList.remove('collapsed');
            targetElement.classList.add('expanded');
            targetElement.style.display = 'block';
            targetElement.style.opacity = '1';
            targetElement.style.visibility = 'visible';

            if (expandBtn && collapseBtn) {
                expandBtn.style.display = 'none';
                collapseBtn.style.display = 'inline-block';
            }

            console.log('Common names container styles:', {
                classList: targetElement.classList.toString(),
                display: targetElement.style.display,
                opacity: targetElement.style.opacity,
                visibility: window.getComputedStyle(targetElement).visibility
            });

            const table = targetElement.querySelector('.common-table');
            if (table) {
                applyFilterToTable(table);
            }

            sessionStorage.setItem(`expanded_${targetId}`, JSON.stringify({ category, page }));
        })
        .catch(error => {
            console.error('Common names error:', error.message);
            targetElement.innerHTML = `<p>Error: ${error.message}</p>`;
            targetElement.classList.remove('collapsed');
            targetElement.classList.add('expanded');
            targetElement.style.display = 'block';
            targetElement.style.opacity = '1';
            targetElement.style.visibility = 'visible';
        })
        .finally(() => {
            if (loadingSuccess) hideLoading(targetId);
        });
};

// Expand items for Tab 4
window.expandItems = function(contractNumber, commonName, targetId, page = 1, tabNum = 4) {
    console.log('expandItems:', { contractNumber, commonName, targetId, page, tabNum });

    const targetElement = document.getElementById(targetId);
    if (!targetElement) {
        console.error(`Target ${targetId} not found`);
        return;
    }

    const parentRow = targetElement.closest('tr').previousElementSibling;
    const expandBtn = parentRow.querySelector('.expand-btn');
    const collapseBtn = parentRow.querySelector('.collapse-btn');

    if (targetElement.classList.contains('expanded') && page === 1) {
        console.log(`Collapsing ${targetId}`);
        collapseSection(targetId);
        if (expandBtn && collapseBtn) {
            expandBtn.style.display = 'inline-block';
            collapseBtn.style.display = 'none';
        }
        return;
    }

    const commonId = targetId.replace('items-', '');
    const loadingSuccess = showLoading(`loading-items-${commonId}`);
    targetElement.innerHTML = '';

    const url = `/tab/4/data?contract_number=${encodeURIComponent(contractNumber)}&common_name=${encodeURIComponent(commonName)}&page=${page}`;
    console.log(`Fetching items: ${url}`);

    fetch(url)
        .then(response => {
            console.log(`Items fetch status: ${response.status}`);
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`Items fetch failed: ${response.status} - ${text}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Items data:', data);
            if (data.error) {
                console.error('Items error:', data.error);
                targetElement.innerHTML = `<p>Error: ${data.error}</p>`;
                return;
            }

            const items = data.items || [];
            const totalItems = data.total_items || 0;
            const perPage = data.per_page || 10;
            const currentPage = data.page || 1;

            let html = `
                <div class="item-level-wrapper ml-4">
                    <table class="table table-bordered table-hover item-table">
                        <thead class="thead-dark">
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
                const formattedScanDate = formatDate(item.last_scanned_date);
                html += `
                    <tr>
                        <td>${item.tag_id}</td>
                        <td>${item.common_name}</td>
                        <td>${item.bin_location || 'N/A'}</td>
                        <td>${item.status}</td>
                        <td>${item.last_contract_num || 'N/A'}</td>
                        <td>${formattedScanDate}</td>
                    </tr>
                `;
            });

            html += `</tbody></table></div>`;

            if (totalItems > perPage) {
                const totalPages = Math.ceil(totalItems / perPage);
                const escapedCommonName = commonName.replace(/'/g, "\\'").replace(/"/g, '\\"');
                html += `
                    <div class="pagination-controls mt-2 ml-4">
                        <button class="btn btn-sm btn-secondary" onclick="window.expandItems('${contractNumber}', '${escapedCommonName}', '${targetId}', ${currentPage - 1}, 4)" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>
                        <span class="mx-2">Page ${currentPage} of ${totalPages}</span>
                        <button class="btn btn-sm btn-secondary" onclick="window.expandItems('${contractNumber}', '${escapedCommonName}', '${targetId}', ${currentPage + 1}, 4)" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>
                    </div>
                `;
            }

            targetElement.innerHTML = html;
            targetElement.classList.remove('collapsed');
            targetElement.classList.add('expanded');
            targetElement.style.display = 'block';
            targetElement.style.opacity = '1';
            targetElement.style.visibility = 'visible';

            if (expandBtn && collapseBtn) {
                expandBtn.style.display = 'none';
                collapseBtn.style.display = 'inline-block';
            }

            console.log('Items container styles:', {
                classList: targetElement.classList.toString(),
                display: targetElement.style.display,
                opacity: targetElement.style.opacity,
                visibility: window.getComputedStyle(targetElement).visibility
            });

            const table = targetElement.querySelector('.item-table');
            if (table) {
                applyFilterToTable(table);
            }

            sessionStorage.setItem(`expanded_items_${targetId}`, JSON.stringify({ contractNumber, commonName, page }));
        })
        .catch(error => {
            console.error('Items error:', error.message);
            targetElement.innerHTML = `<p>Error: ${error.message}</p>`;
            targetElement.classList.remove('collapsed');
            targetElement.classList.add('expanded');
            targetElement.style.display = 'block';
            targetElement.style.opacity = '1';
            targetElement.style.visibility = 'visible';
        })
        .finally(() => {
            if (loadingSuccess) hideLoading(`loading-items-${commonId}`);
        });
};

// Hand-counted items functions
function formatDate(isoDateString) {
    if (!isoDateString || isoDateString === 'N/A') return 'N/A';
    try {
        const date = new Date(isoDateString);
        if (isNaN(date.getTime())) return isoDateString;
        const days = ['Sun', 'Mon', 'Tues', 'Wed', 'Thurs', 'Fri', 'Sat'];
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec'];
        const dayName = days[date.getDay()];
        const monthName = months[date.getMonth()];
        const day = date.getDate();
        const year = date.getFullYear();
        let hours = date.getHours();
        const minutes = date.getMinutes().toString().padStart(2, '0');
        const ampm = hours >= 12 ? 'pm' : 'am';
        hours = hours % 12 || 12;
        return `${dayName}, ${monthName} ${day} ${year} ${hours}:${minutes} ${ampm}`;
    } catch (error) {
        console.error('Error formatting date:', error);
        return isoDateString;
    }
}

function refreshTab() {
    window.location.reload();
}

function filterHandCountedItems() {
    const contractNumber = document.getElementById('hand-counted-contract-number').value;
    const url = contractNumber ? `/tab/4/hand_counted_items?contract_number=${encodeURIComponent(contractNumber)}` : '/tab/4/hand_counted_items';
    if (typeof htmx !== 'undefined') {
        htmx.ajax('GET', url, '#hand-counted-items');
    } else {
        console.warn('HTMX not available, using fallback');
        fetch(url)
            .then(response => response.text())
            .then(html => {
                const target = document.getElementById('hand-counted-items');
                if (target) {
                    target.innerHTML = html;
                    const rows = target.querySelectorAll('tr');
                    rows.forEach(row => {
                        const timestampCell = row.querySelector('td:nth-child(5)');
                        if (timestampCell) {
                            const rawDate = timestampCell.textContent.trim();
                            timestampCell.textContent = formatDate(rawDate);
                        }
                    });
                }
            })
            .catch(error => {
                console.error('Error fetching hand-counted items:', error);
                document.getElementById('hand-counted-items').innerHTML = '<tr><td colspan="6">Error loading hand-counted items.</td></tr>';
            });
    }
}

window.toggleNewContractInput = function toggleNewContractInput() {
    const contractDropdown = document.getElementById('hand-counted-contract-number');
    const newContractInput = document.getElementById('new-contract-number');
    if (newContractInput.style.display === 'none') {
        fetch('/tab/4/next_contract_number')
            .then(response => response.json())
            .then(data => {
                newContractInput.value = data.next_contract_number || 'L1';
            })
            .catch(() => {
                newContractInput.value = 'L1';
            });
        newContractInput.style.display = 'block';
        contractDropdown.disabled = true;
    } else {
        newContractInput.style.display = 'none';
        newContractInput.value = '';
        contractDropdown.disabled = false;
        window.updateItemDropdown();
    }
};
window.handleItemSelection = function handleItemSelection() {
    const itemDropdown = document.getElementById('hand-counted-item-name');
    const newItemInput = document.getElementById('new-item-name');
    if (itemDropdown.value === '__other') {
        newItemInput.style.display = 'block';
    } else {
        newItemInput.style.display = 'none';
        newItemInput.value = '';
    }
};

window.updateItemDropdown = function updateItemDropdown() {
    const contractDropdown = document.getElementById('hand-counted-contract-number');
    const itemDropdown = document.getElementById('hand-counted-item-name');
    const newContractInput = document.getElementById('new-contract-number');
    const contractNumber = newContractInput.style.display === 'block' ? newContractInput.value : contractDropdown.value;
    itemDropdown.innerHTML = '<option value="">Select Item...</option>';
    fetch('/tab/4/hand_counted_catalog')
        .then(response => {
            if (!response.ok) throw new Error(`Failed to fetch catalog: ${response.status}`);
            return response.json();
        })
        .then(catalogData => {
            const catalogItems = catalogData.items || [];
            const contractItems = {};
            const populateOptions = () => {
                const uniqueNames = new Set([...catalogItems, ...Object.keys(contractItems)]);
                uniqueNames.forEach(name => {
                    if (name.toLowerCase() === 'other') return;
                    const option = document.createElement('option');
                    const qty = contractItems[name];
                    option.value = name;
                    option.textContent = qty ? `${name} (Qty: ${qty})` : name;
                    itemDropdown.appendChild(option);
                });
                const otherOption = document.createElement('option');
                otherOption.value = '__other';
                otherOption.textContent = 'Other';
                itemDropdown.appendChild(otherOption);
            };

            if (contractNumber) {
                console.log(`Fetching items for contract ${contractNumber}`);
                fetch(`/tab/4/hand_counted_items_by_contract?contract_number=${encodeURIComponent(contractNumber)}`)
                    .then(response => {
                        if (!response.ok) throw new Error(`Failed to fetch items: ${response.status}`);
                        return response.json();
                    })
                    .then(data => {
                        if (data.items && Array.isArray(data.items)) {
                            data.items.forEach(item => {
                                contractItems[item.item_name] = item.quantity;
                            });
                        }
                        populateOptions();
                    })
                    .catch(error => {
                        console.error('Error fetching hand-counted items:', error);
                        populateOptions();
                    });
            } else {
                populateOptions();
            }
        })
        .catch(error => {
            console.error('Error fetching hand-counted catalog:', error);
        })
        .finally(() => {
            handleItemSelection();
        });
};

// Global variable to store categorized items
let categorizedItemsData = {};

// Load categorized items data on page load
window.loadCategorizedItems = function loadCategorizedItems() {
    fetch('/tab/4/hand_counted_catalog_categorized')
        .then(response => {
            if (!response.ok) throw new Error(`Failed to fetch categorized catalog: ${response.status}`);
            return response.json();
        })
        .then(data => {
            categorizedItemsData = data.categories || {};
            populateCategoryDropdown();
            console.log('Loaded categorized items data:', categorizedItemsData);
        })
        .catch(error => {
            console.error('Error fetching categorized hand-counted catalog:', error);
            // Fallback to original dropdown
            window.updateItemDropdown();
        });
};

// Populate the category dropdown
function populateCategoryDropdown() {
    const categoryDropdown = document.getElementById('hand-counted-category');
    categoryDropdown.innerHTML = '<option value="">Select Category...</option>';
    
    Object.keys(categorizedItemsData).sort().forEach(category => {
        const option = document.createElement('option');
        option.value = category;
        option.textContent = category;
        categoryDropdown.appendChild(option);
    });
}

// Update subcategory dropdown based on selected category
window.updateSubcategoryDropdown = function updateSubcategoryDropdown() {
    const categoryDropdown = document.getElementById('hand-counted-category');
    const subcategoryDropdown = document.getElementById('hand-counted-subcategory');
    const itemDropdown = document.getElementById('hand-counted-item-name');
    
    // Clear subcategory and item dropdowns
    subcategoryDropdown.innerHTML = '<option value="">Select Subcategory...</option>';
    itemDropdown.innerHTML = '<option value="">Select Item...</option>';
    
    const selectedCategory = categoryDropdown.value;
    if (!selectedCategory || !categorizedItemsData[selectedCategory]) {
        return;
    }
    
    // Populate subcategory dropdown
    Object.keys(categorizedItemsData[selectedCategory]).sort().forEach(subcategory => {
        const option = document.createElement('option');
        option.value = subcategory;
        option.textContent = subcategory;
        subcategoryDropdown.appendChild(option);
    });
};

// Update item dropdown based on selected category and subcategory
window.updateItemDropdownHierarchical = function updateItemDropdownHierarchical() {
    const categoryDropdown = document.getElementById('hand-counted-category');
    const subcategoryDropdown = document.getElementById('hand-counted-subcategory');
    const itemDropdown = document.getElementById('hand-counted-item-name');
    const contractDropdown = document.getElementById('hand-counted-contract-number');
    const newContractInput = document.getElementById('new-contract-number');
    
    // Clear item dropdown
    itemDropdown.innerHTML = '<option value="">Select Item...</option>';
    
    const selectedCategory = categoryDropdown.value;
    const selectedSubcategory = subcategoryDropdown.value;
    
    if (!selectedCategory || !selectedSubcategory || 
        !categorizedItemsData[selectedCategory] || 
        !categorizedItemsData[selectedCategory][selectedSubcategory]) {
        return;
    }
    
    const items = categorizedItemsData[selectedCategory][selectedSubcategory];
    const contractNumber = newContractInput.style.display === 'block' ? newContractInput.value : contractDropdown.value;
    
    // Get existing quantities for the contract if available
    if (contractNumber) {
        fetch(`/tab/4/hand_counted_items_by_contract?contract_number=${encodeURIComponent(contractNumber)}`)
            .then(response => {
                if (!response.ok) throw new Error(`Failed to fetch contract items: ${response.status}`);
                return response.json();
            })
            .then(data => {
                const contractItems = {};
                if (data.items && Array.isArray(data.items)) {
                    data.items.forEach(item => {
                        contractItems[item.item_name] = item.quantity;
                    });
                }
                
                // Populate item dropdown with quantities if available
                items.forEach(itemName => {
                    const option = document.createElement('option');
                    option.value = itemName;
                    const qty = contractItems[itemName];
                    option.textContent = qty ? `${itemName} (Qty: ${qty})` : itemName;
                    itemDropdown.appendChild(option);
                });
                
                // Add "Other" option
                const otherOption = document.createElement('option');
                otherOption.value = '__other';
                otherOption.textContent = 'Other';
                itemDropdown.appendChild(otherOption);
            })
            .catch(error => {
                console.error('Error fetching contract items:', error);
                // Populate without quantities
                items.forEach(itemName => {
                    const option = document.createElement('option');
                    option.value = itemName;
                    option.textContent = itemName;
                    itemDropdown.appendChild(option);
                });
                
                const otherOption = document.createElement('option');
                otherOption.value = '__other';
                otherOption.textContent = 'Other';
                itemDropdown.appendChild(otherOption);
            });
    } else {
        // No contract selected, just populate items
        items.forEach(itemName => {
            const option = document.createElement('option');
            option.value = itemName;
            option.textContent = itemName;
            itemDropdown.appendChild(option);
        });
        
        const otherOption = document.createElement('option');
        otherOption.value = '__other';
        otherOption.textContent = 'Other';
        itemDropdown.appendChild(otherOption);
    }
    
    handleItemSelection();
};

window.addHandCountedItem = function addHandCountedItem() {
    // Use add-mode specific IDs
    const contractDropdown = document.getElementById('add-contract-number');
    const newContractInput = document.getElementById('add-new-contract-number');
    const itemDropdown = document.getElementById('add-item-name');
    const newItemInput = document.getElementById('add-new-item-name');
    const quantityInput = document.getElementById('add-quantity');
    const employeeInput = document.getElementById('add-employee');
    const contractNumber = newContractInput.style.display === 'block' ? newContractInput.value : contractDropdown.value;
    const itemValue = itemDropdown.value;
    const itemName = itemValue === '__other' ? newItemInput.value : itemValue;
    const quantity = parseInt(quantityInput.value);
    const employeeName = employeeInput.value;
    if (!contractNumber || !itemName || !quantity || quantity < 1 || !employeeName) {
        alert('Please fill in all fields: Contract Number, Item Name, Quantity (positive number), and Employee Name.');
        return;
    }
    if (itemValue === '__other' && !newItemInput.value) {
        alert('Please enter an item name for "Other".');
        return;
    }
    if (!contractNumber.startsWith('L')) {
        alert('Contract Number must start with "L" for Laundry Contracts.');
        return;
    }
    fetch('/tab/4/add_hand_counted_item', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            contract_number: contractNumber,
            item_name: itemName,
            quantity: quantity,
            action: 'Added',
            employee_name: employeeName
        })
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            alert(data.message);
            if (newContractInput.style.display === 'block') window.toggleNewContractInput();
            contractDropdown.value = '';
            itemDropdown.value = '';
            quantityInput.value = '';
            employeeInput.value = '';
            handleItemSelection();
            window.filterHandCountedItems?.();
            addContractToTable(contractNumber);
            updateContractCounts(contractNumber);
            refreshCommonNames(contractNumber);
            window.loadCategorizedItems(); // Refresh dropdown after successful add
        }
    })
    .catch(error => {
        console.error('Error adding hand-counted item:', error);
        alert('Failed to add item. Please try again.');
        addContractToTable(contractNumber);
        updateContractCounts(contractNumber);
        refreshCommonNames(contractNumber);
    });
};

window.removeHandCountedItem = function removeHandCountedItem() {
    // Use remove-mode specific IDs  
    const contractDropdown = document.getElementById('remove-contract-number');
    const itemDropdown = document.getElementById('remove-item-name');
    const quantityInput = document.getElementById('remove-quantity');
    const employeeInput = document.getElementById('remove-employee');
    const contractNumber = contractDropdown.value;
    const itemValue = itemDropdown.value;
    const itemName = itemValue; // Remove mode doesn't have "other" option
    const quantity = parseInt(quantityInput.value);
    const employeeName = employeeInput.value;
    if (!contractNumber || !itemName || !quantity || quantity < 1 || !employeeName) {
        alert('Please fill in all fields: Contract Number, Item Name, Quantity (positive number), and Employee Name.');
        return;
    }
    fetch('/tab/4/remove_hand_counted_item', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            contract_number: contractNumber,
            item_name: itemName,
            quantity: quantity,
            action: 'Removed',
            employee_name: employeeName
        })
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            alert(data.message);
            if (newContractInput.style.display === 'block') window.toggleNewContractInput();
            contractDropdown.value = '';
            itemDropdown.value = '';
            quantityInput.value = '';
            employeeInput.value = '';
            handleItemSelection();
            window.filterHandCountedItems?.();
            addContractToTable(contractNumber);
            updateContractCounts(contractNumber);
            refreshCommonNames(contractNumber);
            window.loadCategorizedItems(); // Refresh dropdown after successful remove
        }
    })
    .catch(error => {
        console.error('Error removing hand-counted item:', error);
        alert('Failed to remove item. Please try again.');
        addContractToTable(contractNumber);
        updateContractCounts(contractNumber);
        refreshCommonNames(contractNumber);
    });
};

// Keep the hand-counted contract dropdown in sync with active items
window.syncContractOption = function(contractNumber, totalItems) {
    const contractDropdown = document.getElementById('hand-counted-contract-number');
    const option = Array.from(contractDropdown.options).find(opt => opt.value === contractNumber);
    if (totalItems > 0) {
        if (!option) {
            const newOption = document.createElement('option');
            newOption.value = contractNumber;
            newOption.textContent = contractNumber;
            contractDropdown.appendChild(newOption);
        }
    } else if (option) {
        option.remove();
    }
};

function addContractToTable(contractNumber) {
    const tbody = document.getElementById('category-rows');
    const existingRow = tbody.querySelector(`tr[data-contract-number="${contractNumber}"]`);
    if (!existingRow) {
        console.log(`Adding new contract row for ${contractNumber}`);
        const newRowHtml = `
            <tr data-contract-number="${contractNumber}">
                <td class="expandable-cell" onclick="window.expandCategory('${encodeURIComponent(contractNumber).replace(/'/g, "\\'").replace(/"/g, '\\"')}', 'common-${contractNumber}', '${contractNumber}')">
                    ${contractNumber}
                </td>
                <td>N/A</td>
                <td id="items-on-contract-${contractNumber}">0</td>
                <td>0</td>
                <td id="hand-counted-entries-${contractNumber}">0</td>
                <td class="date-last-scanned">N/A</td>
                <td>
                    <button class="btn btn-sm btn-secondary expand-btn" data-contract-number="${contractNumber}" data-target-id="common-${contractNumber}">Expand</button>
                    <button class="btn btn-sm btn-secondary collapse-btn" data-collapse-target="common-${contractNumber}" style="display:none;">Collapse</button>
                    <button class="btn btn-sm btn-info print-contract-btn" data-print-level="Contract" data-print-id="common-${contractNumber}" data-contract-number="${contractNumber}">Print</button>
                    <div id="loading-${contractNumber}" style="display:none;" class="loading-indicator">Loading...</div>
                </td>
            </tr>
            <tr>
                <td colspan="7">
                    <div id="common-${contractNumber}" class="expandable collapsed"></div>
                </td>
            </tr>
        `;
        tbody.insertAdjacentHTML('beforeend', newRowHtml);
    }
}

function updateContractCounts(contractNumber) {
    fetch(`/tab/4/contract_items_count?contract_number=${encodeURIComponent(contractNumber)}`)
        .then(response => {
            if (!response.ok) throw new Error('Failed to fetch Items on Contract');
            return response.json();
        })
        .then(data => {
            const totalItems = data.total_items || 0;
            const currentCountElement = document.getElementById(`items-on-contract-${contractNumber}`);
            if (currentCountElement) {
                currentCountElement.textContent = totalItems;
            }
            window.syncContractOption(contractNumber, totalItems);
            if (totalItems === 0) {
                const row = document.querySelector(`#category-rows tr[data-contract-number="${contractNumber}"]`);
                if (row) {
                    const nextRow = row.nextElementSibling;
                    if (nextRow && nextRow.querySelector(`#common-${contractNumber}`)) {
                        nextRow.remove();
                    }
                    row.remove();
                }
            }
        })
        .catch(error => console.error('Error updating Items on Contract count:', error));
    fetch(`/tab/4/hand_counted_entries?contract_number=${encodeURIComponent(contractNumber)}`)
        .then(response => {
            if (!response.ok) throw new Error('Failed to fetch Hand-Counted Entries');
            return response.json();
        })
        .then(data => {
            const handCountedElement = document.getElementById(`hand-counted-entries-${contractNumber}`);
            if (handCountedElement) {
                handCountedElement.textContent = data.hand_counted_entries || 0;
            }
        })
        .catch(error => console.error('Error updating Hand-Counted Entries count:', error));
}

function refreshCommonNames(contractNumber) {
    const commonDiv = document.getElementById(`common-${contractNumber}`);
    if (commonDiv && !commonDiv.classList.contains('collapsed')) {
        window.expandCategory(
            encodeURIComponent(contractNumber),
            `common-${contractNumber}`,
            contractNumber
        );
    }
}

// Load global filter from sessionStorage on page load and format timestamps
document.addEventListener('DOMContentLoaded', function() {
    // Set cached tab number if needed
    if (!getCachedTabNum()) {
        const pathMatch = window.location.pathname.match(/\/tab\/(\d+)/);
        setCachedTabNum(pathMatch ? parseInt(pathMatch[1], 10) : (window.location.pathname === '/' ? 1 : null));
        console.log('tab4.js: Set cachedTabNum:', getCachedTabNum());
    } else {
        console.log('tab4.js: cachedTabNum already set:', getCachedTabNum());
    }

    if (getCachedTabNum() !== 4) {
        console.log(`Tab ${getCachedTabNum()} detected, skipping tab4.js`);
        return;
    }

    // Format timestamps in the contract table
    const contractRows = document.querySelectorAll('#category-rows tr:not(.expandable)');
    contractRows.forEach(row => {
        const timestampCell = row.querySelector('td:nth-child(6)'); // Last Scanned Date column
        if (timestampCell) {
            const rawDate = timestampCell.textContent.trim();
            const formattedDate = formatDate(rawDate);
            timestampCell.textContent = formattedDate;
        }
    });

    // Load hand-counted contracts
    fetch('/tab/4/hand_counted_contracts')
        .then(response => response.json())
        .then(data => {
            const contractDropdown = document.getElementById('hand-counted-contract-number');
            data.contracts.forEach(contract => {
                const option = document.createElement('option');
                option.value = contract;
                option.textContent = contract;
                contractDropdown.appendChild(option);
            });
        })
        .catch(error => console.error('Error fetching hand-counted contracts:', error));

    // Load categorized items for improved dropdown UX
    window.loadCategorizedItems();

    // Attach event listeners
    document.removeEventListener('click', handleClick);
    console.log('Attaching click event listener');
    document.addEventListener('click', handleClick);

    function handleClick(event) {
        const expandBtn = event.target.closest('.expand-btn');
        if (expandBtn) {
            event.stopPropagation();
            console.log('Expand button clicked:', {
                category: expandBtn.getAttribute('data-category'),
                commonName: expandBtn.getAttribute('data-common-name'),
                targetId: expandBtn.getAttribute('data-target-id'),
                contractNumber: expandBtn.getAttribute('data-contract-number')
            });

            const category = expandBtn.getAttribute('data-category');
            const commonName = expandBtn.getAttribute('data-common-name');
            const targetId = expandBtn.getAttribute('data-target-id');
            const contractNumber = expandBtn.getAttribute('data-contract-number');

            if (commonName) {
                console.log(`Expanding items for ${contractNumber}, ${commonName}`);
                window.expandItems(contractNumber, commonName, targetId, 1, 4);
            } else if (contractNumber && getCachedTabNum() === 4) {
                console.log(`Expanding category for ${contractNumber}`);
                window.expandCategory(category, targetId, contractNumber, 1, 4);
            }
            return;
        }

        const collapseBtn = event.target.closest('.collapse-btn');
        if (collapseBtn) {
            event.stopPropagation();
            console.log(`Collapsing ${collapseBtn.getAttribute('data-collapse-target')}`);
            collapseSection(collapseBtn.getAttribute('data-collapse-target'));
            const parentRow = document.querySelector(`[data-target-id="${collapseBtn.getAttribute('data-collapse-target')}"]`)?.closest('tr');
            if (parentRow) {
                const expandBtn = parentRow.querySelector('.expand-btn');
                const collapseBtn = parentRow.querySelector('.collapse-btn');
                if (expandBtn && collapseBtn) {
                    expandBtn.style.display = 'inline-block';
                    collapseBtn.style.display = 'none';
                }
            }
            return;
        }

        // Handle main Print Items button
        const printItemsBtn = event.target.closest('.print-items-btn');
        if (printItemsBtn) {
            event.preventDefault();
            event.stopPropagation();
            const contractNumber = printItemsBtn.getAttribute('data-contract-number');
            console.log(`Opening contract items print for: ${contractNumber}`);
            const url = `/tab/4/contract_items_print?contract_number=${encodeURIComponent(contractNumber)}`;
            window.open(url, '_blank', 'width=1200,height=800,scrollbars=yes,resizable=yes');
            return;
        }

        // Handle dropdown Print Items button (from dropdown menu only)
        const dropdownPrintBtn = event.target.closest('.dropdown-item.print-btn');
        if (dropdownPrintBtn) {
            event.preventDefault();
            event.stopPropagation();
            const contractNumber = dropdownPrintBtn.getAttribute('data-contract-number');
            console.log(`Opening contract items print from dropdown for: ${contractNumber}`);
            const url = `/tab/4/contract_items_print?contract_number=${encodeURIComponent(contractNumber)}`;
            window.open(url, '_blank', 'width=1200,height=800,scrollbars=yes,resizable=yes');
            return;
        }
        
        // Handle expanded common name print button
        const printCommonNameBtn = event.target.closest('.print-common-name-btn');
        if (printCommonNameBtn) {
            event.preventDefault();
            event.stopPropagation();
            const level = printCommonNameBtn.getAttribute('data-print-level');
            const id = printCommonNameBtn.getAttribute('data-print-id');
            const commonName = printCommonNameBtn.getAttribute('data-common-name');
            const category = printCommonNameBtn.getAttribute('data-category');
            console.log(`Using printTable for common name: ${commonName}`);
            printTable(level, id, commonName, category);
            return;
        }
        
        // Handle expanded contract print button  
        const printContractBtn = event.target.closest('.print-contract-btn');
        if (printContractBtn) {
            event.preventDefault();
            event.stopPropagation();
            const level = printContractBtn.getAttribute('data-print-level');
            const id = printContractBtn.getAttribute('data-print-id');
            const contractNumber = printContractBtn.getAttribute('data-contract-number');
            console.log(`Using printTable for contract: ${contractNumber}`);
            printTable(level, id, null, contractNumber);
            return;
        }

        const printFullBtn = event.target.closest('.print-full-btn');
        if (printFullBtn) {
            event.preventDefault();
            event.stopPropagation();
            const commonName = printFullBtn.getAttribute('data-common-name');
            const category = printFullBtn.getAttribute('data-category');
            const subcategory = printFullBtn.getAttribute('data-subcategory');
            printFullItemList(category, subcategory, commonName);
            return;
        }

        // Handle new comprehensive print options
        const printContractHistory = event.target.closest('.print-contract-history');
        if (printContractHistory) {
            event.preventDefault();
            event.stopPropagation();
            const contractNumber = printContractHistory.getAttribute('data-contract-number');
            console.log(`Opening contract history for: ${contractNumber}`);
            const url = `/tab/4/contract_history_print?contract_number=${encodeURIComponent(contractNumber)}`;
            window.open(url, '_blank', 'width=1200,height=800,scrollbars=yes,resizable=yes');
            return;
        }

        const printHandCountedHistory = event.target.closest('.print-hand-counted-history');
        if (printHandCountedHistory) {
            event.preventDefault();
            event.stopPropagation();
            const contractNumber = printHandCountedHistory.getAttribute('data-contract-number');
            console.log(`Opening hand counted history for: ${contractNumber}`);
            const url = `/tab/4/hand_counted_history_print?contract_number=${encodeURIComponent(contractNumber)}`;
            window.open(url, '_blank', 'width=1200,height=800,scrollbars=yes,resizable=yes');
            return;
        }

        // Handle print buttons for selected contract
        const printSelectedContractHistory = event.target.closest('.print-selected-contract-history');
        if (printSelectedContractHistory) {
            event.preventDefault();
            event.stopPropagation();
            const contractSelector = document.getElementById('print-contract-selector');
            const contractNumber = contractSelector.value;
            if (contractNumber) {
                console.log(`Opening contract history for selected: ${contractNumber}`);
                const url = `/tab/4/contract_history_print?contract_number=${encodeURIComponent(contractNumber)}`;
                window.open(url, '_blank', 'width=1200,height=800,scrollbars=yes,resizable=yes');
            }
            return;
        }

        const printSelectedHandCountedHistory = event.target.closest('.print-selected-hand-counted-history');
        if (printSelectedHandCountedHistory) {
            event.preventDefault();
            event.stopPropagation();
            const contractSelector = document.getElementById('print-contract-selector');
            const contractNumber = contractSelector.value;
            if (contractNumber) {
                console.log(`Opening hand counted history for selected: ${contractNumber}`);
                const url = `/tab/4/hand_counted_history_print?contract_number=${encodeURIComponent(contractNumber)}`;
                window.open(url, '_blank', 'width=1200,height=800,scrollbars=yes,resizable=yes');
            }
            return;
        }
        
        // Handle create snapshot button
        const createSnapshotBtn = event.target.closest('.create-contract-snapshot');
        if (createSnapshotBtn) {
            event.preventDefault();
            event.stopPropagation();
            const contractSelector = document.getElementById('print-contract-selector');
            const contractNumber = contractSelector.value;
            if (contractNumber) {
                createContractSnapshot(contractNumber);
            }
            return;
        }
    }

    // HTMX event listener for hand-counted items
    document.body.addEventListener('htmx:afterSwap', function(event) {
        const target = event.target;
        if (target.id === 'hand-counted-items') {
            const rows = target.querySelectorAll('tr');
            rows.forEach(row => {
                const timestampCell = row.querySelector('td:nth-child(5)');
                if (timestampCell) {
                    const rawDate = timestampCell.textContent.trim();
                    timestampCell.textContent = formatDate(rawDate);
                }
            });
        }
    });
    
    // Handle contract selector for print functionality
    const printContractSelector = document.getElementById('print-contract-selector');
    if (printContractSelector) {
        printContractSelector.addEventListener('change', function() {
            const contractHistoryBtn = document.querySelector('.print-selected-contract-history');
            const handCountedHistoryBtn = document.querySelector('.print-selected-hand-counted-history');
            
            const snapshotBtn = document.querySelector('.create-contract-snapshot');
            
            if (this.value) {
                contractHistoryBtn.disabled = false;
                handCountedHistoryBtn.disabled = false;
                snapshotBtn.disabled = false;
            } else {
                contractHistoryBtn.disabled = true;
                handCountedHistoryBtn.disabled = true;
                snapshotBtn.disabled = true;
            }
        });
    }
    
    // Function to create contract snapshot
    window.createContractSnapshot = async function(contractNumber) {
        try {
            const response = await fetch('/tab/4/create_contract_snapshot', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    contract_number: contractNumber,
                    snapshot_type: 'manual',
                    created_by: 'user'
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert(`✅ Snapshot created successfully!\nContract: ${contractNumber}\nItems: ${data.items_count}`);
            } else {
                alert(`❌ Error creating snapshot: ${data.error}`);
            }
        } catch (error) {
            console.error('Error creating snapshot:', error);
            alert(`❌ Error creating snapshot: ${error.message}`);
        }
    };
    
    // Function to show snapshot automation status
    window.showSnapshotStatus = async function() {
        try {
            const response = await fetch('/tab/4/snapshot_status');
            const data = await response.json();
            
            if (data.error) {
                alert(`❌ Error getting status: ${data.error}`);
                return;
            }
            
            const schedule = data.schedule_info;
            const lastRun = data.last_run;
            
            let statusMessage = `📊 SNAPSHOT AUTOMATION STATUS\n\n`;
            statusMessage += `🗓️  Schedule: ${schedule.schedule}\n`;
            statusMessage += `📈 Recent snapshots (7 days): ${schedule.recent_periodic_count}\n`;
            statusMessage += `🕐 Last periodic snapshot: ${schedule.last_periodic_snapshot || 'Never'}\n\n`;
            
            if (lastRun) {
                statusMessage += `📋 LAST RUN SUMMARY:\n`;
                statusMessage += `⏰ Timestamp: ${new Date(lastRun.timestamp).toLocaleString()}\n`;
                
                if (lastRun.results) {
                    const results = lastRun.results;
                    statusMessage += `✅ Successful: ${results.successful_snapshots}/${results.total_contracts}\n`;
                    statusMessage += `📦 Items snapshotted: ${results.total_items_snapshotted}\n`;
                    
                    if (results.failed_snapshots > 0) {
                        statusMessage += `❌ Failed: ${results.failed_snapshots}\n`;
                    }
                } else if (lastRun.error) {
                    statusMessage += `❌ Error: ${lastRun.error}\n`;
                }
            } else {
                statusMessage += `📋 No automation runs recorded yet\n`;
            }
            
            statusMessage += `\n📁 Log files available on server:\n`;
            statusMessage += `   • snapshot_automation.log (detailed)\n`;
            statusMessage += `   • snapshot_cron.log (cron output)\n`;
            statusMessage += `   • last_snapshot_run.json (status)\n`;
            
            alert(statusMessage);
            
        } catch (error) {
            console.error('Error getting snapshot status:', error);
            alert(`❌ Error getting status: ${error.message}`);
        }
    };

    // ===== LAUNDRY CONTRACT STATUS MANAGEMENT =====
    
    // Track which statuses are currently visible
    let visibleStatuses = new Set(['active', 'finalized']); // Default: show both active statuses
    
    // Toggle status filter - expose globally for onclick handlers
    function toggleStatusFilter(status, isChecked) {
        console.log(`Toggling ${status}: ${isChecked}`);
        
        if (isChecked) {
            visibleStatuses.add(status);
        } else {
            visibleStatuses.delete(status);
        }
        
        updateContractVisibility();
    }
    
    // Update contract visibility based on selected statuses
    function updateContractVisibility() {
        const rows = document.querySelectorAll('.contract-row');
        let visibleCount = 0;
        
        rows.forEach(row => {
            const contractStatus = row.dataset.contractStatus || 'active';
            const shouldShow = visibleStatuses.has(contractStatus);
            
            if (shouldShow) {
                row.style.display = '';
                row.nextElementSibling.style.display = ''; // Show the expandable row too
                visibleCount++;
            } else {
                row.style.display = 'none';
                row.nextElementSibling.style.display = 'none'; // Hide the expandable row too
            }
        });
        
        // Update contract count
        const countElement = document.getElementById('contract-count');
        if (countElement) {
            countElement.textContent = visibleCount;
        }
        
        console.log(`Showing ${visibleCount} contracts with statuses:`, Array.from(visibleStatuses));
    }
    
    // Show all contracts
    function showAllContracts() {
        console.log('Showing all contracts');
        
        // Check all checkboxes
        document.getElementById('filter-active').checked = true;
        document.getElementById('filter-finalized').checked = true;
        document.getElementById('filter-returned').checked = true;
        
        // Update visible statuses
        visibleStatuses = new Set(['active', 'finalized', 'returned']);
        updateContractVisibility();
    }
    
    // Show only active contracts (PreWash + Sent to Laundry)
    function showActiveOnly() {
        console.log('Showing active contracts only');
        
        // Set checkboxes to active only state
        document.getElementById('filter-active').checked = true;
        document.getElementById('filter-finalized').checked = true;
        document.getElementById('filter-returned').checked = false;
        
        // Update visible statuses
        visibleStatuses = new Set(['active', 'finalized']);
        updateContractVisibility();
    }
    
    // Legacy function for compatibility
    function filterContractsByStatus(status) {
        if (status === 'all') {
            showAllContracts();
        } else {
            // Single status mode (legacy)
            visibleStatuses = new Set([status]);
            updateContractVisibility();
        }
    }
    
    // Finalize contract - expose globally for onclick handlers  
    async function finalizeContract(contractNumber) {
        const user = prompt('Enter your name to send this contract to laundry:');
        if (!user || user.trim() === '') return;
        
        const notes = prompt('Optional notes about sending to laundry (e.g., "Picked up by ABC Cleaners"):') || '';
        
        try {
            const response = await fetch('/tab/4/finalize_contract', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    contract_number: contractNumber, 
                    user: user.trim(),
                    notes: notes.trim()
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert(`✅ Contract ${contractNumber} has been sent to laundry`);
                location.reload(); // Refresh to show updated status
            } else {
                alert(`❌ Error: ${data.error}`);
            }
        } catch (error) {
            console.error('Error sending contract to laundry:', error);
            alert(`❌ Error sending contract to laundry: ${error.message}`);
        }
    }
    
    // Mark contract as returned - expose globally for onclick handlers
    async function markReturned(contractNumber) {
        const user = prompt('Enter your name to mark this contract as returned:');
        if (!user || user.trim() === '') return;
        
        const notes = prompt('Optional notes about return (e.g., "Missing 2 napkin packs"):') || '';
        
        try {
            const response = await fetch('/tab/4/mark_returned', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    contract_number: contractNumber, 
                    user: user.trim(),
                    notes: notes.trim()
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert(`✅ ${data.message}`);
                location.reload(); // Refresh to show updated status
            } else {
                alert(`❌ Error: ${data.error}`);
            }
        } catch (error) {
            console.error('Error marking contract as returned:', error);
            alert(`❌ Error marking contract as returned: ${error.message}`);
        }
    }
    
    // Reactivate contract - expose globally for onclick handlers
    async function reactivateContract(contractNumber) {
        if (!confirm(`Are you sure you want to reactivate contract ${contractNumber}? This will reset its status to active.`)) {
            return;
        }
        
        const user = prompt('Enter your name to reactivate this contract:');
        if (!user || user.trim() === '') return;
        
        const notes = prompt('Optional notes about reactivation:') || '';
        
        try {
            const response = await fetch('/tab/4/reactivate_contract', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    contract_number: contractNumber, 
                    user: user.trim(),
                    notes: notes.trim()
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert(`✅ ${data.message}`);
                location.reload(); // Refresh to show updated status
            } else {
                alert(`❌ Error: ${data.error}`);
            }
        } catch (error) {
            console.error('Error reactivating contract:', error);
            alert(`❌ Error reactivating contract: ${error.message}`);
        }
    }

    // Initialize event listeners when page loads
    function initializeStatusManagement() {
        console.log('Initializing status management...');
        
        // Status filter checkboxes
        const filterCheckboxes = document.querySelectorAll('#status-filter input[type="checkbox"]');
        console.log('Found filter checkboxes:', filterCheckboxes.length);
        
        filterCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                console.log('Filter checkbox changed:', this.value, this.checked);
                toggleStatusFilter(this.value, this.checked);
            });
        });
        
        // Status action buttons
        const finalizeButtons = document.querySelectorAll('.finalize-btn');
        console.log('Found finalize buttons:', finalizeButtons.length);
        
        finalizeButtons.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                console.log('Finalize button clicked for:', this.dataset.contractNumber);
                finalizeContract(this.dataset.contractNumber);
            });
        });
        
        const returnButtons = document.querySelectorAll('.return-btn');
        console.log('Found return buttons:', returnButtons.length);
        
        returnButtons.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                console.log('Return button clicked for:', this.dataset.contractNumber);
                markReturned(this.dataset.contractNumber);
            });
        });
        
        const reactivateButtons = document.querySelectorAll('.reactivate-btn');
        console.log('Found reactivate buttons:', reactivateButtons.length);
        
        reactivateButtons.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                console.log('Reactivate button clicked for:', this.dataset.contractNumber);
                reactivateContract(this.dataset.contractNumber);
            });
        });
        
        // Initialize with default view (PreWash + Sent to Laundry)
        setTimeout(() => {
            console.log('Setting initial filter to show active contracts (PreWash + Sent to Laundry)');
            showActiveOnly(); // This sets the checkboxes and visibility correctly
        }, 100);
        
        console.log('Laundry contract status management initialized');
    }

    // Expose functions globally for onclick handlers
    window.toggleStatusFilter = toggleStatusFilter;
    window.showAllContracts = showAllContracts;
    window.showActiveOnly = showActiveOnly;
    window.filterContractsByStatus = filterContractsByStatus; // Legacy compatibility
    window.finalizeContract = finalizeContract;
    window.markReturned = markReturned;
    window.reactivateContract = reactivateContract;

    // Run initialization when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeStatusManagement);
    } else {
        initializeStatusManagement();
    }
    
    // Also run when tab becomes active (for tab switching)
    document.addEventListener('tabActivated', function(e) {
        if (e.detail && e.detail.tabNum === 4) {
            console.log('Tab 4 activated, reinitializing status management');
            setTimeout(initializeStatusManagement, 100);
        }
    });
});

// Dual-mode hand counted interface functions
let currentMode = 'add';

function switchToAddMode() {
    console.log('Switching to add mode');
    currentMode = 'add';
    populateContractDropdowns();
    populateCategoryDropdowns();
}

function switchToRemoveMode() {
    console.log('Switching to remove mode');
    currentMode = 'remove';
    populateContractDropdowns();
    // Hide progressive fields initially
    document.getElementById('remove-item-group').style.display = 'none';
    document.getElementById('remove-quantity-group').style.display = 'none';
    document.getElementById('remove-employee-group').style.display = 'none';
    document.getElementById('remove-button-group').style.display = 'none';
}

function populateContractDropdowns() {
    const contractSelect = document.getElementById(currentMode === 'add' ? 'add-contract-number' : 'remove-contract-number');
    if (!contractSelect) return;
    
    // Clear existing options
    contractSelect.innerHTML = '<option value="">Select Contract...</option>';
    
    // Get contracts from the main table
    const contractRows = document.querySelectorAll('tr[data-contract-status]');
    const contracts = new Set();
    
    contractRows.forEach(row => {
        const contractCell = row.cells[0];
        if (contractCell) {
            const contractText = contractCell.textContent.trim();
            const contractMatch = contractText.match(/^(L\d+)/);
            if (contractMatch) {
                contracts.add(contractMatch[1]);
            }
        }
    });
    
    // Add contracts to dropdown
    Array.from(contracts).sort().forEach(contract => {
        const option = document.createElement('option');
        option.value = contract;
        option.textContent = contract;
        contractSelect.appendChild(option);
    });
    
    console.log(`Populated ${currentMode} contract dropdown with ${contracts.size} contracts`);
}

function loadRemovableItems() {
    const contractNumber = document.getElementById('remove-contract-number').value;
    if (!contractNumber) {
        document.getElementById('remove-item-group').style.display = 'none';
        document.getElementById('remove-quantity-group').style.display = 'none';
        document.getElementById('remove-employee-group').style.display = 'none';
        document.getElementById('remove-button-group').style.display = 'none';
        return;
    }
    
    console.log('Loading removable items for contract:', contractNumber);
    
    // Fetch hand counted items for this contract
    fetch(`/tab/4/hand_counted_items_for_contract/${contractNumber}`)
        .then(response => response.json())
        .then(data => {
            const itemSelect = document.getElementById('remove-item-name');
            itemSelect.innerHTML = '<option value="">Select Item...</option>';
            
            if (data.items && data.items.length > 0) {
                // Group items by name and calculate net quantities
                const itemTotals = {};
                data.items.forEach(item => {
                    const itemName = item.item_name;
                    if (!itemTotals[itemName]) {
                        itemTotals[itemName] = { added: 0, removed: 0 };
                    }
                    if (item.action === 'Added') {
                        itemTotals[itemName].added += item.quantity;
                    } else if (item.action === 'Removed') {
                        itemTotals[itemName].removed += item.quantity;
                    }
                });
                
                // Add items with positive net quantities to dropdown
                Object.entries(itemTotals).forEach(([itemName, totals]) => {
                    const netQuantity = totals.added - totals.removed;
                    if (netQuantity > 0) {
                        const option = document.createElement('option');
                        option.value = itemName;
                        option.textContent = `${itemName} (Available: ${netQuantity})`;
                        option.dataset.maxQuantity = netQuantity;
                        itemSelect.appendChild(option);
                    }
                });
                
                document.getElementById('remove-item-group').style.display = 'block';
            } else {
                document.getElementById('remove-item-group').style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error loading removable items:', error);
        });
}

function updateMaxRemovalQuantity() {
    const itemSelect = document.getElementById('remove-item-name');
    const selectedOption = itemSelect.options[itemSelect.selectedIndex];
    
    if (selectedOption && selectedOption.value) {
        const maxQuantity = selectedOption.dataset.maxQuantity;
        document.getElementById('max-removal-quantity').textContent = maxQuantity;
        document.getElementById('remove-quantity').max = maxQuantity;
        document.getElementById('remove-quantity').value = '';
        
        document.getElementById('remove-quantity-group').style.display = 'block';
        document.getElementById('remove-employee-group').style.display = 'block';
        document.getElementById('remove-button-group').style.display = 'block';
    } else {
        document.getElementById('remove-quantity-group').style.display = 'none';
        document.getElementById('remove-employee-group').style.display = 'none';
        document.getElementById('remove-button-group').style.display = 'none';
    }
}

// Updated function calls to support mode parameter
function updateItemDropdownHierarchical(mode = null) {
    if (!mode) mode = currentMode;
    
    const categorySelect = document.getElementById(`${mode}-category`);
    const subcategorySelect = document.getElementById(`${mode}-subcategory`);
    const itemSelect = document.getElementById(`${mode}-item-name`);
    
    if (!categorySelect || !subcategorySelect) return;
    
    const category = categorySelect.value;
    const subcategory = subcategorySelect.value;
    
    // Clear item dropdown
    itemSelect.innerHTML = '<option value="">Select Item...</option>';
    
    if (category && subcategory) {
        console.log(`Fetching items for category: ${category}, subcategory: ${subcategory}`);
        
        fetch(`/tab/4/items_for_category_subcategory/${encodeURIComponent(category)}/${encodeURIComponent(subcategory)}`)
            .then(response => response.json())
            .then(data => {
                if (data.items && data.items.length > 0) {
                    data.items.forEach(item => {
                        const option = document.createElement('option');
                        option.value = item.item_name;
                        option.textContent = item.display_name || item.item_name;
                        itemSelect.appendChild(option);
                    });
                    console.log(`Loaded ${data.items.length} items for ${category}/${subcategory}`);
                }
            })
            .catch(error => {
                console.error('Error fetching items:', error);
            });
    }
}

function updateSubcategoryDropdown(mode = null) {
    if (!mode) mode = currentMode;
    
    const categorySelect = document.getElementById(`${mode}-category`);
    const subcategorySelect = document.getElementById(`${mode}-subcategory`);
    const itemSelect = document.getElementById(`${mode}-item-name`);
    
    if (!categorySelect || !subcategorySelect) return;
    
    // Clear subcategory and item dropdowns
    subcategorySelect.innerHTML = '<option value="">Select Subcategory...</option>';
    itemSelect.innerHTML = '<option value="">Select Item...</option>';
    
    const category = categorySelect.value;
    if (category) {
        console.log(`Fetching subcategories for category: ${category}`);
        
        fetch(`/tab/4/subcategories_for_category/${encodeURIComponent(category)}`)
            .then(response => response.json())
            .then(data => {
                if (data.subcategories && data.subcategories.length > 0) {
                    data.subcategories.forEach(subcategory => {
                        const option = document.createElement('option');
                        option.value = subcategory;
                        option.textContent = subcategory;
                        subcategorySelect.appendChild(option);
                    });
                    console.log(`Loaded ${data.subcategories.length} subcategories for ${category}`);
                }
            })
            .catch(error => {
                console.error('Error fetching subcategories:', error);
            });
    }
}

function handleItemSelection(mode = null) {
    if (!mode) mode = currentMode;
    
    const itemSelect = document.getElementById(`${mode}-item-name`);
    const newItemInput = document.getElementById(`${mode}-new-item-name`);
    
    if (itemSelect.value === 'new') {
        newItemInput.style.display = 'block';
        newItemInput.focus();
    } else {
        newItemInput.style.display = 'none';
    }
}

function toggleNewContractInput(mode = null) {
    if (!mode) mode = currentMode;
    
    const contractSelect = document.getElementById(`${mode}-contract-number`);
    const newContractInput = document.getElementById(`${mode}-new-contract-number`);
    
    if (newContractInput.style.display === 'none') {
        newContractInput.style.display = 'block';
        contractSelect.style.display = 'none';
        newContractInput.focus();
    } else {
        newContractInput.style.display = 'none';
        contractSelect.style.display = 'block';
    }
}

// Expose new functions globally
window.switchToAddMode = switchToAddMode;
window.switchToRemoveMode = switchToRemoveMode;
window.loadRemovableItems = loadRemovableItems;
window.updateMaxRemovalQuantity = updateMaxRemovalQuantity;
window.populateContractDropdowns = populateContractDropdowns;