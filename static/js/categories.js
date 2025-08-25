console.log('categories.js version: 2025-07-02-v6 loaded');

/**
 * categories.js: Logic for Manage Categories tab.
 * Dependencies: None (self-contained).
 * Updated: 2025-07-02-v6
 * - Fixed duplicate rows caused by array mutation during load.
 * - Added client-side sorting for Category, Subcategory, and Common Name.
 * - Implemented floating action buttons at the bottom of the view.
 * - Preserved existing functionality.
 */

(function() {
    let mappings = [];
    let currentSort = { column: null, direction: 'asc' };

    function addMappingRow(mapping = {category: '', subcategory: '', rental_class_id: '', common_name: '', short_common_name: '', is_hand_counted: false, hand_counted_name: ''}) {
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
            <td><input type="text" class="form-control common-name-input" value="${mapping.common_name || ''}" ${mapping.rental_class_id ? 'readonly' : ''}></td>
            <td><input type="text" class="form-control short-common-name-input" value="${mapping.short_common_name || ''}"></td>
            <td class="text-center"><input type="checkbox" class="form-check-input hand-counted-checkbox" ${mapping.is_hand_counted ? 'checked' : ''}></td>
            <td><input type="text" class="form-control hand-counted-name-input" value="${mapping.hand_counted_name || ''}" placeholder="Optional display name"></td>
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
        const common_name = row.querySelector('.common-name-input')?.value?.trim();
        const short_common_name = row.querySelector('.short-common-name-input')?.value?.trim();
        const is_hand_counted = row.querySelector('.hand-counted-checkbox')?.checked || false;
        const hand_counted_name = row.querySelector('.hand-counted-name-input')?.value?.trim();
        return { rental_class_id, category, subcategory, common_name: common_name || '', short_common_name: short_common_name || '', is_hand_counted, hand_counted_name: hand_counted_name || '' };
    }

    function collectMappings() {
        const rows = document.querySelectorAll('#mappings-table tbody tr[data-edited="true"]');
        const validMappings = [];
        rows.forEach((row, index) => {
            const mapping = collectRowData(row);
            if ((mapping.rental_class_id && mapping.category && mapping.subcategory) || (mapping.is_hand_counted && mapping.common_name)) {
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

    function getCellValue(row, column) {
        switch(column) {
            case 'category':
                return row.querySelector('.category-input')?.value?.toLowerCase() || '';
            case 'subcategory':
                return row.querySelector('.subcategory-input')?.value?.toLowerCase() || '';
            case 'common_name':
                return row.querySelector('.common-name-input')?.value?.toLowerCase() || '';
            default:
                return '';
        }
    }

    function updateSortIndicators(column, direction) {
        document.querySelectorAll('#mappings-table th.sortable').forEach(th => {
            let arrow = th.querySelector('.sort-arrow');
            if (!arrow) {
                arrow = document.createElement('span');
                arrow.className = 'sort-arrow';
                th.appendChild(arrow);
            }
            if (th.dataset.column === column) {
                arrow.textContent = direction === 'asc' ? '↑' : '↓';
            } else {
                arrow.textContent = '';
            }
        });
    }

    function sortTable(column) {
        const table = document.getElementById('mappings-table');
        if (!table) return;
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const direction = currentSort.column === column && currentSort.direction === 'asc' ? 'desc' : 'asc';
        rows.sort((a, b) => {
            const aVal = getCellValue(a, column);
            const bVal = getCellValue(b, column);
            return direction === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
        });
        rows.forEach(row => tbody.appendChild(row));
        currentSort = { column, direction };
        updateSortIndicators(column, direction);
    }

    document.addEventListener('DOMContentLoaded', () => {
        console.log(`categories.js: DOMContentLoaded triggered at ${new Date().toISOString()}`);
        const table = document.getElementById('mappings-table');
        if (!table) {
            console.error(`Mappings table not found on page load at ${new Date().toISOString()}`);
            return;
        }
        const existingTbody = table.querySelector('tbody');
        if (existingTbody) {
            existingTbody.innerHTML = '';
        } else {
            table.appendChild(document.createElement('tbody'));
        }
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
            mappings = [];
            const dataMappings = data || [];
            if (dataMappings.length === 0) {
                console.warn(`No mappings returned from /categories/mappings at ${new Date().toISOString()}`);
                addMappingRow(); // Add an empty row for user input
            } else {
                dataMappings.forEach(mapping => addMappingRow(mapping));
            }
            console.log(`Loaded ${dataMappings.length} mappings at ${new Date().toISOString()}`);
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
            document.querySelectorAll('#mappings-table th.sortable').forEach(th => {
                th.addEventListener('click', () => sortTable(th.dataset.column));
            });
        })
        .catch(error => {
            console.error('Error loading mappings:', error, `at ${new Date().toISOString()}`);
            alert('Failed to load mappings: ' + error.message);
            addMappingRow(); // Add an empty row on error
        });
    });

    // Export/Import functionality
    let pendingImportData = null;
    
    function hideModal(modalId) {
        // Hide modal reliably
        const modalElement = document.getElementById(modalId);
        if (modalElement) {
            modalElement.style.display = 'none';
            modalElement.classList.remove('show');
            modalElement.setAttribute('aria-hidden', 'true');
            document.body.classList.remove('modal-open');
            
            // Remove backdrop
            const backdrop = document.getElementById(modalId + '-backdrop');
            if (backdrop) {
                backdrop.remove();
            }
        }
    }
    
    function showModal(modalId) {
        // Show modal reliably
        const modalElement = document.getElementById(modalId);
        if (modalElement) {
            modalElement.style.display = 'block';
            modalElement.classList.add('show');
            modalElement.setAttribute('aria-hidden', 'false');
            document.body.classList.add('modal-open');
            
            // Add backdrop
            const backdrop = document.createElement('div');
            backdrop.className = 'modal-backdrop fade show';
            backdrop.id = modalId + '-backdrop';
            backdrop.onclick = () => hideModal(modalId); // Close on backdrop click
            document.body.appendChild(backdrop);
            
            // Add close functionality to close buttons
            const closeButtons = modalElement.querySelectorAll('[data-bs-dismiss="modal"], .btn-close');
            closeButtons.forEach(btn => {
                btn.onclick = () => hideModal(modalId);
            });
        }
    }
    
    function showExportModal() {
        showModal('export-modal');
    }
    
    async function exportCategoriesWithOptions() {
        try {
            console.log('Starting export with options...');
            
            // Get selected options
            const includeUserMappings = document.getElementById('export-user-mappings').checked;
            const includeHandCounted = document.getElementById('export-hand-counted').checked;
            const includeRentalMappings = document.getElementById('export-rental-mappings').checked;
            
            if (!includeUserMappings && !includeHandCounted && !includeRentalMappings) {
                alert('❌ Please select at least one data type to export');
                return;
            }
            
            // Build query parameters
            const params = new URLSearchParams();
            if (includeUserMappings) params.append('include', 'user_mappings');
            if (includeHandCounted) params.append('include', 'hand_counted');
            if (includeRentalMappings) params.append('include', 'rental_mappings');
            
            const response = await fetch(`/categories/export?${params.toString()}`);
            if (!response.ok) {
                throw new Error(`Export failed: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Create download with descriptive filename
            const selectedTypes = [];
            if (includeUserMappings) selectedTypes.push('mappings');
            if (includeHandCounted) selectedTypes.push('handcounted');
            if (includeRentalMappings) selectedTypes.push('rentals');
            
            const typeString = selectedTypes.length === 3 ? 'complete' : selectedTypes.join('-');
            const filename = `rfid3-${typeString}-backup-${new Date().toISOString().split('T')[0]}.json`;
            
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            // Show success message
            const exportedItems = [];
            if (data.counts.user_mappings) exportedItems.push(`${data.counts.user_mappings} user mappings`);
            if (data.counts.hand_counted_items) exportedItems.push(`${data.counts.hand_counted_items} hand-counted items`);
            if (data.counts.rental_mappings) exportedItems.push(`${data.counts.rental_mappings} rental mappings`);
            
            alert(`✅ Export completed!\n\nFile: ${filename}\n\nExported:\n• ${exportedItems.join('\n• ')}`);
            
            // Hide modal
            hideModal('export-modal');
            
        } catch (error) {
            console.error('Export error:', error);
            alert(`❌ Export failed: ${error.message}`);
        }
    }
    
    // Legacy function for direct export (all data)
    async function exportCategories() {
        // Set all checkboxes to true and export
        document.getElementById('export-user-mappings').checked = true;
        document.getElementById('export-hand-counted').checked = true;
        document.getElementById('export-rental-mappings').checked = true;
        await exportCategoriesWithOptions();
    }
    
    function handleImportFile(fileInput) {
        const file = fileInput.files[0];
        if (!file) return;
        
        if (!file.name.endsWith('.json')) {
            alert('❌ Please select a JSON file');
            fileInput.value = '';
            return;
        }
        
        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                const data = JSON.parse(e.target.result);
                
                // Validate file structure
                if (!data.export_info || !data.user_rental_class_mappings || !data.hand_counted_catalog) {
                    throw new Error('Invalid export file format');
                }
                
                // Store data and show modal
                pendingImportData = data;
                document.getElementById('import-filename').textContent = file.name;
                
                // Show preview
                const preview = document.getElementById('import-preview');
                preview.innerHTML = `
                    <div class="alert alert-info">
                        <strong>Export Info:</strong><br>
                        • Exported: ${new Date(data.export_info.exported_at).toLocaleString()}<br>
                        • Version: ${data.export_info.version}<br><br>
                        <strong>Contains:</strong><br>
                        • ${data.user_rental_class_mappings.length} user mappings<br>
                        • ${data.hand_counted_catalog.length} hand-counted items<br>
                        • ${(data.rental_class_mappings || []).length} rental mappings
                    </div>
                `;
                
                // Show modal
                showModal('import-modal');
                
            } catch (error) {
                console.error('File parse error:', error);
                alert(`❌ Invalid file: ${error.message}`);
                fileInput.value = '';
            }
        };
        
        reader.readAsText(file);
    }
    
    async function confirmImport() {
        if (!pendingImportData) {
            alert('❌ No import data available');
            return;
        }
        
        try {
            const mode = document.querySelector('input[name="import-mode"]:checked').value;
            console.log(`Starting import in ${mode} mode...`);
            
            const response = await fetch(`/categories/import?mode=${mode}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(pendingImportData)
            });
            
            const result = await response.json();
            
            if (!result.success) {
                throw new Error(result.error || 'Import failed');
            }
            
            // Show success message
            const results = result.results;
            const summary = [
                `✅ Import completed successfully!`,
                ``,
                `User Mappings:`,
                `• Added: ${results.user_mappings.added}`,
                `• Updated: ${results.user_mappings.updated}`,
                `• Skipped: ${results.user_mappings.skipped}`,
                ``,
                `Hand-Counted Items:`,
                `• Added: ${results.hand_counted.added}`,
                `• Updated: ${results.hand_counted.updated}`,
                `• Skipped: ${results.hand_counted.skipped}`
            ];
            
            if (results.rental_mappings.added > 0) {
                summary.push(``, `Rental Mappings:`, `• Added: ${results.rental_mappings.added}`);
            }
            
            alert(summary.join('\n'));
            
            // Hide modal and reload page
            hideModal('import-modal');
            
            // Reload the categories
            location.reload();
            
        } catch (error) {
            console.error('Import error:', error);
            alert(`❌ Import failed: ${error.message}`);
        } finally {
            pendingImportData = null;
            document.getElementById('import-file').value = '';
        }
    }

    // Expose functions to global scope safely
    window.categories = {
        addMappingRow,
        removeMappingRow,
        confirmSaveMappings,
        clearEdits,
        sortTable,
        exportCategories,
        handleImportFile,
        confirmImport
    };
    
    // Also expose key functions globally for onclick handlers
    window.showExportModal = showExportModal;
    window.exportCategoriesWithOptions = exportCategoriesWithOptions;
    window.exportCategories = exportCategories;
    window.handleImportFile = handleImportFile;
    window.confirmImport = confirmImport;
    
})();
