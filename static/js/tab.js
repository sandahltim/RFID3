function showLoading(catKey) {
    const loading = document.getElementById(`loading-${catKey}`);
    if (loading) loading.style.display = 'block';
}

function sortTable(column, tableId) {
    // Placeholder for sorting logic
    console.log(`Sorting ${tableId} by ${column}`);
}

function printTable(level, id) {
    // Placeholder for printing logic
    console.log(`Printing ${level} with ID ${id}`);
}

// Debounced refresh
let isRefreshing = false;
function refreshTable(tabNum) {
    if (isRefreshing) return;
    isRefreshing = true;
    htmx.trigger(`#tab-${tabNum}`, 'htmx:load');
    setTimeout(() => { isRefreshing = false; }, 1000);
}

// Initialize refresh
document.addEventListener('DOMContentLoaded', () => {
    const tabNum = document.querySelector('h1').textContent.match(/\d+/)[0];
    setInterval(() => refreshTable(tabNum), 30000);
});