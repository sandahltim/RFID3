console.log('tab1_5.js version: 2025-04-27-v5 loaded');

// Load common names for a given subcategory
function loadCommonNames(select) {
    const category = select.getAttribute('data-category');
    const subcategory = select.value;
    if (!subcategory) return;

    const catId = select.closest('tr').nextElementSibling.querySelector('.common-level').id.split('-')[1];
    const commonLevelDiv = document.getElementById(`common-${catId}`);
    const loadingDiv = document.getElementById(`loading-subcat-${catId}`);

    if (commonLevelDiv.classList.contains('expanded')) {
        commonLevelDiv.classList.remove('expanded');
        commonLevelDiv.classList.add('collapsed');
        commonLevelDiv.innerHTML = '';
        select.closest('tr').querySelector('.expand-btn').style.display = 'inline-block';
        select.closest('tr').querySelector('.collapse-btn').style.display = 'none';
        return;
    }

    if (loadingDiv) loadingDiv.style.display = 'block';

    const url = `/tab/${window.cachedTabNum}/common_names?category=${encodeURIComponent(category)}&subcategory=${encodeURIComponent(subcategory)}`;
    fetch(url)
        .then(response => response.json())
        .then(data => {
            let html = `
                <table class="table table-bordered common-table">
                    <thead>
                        <tr>
                            <th>Common Name <span class="sort-arrow"></span></th>
                            <th>Total Items <span class="sort-arrow"></span></th>
                            <th>Items on Contracts <span class="sort-arrow"></span></th>
                            <th>Items in Service <span class="sort-arrow"></span></th>
                            <th>Items Available <span class="sort-arrow"></span></th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            data.common_names.forEach((common, index) => {
                html += `
                    <tr>
                        <td class="expandable-cell" onclick="expandCommonNames('${encodeURIComponent(category)}', '${encodeURIComponent(subcategory)}', '${encodeURIComponent(common.name)}', 'item-${catId}-${index}')">
                            ${common.name}
                        </td>
                        <td>${common.total_items}</td>
                        <td>${common.items_on_contracts}</td>
                        <td>${common.items_in_service}</td>
                        <td>${common.items_available}</td>
                        <td>
                            <button class="btn btn-sm btn-secondary expand-btn" onclick="expandCommonNames('${encodeURIComponent(category)}', '${encodeURIComponent(subcategory)}', '${encodeURIComponent(common.name)}', 'item-${catId}-${index}')">Expand Items</button>
                            <button class="btn btn-sm btn-secondary collapse-btn" style="display:none;" onclick="collapseSection('item-${catId}-${index}')">Collapse</button>
                            <button class="btn btn-sm btn-info print-btn" data-print-level="Common" data-print-id="item-${catId}-${index}" data-common-name="${encodeURIComponent(common.name)}">Print Aggregate</button>
                            <button class="btn btn-sm btn-info print-btn" data-print-level="Full" data-print-id="item-${catId}-${index}" data-common-name="${encodeURIComponent(common.name)}">Print Full List</button>
                            <div id="loading-item-${catId}-${index}" style="display:none;" class="loading">Loading...</div>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="6">
                            <div id="item-${catId}-${index}" class="expandable collapsed"></div>
                        </td>
                    </tr>
                `;
            });

            html += `
                    </tbody>
                </table>
                <div class="row-count mt-2">Showing ${data.common_names.length} of ${data.total_common_names} rows</div>
            `;

            commonLevelDiv.innerHTML = html;
            commonLevelDiv.classList.remove('collapsed');
            commonLevelDiv.classList.add('expanded');
            select.closest('tr').querySelector('.expand-btn').style.display = 'none';
            select.closest('tr').querySelector('.collapse-btn').style.display = 'inline-block';

            // Apply global filter to the newly loaded common names table
            applyFilterToAllLevels();
        })
        .catch(error => {
            console.error('Error loading common names:', error);
            commonLevelDiv.innerHTML = '<p>Error loading common names.</p>';
        })
        .finally(() => {
            if (loadingDiv) loadingDiv.style.display = 'none';
        });
}

// Expand common names to show individual items
function expandCommonNames(category, subcategory, commonName, targetId) {
    const targetDiv = document.getElementById(targetId);
    const loadingDiv = document.getElementById(`loading-${targetId}`);

    if (targetDiv.classList.contains('expanded')) {
        targetDiv.classList.remove('expanded');
        targetDiv.classList.add('collapsed');
        targetDiv.innerHTML = '';
        const parentRow = targetDiv.closest('tr').previousElementSibling;
        parentRow.querySelector('.expand-btn').style.display = 'inline-block';
        parentRow.querySelector('.collapse-btn').style.display = 'none';
        return;
    }

    if (loadingDiv) loadingDiv.style.display = 'block';

    const url = `/tab/${window.cachedTabNum}/data?category=${category}&subcategory=${subcategory}&common_name=${commonName}`;
    fetch(url)
        .then(response => response.json())
        .then(data => {
            let html = `
                <table class="table table-bordered item-table">
                    <thead>
                        <tr>
                            <th>Tag ID <span class="sort-arrow"></span></th>
                            <th>Common Name <span class="sort-arrow"></span></th>
                            <th>Bin Location <span class="sort-arrow"></span></th>
                            <th>Status <span class="sort-arrow"></span></th>
                            <th>Last Contract <span class="sort-arrow"></span></th>
                            <th>Last Scanned Date <span class="sort-arrow"></span></th>
                            <th>Quality</th>
                            <th>Notes</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            data.items.forEach(item => {
                const formattedDate = formatDate(item.last_scanned_date); // Use the new formatDate function
                html += `
                    <tr>
                        <td>${item.tag_id}</td>
                        <td>${item.common_name}</td>
                        <td>${item.bin_location}</td>
                        <td>${item.status}</td>
                        <td>${item.last_contract_num}</td>
                        <td>${formattedDate}</td>
                        <td>${item.quality || 'N/A'}</td>
                        <td>${item.notes || 'N/A'}</td>
                    </tr>
                `;
            });

            html += `
                    </tbody>
                </table>
                <div class="row-count mt-2">Showing ${data.items.length} of ${data.total_items} rows</div>
            `;

            targetDiv.innerHTML = html;
            targetDiv.classList.remove('collapsed');
            targetDiv.classList.add('expanded');
            const parentRow = targetDiv.closest('tr').previousElementSibling;
            parentRow.querySelector('.expand-btn').style.display = 'none';
            parentRow.querySelector('.collapse-btn').style.display = 'inline-block';

            // Apply global filter to the newly loaded item table
            applyFilterToAllLevels();
        })
        .catch(error => {
            console.error('Error loading items:', error);
            targetDiv.innerHTML = '<p>Error loading items.</p>';
        })
        .finally(() => {
            if (loadingDiv) loadingDiv.style.display = 'none';
        });
}

// Collapse a section
function collapseSection(targetId) {
    const targetDiv = document.getElementById(targetId);
    if (targetDiv) {
        targetDiv.classList.remove('expanded');
        targetDiv.classList.add('collapsed');
        targetDiv.innerHTML = '';
        const parentRow = targetDiv.closest('tr').previousElementSibling;
        parentRow.querySelector('.expand-btn').style.display = 'inline-block';
        parentRow.querySelector('.collapse-btn').style.display = 'none';
    }
}