console.log('categories.js version: 2025-06-26-v5 loaded');

/**
 * categories.js: Logic for Manage Categories tab.
 * Dependencies: None (self-contained).
 * Updated: 2025-06-26-v5
 * - Fixed endpoint URL from /categories/mapping to /categories/mappings.
 * - Added tracking for edited rows with data-edited attribute.
 * - Modified collectMappings to send only edited mappings.
 * - Added clearEdits function for resetting changes.
 * - Preserved all existing functionality.
 */

(function() {
    let mappings = [];

    function addMappingRow(mapping = {category: '', subcategory: '', rental_class_id: '', common_name: 'N/A', short_common_name: ''}) {
        const table = document.getElementById('mappings-table');
        if (!table) {
            console.error(`Mappings table not found at ${new Date().toISOString()}`);
            return;
        }
        const tbody = table.querySelector('tbody') || table.appendChild(document.createElement('tbody'));
        
        const row = document.createElement('tr');
        row.setAttribute('data-edited', 'false');
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
        console.log(`Added mapping row: ${JSON.stringify(mapping)} at ${new Date().toISOString()}`);

        // Mark row as edited on input change
        row.querySelectorAll('input').forEach(input => {
            input.addEventListener('change', () => {
                row.setAttribute('data-edited', 'true');
                console.log(`Row marked as edited: ${JSON.stringify(collectRowData(row))} at ${new Date().toISOString()}`);
            });
        });
    }

    function removeMappingRow(button) {
        const row = button.closest('tr');
        if (!row) {
            console.error(`Row not found for removal at ${new Date().toISOString()}`);
            return;
        }
        const index = Array.from(row.parentNode.children).indexOf(row);
        mappings.splice(index, 1);
        row.remove();
        console.log(`Removed mapping row at index ${index} at ${new Date().toISOString()}`);
    }

    function collectRowData(row) {
        const category = row.querySelector('.category-input')?.value?.trim();
        const subcategory = row.querySelector('.subcategory-input')?.value?.trim();
        const rental_class_id = row.querySelector('.rental-class-id-input')?.value?.trim();
        const short_common_name = row.querySelector('.short-common-name-input')?.value?.trim();
        return { rental_class_id, category, subcategory, short_common_name: short_common_name || '' };
    }

    function collectMappings() {
        const rows = document.querySelectorAll('#mappings-table tbody tr[data-edited="true"]');
        const validMappings = [];
        rows.forEach((row, index) => {
            const mapping = collectRowData(row);
            if (mapping.rental_class_id && mapping.category && mapping.subcategory) {
                validMappings.push(mapping);
                console.log(`Collected edited mapping at row ${index}: ${JSON.stringify(mapping)} at ${new Date().toISOString()}`);
            } else {
                console.warn(`Skipping invalid edited mapping at row ${index}: ${JSON.stringify(mapping)} at ${new Date().toISOString()}`);
            }
        });
        return validMappings;
    }

    function clearEdits() {
        const rows = document.querySelectorAll('#mappings-table tbody tr');
        rows.forEach(row => {
            row.setAttribute('data-edited', 'false');
        });
        console.log(`Cleared edit flags for ${rows.length} rows at ${new Date().toISOString()}`);
    }

    function confirmSaveMappings() {
        const validMappings = collectMappings();
        if (validMappings.length === 0) {
            alert('No edited mappings to save. Make changes to rows before saving.');
            return;
        }
        if (confirm(`Are you sure you want to save ${validMappings.length} edited mappings?`)) {
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
            console.log(`Save mappings status: ${response.status} at ${new Date().toISOString()}`);
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`Failed to save mappings: ${response.status} - ${text}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                alert('Failed to save mappings: ' + data.error);
                console.error('Error saving mappings:', data.error, `at ${new Date().toISOString()}`);
            } else {
                alert('Mappings saved successfully');
                console.log('Mappings saved:', validMappings, `at ${new Date().toISOString()}`);
                mappings = validMappings; // Update local mappings
                clearEdits(); // Reset edit flags
            }
        })
        .catch(error => {
            alert('Failed to save mappings: ' + error.message);
            console.error('Error saving mappings:', error, `at ${new Date().toISOString()}`);
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        console.log(`categories.js: DOMContentLoaded triggered at ${new Date().toISOString()}`);
        const table = document.getElementById('mappings-table');
        if (!table) {
            console.error(`Mappings table not found on page load at ${new Date().toISOString()}`);
            return;
        }
        table.innerHTML = '<tbody></tbody>'; // Ensure tbody exists
        fetch('/categories/mappings', {
            method: 'GET',
            headers: {'Content-Type': 'application/json'}
        })
        .then(response => {
            console.log(`Fetch mappings status: ${response.status} at ${new Date().toISOString()}`);
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`Failed to fetch mappings: ${response.status} - ${text}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                alert('Failed to load mappings: ' + data.error);
                console.error('Error loading mappings:', data.error, `at ${new Date().toISOString()}`);
                return;
            }
            mappings = data || [];
            if (mappings.length === 0) {
                console.warn(`No mappings returned from /categories/mappings at ${new Date().toISOString()}`);
                addMappingRow(); // Add an empty row for user input
            } else {
                mappings.forEach(mapping => addMappingRow(mapping));
            }
            console.log(`Loaded ${mappings.length} mappings at ${new Date().toISOString()}`);
        })
        .then(() => {
            const addButton = document.getElementById('add-mapping-btn');
            const saveButton = document.getElementById('save-mappings-btn');
            const clearButton = document.getElementById('clear-changes-btn');

            if (addButton) {
                addButton.addEventListener('click', () => {
                    addMappingRow();
                    console.log('Add mapping button clicked');
                });
            }
            if (saveButton) {
                saveButton.addEventListener('click', confirmSaveMappings);
                console.log('Save mappings button initialized');
            }
            if (clearButton) {
                clearButton.addEventListener('click', clearEdits);
                console.log('Clear changes button initialized');
            }
        })
        .catch(error => {
            console.error('Error loading mappings:', error, `at ${new Date().toISOString()}`);
            alert('Failed to load mappings: ' + error.message);
            addMappingRow(); // Add an empty row on error
        });
    });

    // Expose functions to global scope safely
    window.categories = {
        addMappingRow,
        removeMappingRow,
        confirmSaveMappings,
        clearEdits
    };
})();