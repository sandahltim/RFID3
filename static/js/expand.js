console.log('expand.js version: 2025-04-25 v40 loaded');

function showLoading(key) {
    const loadingDiv = document.getElementById(`loading-${key}`);
    if (loadingDiv) {
        console.log('Loading indicator found, displaying:', loadingDiv);
        loadingDiv.style.display = 'block';
    } else {
        console.warn(`Loading indicator with ID loading-${key} not found`);
    }
}

function hideLoading(key) {
    const loadingDiv = document.getElementById(`loading-${key}`);
    if (loadingDiv) {
        console.log('Loading indicator found, hiding:', loadingDiv);
        loadingDiv.style.display = 'none';
    } else {
        console.warn(`Loading indicator with ID loading-${key} not found`);
    }
}

function hideOtherSubcats(currentCategory) {
    const subcatDivs = document.querySelectorAll('[id^="subcat-"]');
    console.log('Found subcat divs:', subcatDivs.length);
    subcatDivs.forEach(div => {
        const divId = div.id;
        console.log('Subcat div ID:', divId);
        if (divId !== `subcat-${currentCategory}`) {
            console.log('Collapsing subcat div:', divId);
            div.classList.remove('expanded');
            div.classList.add('collapsed');
            div.classList.remove('fade');
            div.style.display = 'none';
            div.style.opacity = '0';
        } else {
            console.log(`Keeping subcat div visible: ${divId}`);
        }
    });
}

function hideOtherCommonNames(currentTargetId) {
    const commonDivs = document.querySelectorAll('[id^="common-"]');
    console.log('Found common divs:', commonDivs.length);
    commonDivs.forEach(div => {
        const divId = div.id;
        console.log('Common div ID:', divId);
        if (divId !== currentTargetId) {
            console.log('Collapsing common div:', divId);
            div.classList.remove('expanded');
            div.classList.add('collapsed');
            div.classList.remove('fade');
            div.style.display = 'none';
        }
    });
}

function hideOtherItems(currentTargetId) {
    const itemDivs = document.querySelectorAll('[id^="items-"]');
    console.log('Found item divs:', itemDivs.length);
    itemDivs.forEach(div => {
        const divId = div.id;
        console.log('Item div ID:', divId);
        if (divId !== currentTargetId) {
            console.log('Collapsing item div:', divId);
            div.classList.remove('expanded');
            div.classList.add('collapsed');
            div.classList.remove('fade');
            div.style.display = 'none';
        }
    });
}

function collapseSection(targetId) {
    const section = document.getElementById(targetId);
    if (section) {
        section.classList.remove('expanded');
        section.classList.add('collapsed');
        section.classList.remove('fade');
        section.style.display = 'none';
        section.style.opacity = '0';

        const expandBtn = document.querySelector(`button[onclick*="${targetId}"]`);
        const collapseBtn = expandBtn ? expandBtn.nextElementSibling : null;
        if (expandBtn && collapseBtn) {
            expandBtn.style.display = 'inline-block';
            collapseBtn.style.display = 'none';
        }
    }
}

