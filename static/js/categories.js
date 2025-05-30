// app/static/js/categories.js
console.log('categories.js version: 2025-05-29-v1 loaded');

let mappings = [];

function addMappingRow(mapping = {category: '', subcategory: '', rental_class_id: '', common_name: 'N/A', short_common_name: ''}) {
    // ... (move from categories.html)
}

function removeMappingRow(button) {
    // ... (move from categories.html)
}

function collectMappings() {
    // ... (move from categories.html)
}

function confirmSaveMappings() {
    // ... (move from categories.html)
}

function saveMappings(validMappings) {
    // ... (move from categories.html)
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('mappings-table').innerHTML = '';
    fetch('/categories/mapping')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to fetch mappings: HTTP status ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                alert('Failed to load mappings: ' + data.error);
                return;
            }
            data.forEach(mapping => addMappingRow(mapping));
        })
        .catch(error => {
            console.error('Error loading mappings:', error);
            alert('Failed to load mappings: ' + error.message);
        });

    if (typeof window.applyGlobalFilter === 'function') {
        window.applyGlobalFilter();
    }
});