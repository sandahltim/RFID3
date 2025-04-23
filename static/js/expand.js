console.log('expand.js version: 2025-04-23 v27 loaded');

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
            div.style.display = 'none';
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
            div.style.display = 'none';
        }
    });
}

function collapseSection(targetId) {
    const section = document.getElementById(targetId);
    if (section) {
        section.classList.remove('expanded');
        section.classList.add('collapsed');
        section.style.display = 'none';

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

    // For Tabs 2 and 4, targetId is already the correct container ID (e.g., 'common-212761')
    // For Tabs 1, 3, and 5, targetId is a base ID (e.g., 'resale_resale'), so we need to prepend 'common-'
    const containerId = (window.cachedTabNum == 2 || window.cachedTabNum == 4) ? targetId : `common-${targetId}`;
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container with ID ${containerId} not found`);
        return;
    }

    const key = subcategory ? `${category}_${subcategory}` : category;
    showLoading(key);
    hideOtherCommonNames(containerId);

    let url = `/tab/${window.cachedTabNum}/common_names?category=${encodeURIComponent(category)}&page=${page}`;
    if (contractNumber) {
        url += `&contract_number=${encodeURIComponent(contractNumber)}`;
    }
    if (subcategory) {
        url += `&subcategory=${encodeURIComponent(subcategory)}`;
    }

    fetch(url)
        .then(response => {
            console.log('Fetch finished loading:', `GET "${url}"`);
            if (!response.ok) {
                throw new Error(`Common names fetch failed with status ${response.status}`);
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
                                <td>${item.on_contracts}</td>
                                <td>${item.total_items_inventory}</td>
                                <td>
                                    <button class="btn btn-sm btn-secondary expand-btn" onclick="loadItems('${category}', '${subcategory || ''}', '${item.name}', 'items-${rowId}')">Expand</button>
                                    <button class="btn btn-sm btn-secondary collapse-btn" style="display:none;" onclick="collapseSection('items-${rowId}')">Collapse</button>
                                    <button class="btn btn-sm btn-info print-btn" data-print-level="Common Name" data-print-id="common-table-${key}">Print</button>
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
                                <td>${item.in_service}</td>
                                <td>${item.available}</td>
                                <td>
                                    <button class="btn btn-sm btn-secondary expand-btn" onclick="loadItems('${category}', '${subcategory || ''}', '${item.name}', 'items-${rowId}')">Expand</button>
                                    <button class="btn btn-sm btn-secondary collapse-btn" style="display:none;" onclick="collapseSection('items-${rowId}')">Collapse</button>
                                    <button class="btn btn-sm btn-info print-btn" data-print-level="Common Name" data-print-id="common-table-${key}">Print</button>
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
                                <button class="btn btn-sm btn-secondary" onclick="loadCommonNames('${category}', '${subcategory || ''}', '${targetId}', ${page - 1})" ${page === 1 ? 'disabled' : ''}>Previous</button>
                                <span>Page ${page} of ${totalPages}</span>
                                <button class="btn btn-sm btn-secondary" onclick="loadCommonNames('${category}', '${subcategory || ''}', '${targetId}', ${page + 1})" ${page === totalPages ? 'disabled' : ''}>Next</button>
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
            container.style.display = 'block';
        })
        .finally(() => {
            hideLoading(key);
            console.log('loadCommonNames completed for targetId:', targetId);
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

    let url = `/tab/${window.cachedTabNum}/data?category=${encodeURIComponent(category)}&common_name=${encodeURIComponent(commonName)}&page=${page}`;
    if (subcategory) {
        url += `&subcategory=${encodeURIComponent(subcategory)}`;
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
            let html = '';
            if (data.items && data.items.length > 0) {
                const headers = ['Tag ID', 'Common Name', 'Bin Location', 'Status', 'Last Contract', 'Last Scanned Date'];
                if (window.cachedTabNum == 1 || window.cachedTabNum == 5) {
                    headers.push('Quality', 'Notes');
                }

                html += `
                    <div class="item-level-wrapper">
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
            container.style.display = 'block';

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
            container.style.display = 'block';
        })
        .finally(() => {
            hideLoading(key);
            console.log('loadItems completed for targetId:', targetId);
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

    hideOtherSubcats(normalizedCategory);
    showLoading(normalizedCategory);

    fetch(`/tab/${window.cachedTabNum}/subcat_data?category=${encodeURIComponent(originalCategory)}&page=${page}`)
        .then(response => {
            console.log('Fetch finished loading:', `GET "/tab/${window.cachedTabNum}/subcat_data?category=${encodeURIComponent(originalCategory)}&page=${page}"`);
            if (!response.ok) {
                throw new Error(`Subcategory fetch failed with status ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            let html = '';
            if (data.subcategories && data.subcategories.length > 0) {
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
                                    <tr>
                                        <td>${subcat.subcategory}</td>
                                        <td>${subcat.total_items}</td>
                                        <td>${subcat.on_contracts}</td>
                                        <td>${subcat.in_service}</td>
                                        <td>${subcat.available}</td>
                                        <td>
                                            <button class="btn btn-sm btn-secondary expand-btn" onclick="loadCommonNames('${originalCategory}', '${subcat.subcategory}', '${subcatKey}')">Expand</button>
                                            <button class="btn btn-sm btn-secondary collapse-btn" style="display:none;" onclick="collapseSection('common-${subcatKey}')">Collapse</button>
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

                    if (data.total_subcats > data.per_page) {
                        const totalPages = Math.ceil(data.total_subcats / data.per_page);
                        html += `
                            <tr>
                                <td colspan="6" class="pagination-controls">
                                    <button class="btn btn-sm btn-secondary" onclick="loadSubcatData('${originalCategory}', '${normalizedCategory}', '${targetId}', ${page - 1})" ${page === 1 ? 'disabled' : ''}>Previous</button>
                                    <span>Page ${page} of ${totalPages}</span>
                                    <button class="btn btn-sm btn-secondary" onclick="loadSubcatData('${originalCategory}', '${normalizedCategory}', '${targetId}', ${page + 1})" ${page === totalPages ? 'disabled' : ''}>Next</button>
                                </td>
                            </tr>
                        `;
                    }

                    html += `
                                </tbody>
                            </table>
                        </div>
                    `;
                });
            } else {
                html = `<div class="subcat-level"><p>No subcategories found for this category.</p></div>`;
            }

            container.innerHTML = html;
            container.classList.remove('collapsed');
            container.classList.add('expanded');
            container.style.display = 'block';

            const expandBtn = document.querySelector(`button[onclick*="loadSubcatData('${originalCategory}', '${normalizedCategory}', '${targetId}')"]`);
            const collapseBtn = expandBtn ? expandBtn.nextElementSibling : null;
            if (expandBtn && collapseBtn) {
                expandBtn.style.display = 'none';
                collapseBtn.style.display = 'inline-block';
            }
        })
        .catch(error => {
            console.error('Subcategory fetch error:', error);
            container.innerHTML = `<div class="subcat-level"><p>Error loading subcategories: ${error.message}</p></div>`;
            container.classList.remove('collapsed');
            container.classList.add('expanded');
            container.style.display = 'block';
        })
        .finally(() => {
            hideLoading(normalizedCategory);
            console.log('loadSubcatData completed for targetId:', targetId);
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