function loadCommonNames(category, subcategory, targetId, page = 1, contractNumber = null) {
    console.log('loadCommonNames called with', { category, subcategory, targetId, page, contractNumber });

    const containerId = (window.cachedTabNum == 2 || window.cachedTabNum == 4) ? targetId : `common-${targetId}`;
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container with ID ${containerId} not found`);
        return;
    }
    console.log('Common names container found:', container);
    console.log('Common names container classes before update:', container.className);

    const key = subcategory ? `${category}_${subcategory}` : category;
    showLoading(key);
    hideOtherCommonNames(containerId);

    let url = `/tab/${window.cachedTabNum}/common_names?page=${page}`;
    if (window.cachedTabNum == 2 || window.cachedTabNum == 4) {
        url += `&contract_number=${encodeURIComponent(contractNumber)}`;
    } else {
        url += `&category=${encodeURIComponent(category)}`;
    }
    if (subcategory) {
        url += `&subcategory=${encodeURIComponent(subcategory)}`;
    }

    const commonFilter = document.getElementById(`common-filter-${key}`)?.value || '';
    const commonSort = document.getElementById(`common-sort-${key}`)?.value || '';
    if (commonFilter) {
        url += `&filter=${encodeURIComponent(commonFilter)}`;
    }
    if (commonSort) {
        url += `&sort=${encodeURIComponent(commonSort)}`;
    }

    fetch(url)
        .then(response => {
            console.log('Fetch finished loading:', `GET "${url}"`, response.status);
            if (!response.ok) {
                throw new Error(`Common names fetch failed with status ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Common names data:', data);
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
                    const rowId = `${key}_${item.name.replace(/\s+/g, '_')}`;
                    if (window.cachedTabNum == 2 || window.cachedTabNum == 4) {
                        html += `
                            <tr>
                                <td>${item.name}</td>
                                <td>${item.items_on_contracts}</td>
                                <td>${item.total_items}</td>
                                <td>
                                    <button class="btn btn-sm btn-secondary expand-btn" onclick="loadItems('${category}', '${subcategory || ''}', '${item.name}', 'items-${rowId}')">Expand</button>
                                    <button class="btn btn-sm btn-secondary collapse-btn" style="display:none;" onclick="collapseSection('items-${rowId}')">Collapse</button>
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
                                    <button class="btn btn-sm btn-secondary expand-btn" onclick="loadItems('${category}', '${subcategory || ''}', '${item.name}', 'items-${rowId}')">Expand</button>
                                    <button class="btn btn-sm btn-secondary collapse-btn" style="display:none;" onclick="collapseSection('items-${rowId}')">Collapse</button>
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

            console.log('Setting common names container HTML for targetId:', targetId);
            container.innerHTML = html;
            container.classList.remove('collapsed');
            container.classList.add('expanded');
            container.classList.remove('fade');
            container.classList.add('show');
            container.style.display = 'block';
            container.style.opacity = '1';
            console.log('Common names container classes after update:', container.className);
            console.log('Common names container updated with HTML:', container.innerHTML);

            // Debug the container's computed style
            const computedContainerStyle = window.getComputedStyle(container);
            console.log('Common names container computed style:', {
                display: computedContainerStyle.display,
                visibility: computedContainerStyle.visibility,
                opacity: computedContainerStyle.opacity,
                height: computedContainerStyle.height,
                transition: computedContainerStyle.transition
            });

            // Debug the common-level div
            const commonLevel = container.querySelector('.common-level');
            if (commonLevel) {
                const computedCommonLevelStyle = window.getComputedStyle(commonLevel);
                console.log('Common-level computed style:', {
                    display: computedCommonLevelStyle.display,
                    visibility: computedCommonLevelStyle.visibility,
                    opacity: computedCommonLevelStyle.opacity,
                    height: computedCommonLevelStyle.height
                });
            } else {
                console.log('Common-level div not found');
            }

            const expandBtn = document.querySelector(`button[onclick*="loadCommonNames('${category}', '${subcategory || ''}', '${targetId}')"]`);
            const collapseBtn = expandBtn ? expandBtn.nextElementSibling : null;
            if (expandBtn && collapseBtn) {
                expandBtn.style.display = 'none';
                collapseBtn.style.display = 'inline-block';
            }
        })
        .catch(error => {
            console.error('Common names fetch error:', error);
            container.innerHTML = `<div class="common-level"><p>Error loading common names: ${error.message}</p></div>`;
            container.classList.remove('collapsed');
            container.classList.add('expanded');
            container.classList.remove('fade');
            container.classList.add('show');
            container.style.display = 'block';
            container.style.opacity = '1';
        })
        .finally(() => {
            hideLoading(key);
            console.log('loadCommonNames completed for targetId:', targetId);
        });
}

function loadSubcatData(originalCategory, normalizedCategory, targetId, page = 1) {
    console.log('loadSubcatData called with', { originalCategory, normalizedCategory, targetId, page });

    const container = document.getElementById(targetId);
    console.log('Looking for container with ID:', targetId);
    if (!container) {
        console.error(`Container with ID ${targetId} not found`);
        return;
    }
    console.log('Container found:', container);
    console.log('Container classes before update:', container.className);

    hideOtherSubcats(normalizedCategory);
    showLoading(normalizedCategory);

    let url = `/tab/${window.cachedTabNum}/subcat_data?category=${encodeURIComponent(originalCategory)}&page=${page}`;
    const subcatFilter = document.getElementById(`subcat-filter-${normalizedCategory}`)?.value || '';
    const subcatSort = document.getElementById(`subcat-sort-${normalizedCategory}`)?.value || '';
    if (subcatFilter) {
        url += `&filter=${encodeURIComponent(subcatFilter)}`;
    }
    if (subcatSort) {
        url += `&sort=${encodeURIComponent(subcatSort)}`;
    }

    fetch(url)
        .then(response => {
            console.log('Fetch finished loading:', `GET "${url}"`);
            if (!response.ok) {
                throw new Error(`Subcategory fetch failed with status ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Subcategory data received:', data);
            // Detailed logging of the response
            if (data.subcategories && data.subcategories.length > 0) {
                console.log('Subcategories found:', data.subcategories);
                data.subcategories.forEach(subcat => {
                    console.log(`Subcategory: ${subcat.subcategory}, Total Items: ${subcat.total_items}, Items on Contracts: ${subcat.items_on_contracts}, Items in Service: ${subcat.items_in_service}, Items Available: ${subcat.items_available}`);
                });
            } else if (data.message) {
                console.log('No subcategories message:', data.message);
            } else {
                console.log('Unexpected response format:', data);
            }

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
                `;
                data.subcategories.forEach(subcat => {
                    console.log('Processing subcategory:', subcat);
                    const subcatKey = `${normalizedCategory}_${subcat.subcategory.toLowerCase().replace(/[^a-z0-9]/g, '_')}`;
                    const headers = ['Subcategory', 'Total Items', 'Items on Contracts', 'Items in Service', 'Items Available', 'Actions'];
                    html += `
                        <div class="subcat-level">
                            <table class="table table-bordered subcat-table mt-2" id="subcat-table-${subcatKey}">
                                <thead>
                                    <tr>
                                        ${headers.map(header => `<th>${header}</th>`).join('')}
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr class="subcat-row">
                                        <td>${subcat.subcategory}</td>
                                        <td>${subcat.total_items}</td>
                                        <td>${subcat.items_on_contracts}</td>
                                        <td>${subcat.items_in_service}</td>
                                        <td>${subcat.items_available}</td>
                                        <td>
                                            <button class="btn btn-sm btn-secondary expand-btn" onclick="loadCommonNames('${originalCategory}', '${subcat.subcategory}', '${subcatKey}')">Expand</button>
                                            <button class="btn btn-sm btn-secondary collapse-btn" style="display:none;" onclick="collapseSection('common-${subcatKey}')">Collapse</button>
                                            <button class="btn btn-sm btn-info print-btn" data-print-level="Subcategory" data-print-id="subcat-table-${subcatKey}">Print</button>
                                            <div id="loading-${subcatKey}" style="display:none;" class="loading">Loading...</div>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td colspan="${headers.length}">
                                            <div id="common-${subcatKey}" class="expandable collapsed"></div>
                                        </td>
                                    </tr>
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
                });
                console.log('Generated HTML for subcategories:', html);
            } else {
                html = `<div class="subcat-level"><p>No subcategories found for this category.</p></div>`;
            }

            console.log('Setting container HTML for targetId:', targetId);
            container.innerHTML = html;
            container.classList.remove('collapsed');
            container.classList.add('expanded');
            container.classList.remove('fade');
            container.classList.add('show');
            container.style.display = 'block';
            container.style.opacity = '1';
            console.log('Container classes after update:', container.className);
            console.log('Container updated with HTML:', container.innerHTML);

            // Debug the container's computed style
            const computedContainerStyle = window.getComputedStyle(container);
            console.log('Container computed style:', {
                display: computedContainerStyle.display,
                visibility: computedContainerStyle.visibility,
                opacity: computedContainerStyle.opacity,
                height: computedContainerStyle.height,
                transition: computedContainerStyle.transition
            });

            // Debug the parent <td> and <tr> styles
            const parentTd = container.parentElement;
            if (parentTd) {
                const computedTdStyle = window.getComputedStyle(parentTd);
                console.log('Parent <td> computed style:', {
                    display: computedTdStyle.display,
                    visibility: computedTdStyle.visibility,
                    opacity: computedTdStyle.opacity,
                    height: computedTdStyle.height
                });

                const parentTr = parentTd.parentElement;
                if (parentTr) {
                    const computedTrStyle = window.getComputedStyle(parentTr);
                    console.log('Parent <tr> computed style:', {
                        display: computedTrStyle.display,
                        visibility: computedTrStyle.visibility,
                        opacity: computedTrStyle.opacity,
                        height: computedTrStyle.height
                    });
                }
            }

            // Debug the subcat-level div
            const subcatLevel = container.querySelector('.subcat-level');
            if (subcatLevel) {
                const computedSubcatLevelStyle = window.getComputedStyle(subcatLevel);
                console.log('Subcat-level computed style:', {
                    display: computedSubcatLevelStyle.display,
                    visibility: computedSubcatLevelStyle.visibility,
                    opacity: computedSubcatLevelStyle.opacity,
                    height: computedSubcatLevelStyle.height
                });
            } else {
                console.log('Subcat-level div not found');
            }

            // Debug the subcategory row
            const subcatRow = container.querySelector('tbody tr.subcat-row');
            if (subcatRow) {
                console.log('Subcategory row found:', subcatRow);
                console.log('Subcategory row height:', subcatRow.offsetHeight);
                const computedStyle = window.getComputedStyle(subcatRow);
                console.log('Subcategory row computed style:', {
                    display: computedStyle.display,
                    visibility: computedStyle.visibility,
                    height: computedStyle.height,
                    minHeight: computedStyle.minHeight,
                    padding: computedStyle.padding,
                    margin: computedStyle.margin,
                    opacity: computedStyle.opacity
                });

                // Force a reflow on the container to ensure rendering
                container.style.display = 'none';
                void container.offsetHeight;
                container.style.display = 'block';
                container.style.opacity = '1';
                console.log('After container reflow, container display:', container.style.display, 'opacity:', container.style.opacity);

                // Force a reflow on the row
                subcatRow.style.display = 'table-row';
                subcatRow.style.opacity = '1';
                void subcatRow.offsetHeight;
                console.log('After row reflow, subcategory row height:', subcatRow.offsetHeight);
            } else {
                console.log('Subcategory row not found in DOM');
            }
        })
        .catch(error => {
            console.error('Subcategory fetch error:', error);
            container.innerHTML = `<div class="subcat-level"><p>Error loading subcategories: ${error.message}</p></div>`;
            container.classList.remove('collapsed');
            container.classList.add('expanded');
            container.classList.remove('fade');
            container.classList.add('show');
            container.style.display = 'block';
            container.style.opacity = '1';
        })
        .finally(() => {
            hideLoading(normalizedCategory);
            console.log('loadSubcatData completed for targetId:', targetId);
        });
}

