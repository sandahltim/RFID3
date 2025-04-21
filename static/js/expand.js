// expand.js - Handles category expansion for RFID Dashboard
// Module Purpose: Expands categories to show subcategories on the tab page

document.addEventListener('DOMContentLoaded', () => {
    console.log('expand.js: DOMContentLoaded event fired');
    
    // Define expandCategory globally to handle category expansion
    window.expandCategory = function(category, targetId) {
        console.log('expandCategory called with category:', category, 'targetId:', targetId);
        const url = '/tab/' + window.cachedTabNum + '/subcat_data?category=' + category;
        
        fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Subcat fetch failed with status ' + response.status);
                }
                return response.json();
            })
            .then(data => {
                console.log('Subcat data received:', data);
                // Placeholder: We'll add rendering logic in the next step
            })
            .catch(error => {
                console.error('Subcat fetch error:', error);
            });
    };
    
    console.log('expand.js: expandCategory defined');
});