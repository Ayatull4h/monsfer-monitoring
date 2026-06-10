// Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts
    initializeCharts();
    
    // Initialize data tables
    initializeDataTables();
    
    // Load real-time data
    loadRealTimeData();
    
    // Set up auto-refresh
    setInterval(loadRealTimeData, 30000); // Refresh every 30 seconds
});

function initializeCharts() {
    // Chart initialization code
    const ctx = document.getElementById('uptChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'UPT Status',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

function initializeDataTables() {
    // DataTable initialization
    $('.data-table').DataTable({
        responsive: true,
        language: {
            search: "Search:",
            lengthMenu: "Show _MENU_ entries",
            info: "Showing _START_ to _END_ of _TOTAL_ entries",
            infoEmpty: "Showing 0 to 0 of 0 entries",
            infoFiltered: "(filtered from _MAX_ total entries)"
        }
    });
}

function loadRealTimeData() {
    // Fetch real-time data from API
    fetch('/api/upts')
        .then(response => response.json())
        .then(data => {
            updateDashboardStats(data);
            updateCharts(data);
            updateTables(data);
        })
        .catch(error => {
            console.error('Error loading real-time data:', error);
        });
}

function updateDashboardStats(data) {
    // Update statistics cards
    document.getElementById('totalUPTs').textContent = data.total_upts || 0;
    document.getElementById('activeDevices').textContent = data.active_devices || 0;
    document.getElementById('totalSites').textContent = data.total_sites || 0;
}

function updateCharts(data) {
    // Update chart data
    const chart = Chart.getChart('uptChart');
    if (chart) {
        chart.data.labels = data.timestamps || [];
        chart.data.datasets[0].data = data.values || [];
        chart.update();
    }
}

function updateTables(data) {
    // Update table data
    const table = $('.data-table').DataTable();
    if (table) {
        table.clear();
        table.rows.add(data.table_data || []);
        table.draw();
    }
} 