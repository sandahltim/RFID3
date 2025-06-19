// app/static/js/categories.js
// categories.js version: 2025-06-19-v3
(function() {
    console.log('categories.js version: 2025-06-19-v3 loaded');

    let mappings = [];

    function addMappingRow(mapping = {category: '', subcategory: '', rental_class_id: '', common_name: 'N/A', short_common_name: ''}) {
        const table = document.getElementById('mappings-table');
        if (!table) {
            console.error('Mappings table not found');
            return;
        }
        const tbody = table.querySelector('tbody') || table.appendChild(document.createElement('tbody'));
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><input type="text" class="form-control category-input" value="${mapping.category || ''}"></td>
            <td><input type="text" class="form-control subcategory-input" value="${mapping.subcategory || ''}"></td>
            <td><input type="text" class="form-control rental-class-id-input" value="${mapping.rental_class_id || ''}"></td>
            <td>${mapping.common_name || 'N/A'}</td>
            <td><input type="text" class="form-control short-common-name-input" value="${mapping.short_common_name || ''}"></td>
            <td>
                <button class="btn btn-danger btn-sm remove-btn" onclick="window.categories.removeMappingRow(this)">Remove</button>
            </td>
        `;
        tbody.appendChild(row);
        mappings.push(mapping);
        console.log(`Added mapping row: ${JSON.stringify(mapping)}`);
    }

    function removeMappingRow(button) {
        const row = button.closest('tr');
        if (!row) {
            console.error('Row not found for removal');
            return;
        }
        const index = Array.from(row.parentNode.children).indexOf(row);
        mappings.splice(index, 1);
        row.remove();
        console.log(`Removed mapping row at index ${index}`);
    }

    function collectMappings() {
        const rows = document.querySelectorAll('#mappings-table tbody tr');
        const validMappings = [];
        rows.forEach((row, index) => {
            const category = row.querySelector('.category-input')?.value?.trim();
            const subcategory = row.querySelector('.subcategory-input')?.value?.trim();
            const rental_class_id = row.querySelector('.rental-class-id-input')?.value?.trim();
            const short_common_name = row.querySelector('.short-common-name-input')?.value?.trim();
            
            if (rental_class_id && category && subcategory) {
                validMappings.push({
                    rental_class_id,
                    category,
                    subcategory,
                    short_common_name: short_common_name || ''
                });
                console.log(`Collected valid mapping at row ${index}: ${JSON.stringify(validMappings[validMappings.length - 1])}`);
            } else {
                console.warn(`Skipping invalid mapping at row ${index}: rental_class_id=${rental_class_id}, category=${category}, subcategory=${subcategory}`);
            }
        });
        return validMappings;
    }

    function confirmSaveMappings() {
        const validMappings = collectMappings();
        if (validMappings.length === 0) {
            alert('No valid mappings to save. Ensure all rows have rental class ID, category, and subcategory.');
            return;
        }
        if (confirm(`Are you sure you want to save ${validMappings.length} mappings? This will overwrite existing user mappings.`)) {
            saveMappings(validMappings);
        }
    }

    function saveMappings(validMappings) {
        fetch('/categories/update', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(validMappings)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to save mappings: HTTP status ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                alert('Failed to save mappings: ' + data.error);
                console.error('Error saving mappings:', data.error);
            } else {
                alert('Mappings saved successfully');
                console.log('Mappings saved:', validMappings);
                mappings = validMappings; // Update local mappings
            }
        })
        .catch(error => {
            alert('Failed to save mappings: ' + error.message);
            console.error('Error saving mappings:', error);
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        console.log('categories.js: DOMContentLoaded triggered');
        const table = document.getElementById('mappings-table');
        if (!table) {
            console.error('Mappings table not found on page load');
            return;
        }
        table.innerHTML = '<tbody></tbody>'; // Ensure tbody exists
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
                    console.error('Error loading mappings:', data.error);
                    return;
                }
                mappings = data || [];
                if (mappings.length === 0) {
                    console.warn('No mappings returned from /categories/mapping');
                    addMappingRow(); // Add an empty row for user input
                } else {
                    mappings.forEach(mapping => addMappingRow(mapping));
                }
                console.log(`Loaded ${mappings.length} mappings`);
            })
            .catch(error => {
                console.error('Error loading mappings:', error);
                alert('Failed to load mappings: ' + error.message);
                addMappingRow(); // Add an empty row on error
            });

        if (typeof window.applyGlobalFilter === 'function') {
            window.applyGlobalFilter();
        }
    });

    // Expose functions to global scope safely
    window.categories = {
        addMappingRow,
        removeMappingRow,
        confirmSaveMappings
    };
})();