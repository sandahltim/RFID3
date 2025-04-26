console.log('expand.js version: 2025-04-26-v65 loaded');

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
            const subcategory = expandBtn.getAttribute('data-subcategory');
            const targetId = expandBtn.getAttribute('data-target-id');
            const commonName = expandBtn.getAttribute('data-common-name');

            if (commonName) {
                // For Tabs 2, 3, 4: load items (functionality TBD)
                console.log('Expand items for Tabs 2, 3, 4 not implemented in expand.js');
            } else if (subcategory) {
                // For Tabs 2, 3, 4: load common names (functionality TBD)
                console.log('Expand common names for Tabs 2, 3, 4 not implemented in expand.js');
            } else {
                // For Tabs 2, 3, 4: load subcategories (functionality TBD)
                console.log('Expand subcategories for Tabs 2, 3, 4 not implemented in expand.js');
            }
            return;
        }

        const collapseBtn = event.target.closest('.collapse-btn');
        if (collapseBtn) {
            event.stopPropagation();
            const targetId = collapseBtn.getAttribute('data-collapse-target');
            // Collapse functionality TBD for Tabs 2, 3, 4
            console.log('Collapse for Tabs 2, 3, 4 not implemented in expand.js');
            return;
        }
    }

    // Define expandCategory as a placeholder for Tabs 2, 3, 4
    window.expandCategory = function(category, targetId, contractNumber = null, page = 1) {
        console.log('expandCategory called with', { category, targetId, contractNumber, page });
        console.log('expandCategory for Tabs 2, 3, 4 not fully implemented in expand.js');
    };
});