function loadItems(category, subcategory, commonName, targetId, page = 1) {
    console.log('loadItems called with', { category, subcategory, commonName, targetId, page });

    const container = document.getElementById(targetId);
    if (!container) {
        console.error(`Container with ID ${targetId} not found`);
        return;
    }

    const key = `${category}_${subcategory || ''}_${commonName.replace(/\s+/g, '_')}`;
    showLoading(key);
    hideOtherItems(targetId);

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
    if (itemFilter) {
        url += `&filter=${encodeURIComponent(itemFilter)}`;
    }
    if (itemSort) {
        url += `&sort=${encodeURIComponent(itemSort)}`;
    }

    fetch(url)
        .then(response => {
            console.log('Fetch finished loading:', `GET "${url}"`);
            if (!response.ok) {
                throw new Error(`Items fetch failed with status ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Items data:', data);
            let html = '';
            if (data.items && data.items.length > 0) {
                const headers = ['Tag ID', 'Common Name', 'Bin Location', 'Status', 'Last Contract', 'Last Scanned Date'];
                if (window.cachedTabNum == 1 || window.cachedTabNum == 5) {
                    headers.push('Quality', 'Notes');
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
                    if (window.cachedTabNum == 1 || window.cachedTabNum == 5) {
                        html += `
                            <tr>
                                <td>${item.tag_id}</td>
                                <td>${item.common_name}</td>
                                <td>${item.bin_location || 'N/A'}</td>
                                <td>${item.status}</td>
                                <td>${item.last_contract_num || 'N/A'}</td>
                                <td>${lastScanned}</td>
                                <td>${item.quality || 'N/A'}</td>
                                <td>${item.notes || 'N/A'}</td>
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

                if (data.total_items > data.per_page) {
                    const totalPages = Math.ceil(data.total_items / data.per_page);
                    html += `
                        <tr>
                            <td colspan="${headers.length}" class="pagination-controls">
                                <button class="btn btn-sm btn-secondary" onclick="loadItems('${category}', '${subcategory || ''}', '${commonName}', '${targetId}', ${page - 1})" ${page === 1 ? 'disabled' : ''}>Previous</button>
                                <span>Page ${page} of ${totalPages}</span>
                                <button class="btn btn-sm btn-secondary" onclick="loadItems('${category}', '${subcategory || ''}', '${commonName}', '${targetId}', ${page + 1})" ${page === totalPages ? 'disabled' : ''}>Next</button>
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
                html = `<div class="item-level-wrapper"><p>No items found for this common name.</p></div>`;
            }

            container.innerHTML = html;
            container.classList.remove('collapsed');
            container.classList.add('expanded');
            container.classList.remove('fade');
            container.classList.add('show');
            container.style.display = 'block';
            container.style.opacity = '1';

            const expandBtn = document.querySelector(`button[onclick*="loadItems('${category}', '${subcategory || ''}', '${commonName}', '${targetId}')"]`);
            const collapseBtn = expandBtn ? expandBtn.nextElementSibling : null;
            if (expandBtn && collapseBtn) {
                expandBtn.style.display = 'none';
                collapseBtn.style.display = 'inline-block';
            }
        })
        .catch(error => {
            console.error('Items fetch error:', error);
            container.innerHTML = `<div class="item-level-wrapper"><p>Error loading items: ${error.message}</p></div>`;
            container.classList.remove('collapsed');
            container.classList.add('expanded');
            container.classList.remove('fade');
            container.classList.add('show');
            container.style.display = 'block';
            container.style.opacity = '1';
        })
        .finally(() => {
            hideLoading(key);
            console.log('loadItems completed for targetId:', targetId);
        });
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('expand.js: DOMContentLoaded event fired');
    window.expandCategory = function(category, targetId, contractNumber = null, page = 1) {
        console.log('expandCategory called with', { category, targetId, contractNumber, page });
        const normalizedCategory = targetId.replace('subcat-', '');
        if (window.cachedTabNum == 2 || window.cachedTabNum == 4) {
            loadCommonNames(category, null, targetId, page, contractNumber);
        } else {
            loadSubcatData(category, normalizedCategory, targetId, page);
        }
    };
    console.log('expand.js: expandCategory defined');
});