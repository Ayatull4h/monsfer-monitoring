// Scanner State
let scannerState = {
    isScanning: false,
    autoRefresh: true,
    refreshInterval: 30,
    refreshTimer: null,
    networks: [],
    violations: []
};

// Dummy data for testing
const dummyNetworks = [
    {
        ssid: "Office_WiFi",
        bssid: "00:11:22:33:44:55",
        channel: 1,
        frequency: 2.412,
        signalStrength: -45,
        security: "WPA2",
        lastSeen: "Just now",
        hidden: false
    },
    {
        ssid: "Guest_Network",
        bssid: "00:11:22:33:44:66",
        channel: 6,
        frequency: 2.437,
        signalStrength: -60,
        security: "Open",
        lastSeen: "1 min ago",
        hidden: false
    },
    {
        ssid: "Hidden_AP",
        bssid: "00:11:22:33:44:77",
        channel: 11,
        frequency: 2.462,
        signalStrength: -70,
        security: "WPA3",
        lastSeen: "2 min ago",
        hidden: true
    },
    {
        ssid: "5G_Network",
        bssid: "00:11:22:33:44:88",
        channel: 36,
        frequency: 5.180,
        signalStrength: -55,
        security: "WPA2",
        lastSeen: "Just now",
        hidden: false
    },
    {
        ssid: "5G_Guest",
        bssid: "00:11:22:33:44:99",
        channel: 149,
        frequency: 5.745,
        signalStrength: -65,
        security: "Open",
        lastSeen: "1 min ago",
        hidden: false
    }
];

// Add dummy data for testing
const dummyViolations = [
    {
        ssid: "Illegal_2.3GHz_AP",
        bssid: "00:11:22:33:44:AA",
        frequency: 2.300,
        channel: 0,
        signalStrength: -65,
        security: "WPA2",
        lastSeen: "2 min ago",
        hidden: false
    },
    {
        ssid: "Unauthorized_2.5GHz",
        bssid: "00:11:22:33:44:BB",
        frequency: 2.500,
        channel: 14,
        signalStrength: -58,
        security: "WPA2",
        lastSeen: "5 min ago",
        hidden: false
    },
    {
        ssid: "OutOfBand_5.9GHz",
        bssid: "00:11:22:33:44:CC",
        frequency: 5.900,
        channel: 180,
        signalStrength: -72,
        security: "WPA2",
        lastSeen: "4 min ago",
        hidden: false
    }
];

// Cookie functions
function setCookie(name, value, days) {
    let expires = "";
    if (days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "") + expires + "; path=/";
}

function getCookie(name) {
    const nameEQ = name + "=";
    const ca = document.cookie.split(';');
    for(let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
}

const toggleBtn = document.getElementById('toggleBtn');

const mainWrapper = document.querySelector('.main-wrapper');

// Add violation list functionality
const indonesiaBands = {
    '2.4': {
        start: 2.412,  // Channel 1
        end: 2.472,    // Channel 13
        step: 0.005    // 5 MHz spacing
    },
    '5.8': {
        start: 5.180,  // Channel 36
        end: 5.825,    // Channel 165
        step: 0.005    // 5 MHz spacing
    }
};

function checkFrequencyViolation(network) {
    const freq = parseFloat(network.frequency);
    const band = freq < 3 ? '2.4' : '5.8';
    const bandInfo = indonesiaBands[band];
    
    return freq < bandInfo.start || freq > bandInfo.end;
}

function updateViolationList(networks) {
    const violationList = document.getElementById('violationList');
    const violationCount = document.getElementById('violationCount');
    const violations = networks.filter(checkFrequencyViolation);
    
    violationCount.textContent = violations.length;
    
    if (violations.length === 0) {
        violationList.innerHTML = `
            <div class="list-group-item text-center text-muted">
                No violations detected
            </div>
        `;
        return;
    }

    violationList.innerHTML = violations.map(network => `
        <div class="list-group-item py-2">
            <div class="d-flex align-items-center">
                <div class="flex-grow-1">
                    <div class="d-flex align-items-center">
                        <i class="bi bi-exclamation-triangle-fill text-danger me-2"></i>
                        <strong>${network.ssid}</strong>
                        <span class="badge bg-danger ms-2">${network.signalStrength} dBm</span>
                    </div>
                    <small class="text-muted">
                        ${network.frequency} GHz • Ch ${network.channel} • ${network.security} • ${network.lastSeen}
                    </small>
                </div>
            </div>
        </div>
    `).join('');
}

// Chart instances
let chart24GHz = null;
let chart58GHz = null;

// Initialize charts
function initCharts() {
    // Initialize 2.4GHz chart
    chart24GHz = echarts.init(document.getElementById('channelChart24'), null, {
        renderer: 'canvas',
        useDirtyRect: true
    });
    
    // Initialize 5.8GHz chart
    chart58GHz = echarts.init(document.getElementById('channelChart58'), null, {
        renderer: 'canvas',
        useDirtyRect: true
    });
    
    // Set initial options
    const chartOptions = {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'shadow'
            }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14']
        },
        yAxis: {
            type: 'value',
            name: 'Signal Strength (dBm)'
        },
        series: [{
            name: 'Channel Usage',
            type: 'bar',
            data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        }]
    };
    
    chart24GHz.setOption(chartOptions);
    chart58GHz.setOption(chartOptions);
    
    // Handle resize
    const resizeObserver = new ResizeObserver(entries => {
        for (let entry of entries) {
            const chart = entry.target.id === 'channelChart24' ? chart24GHz : chart58GHz;
            if (chart) {
                chart.resize();
            }
        }
    });
    
    resizeObserver.observe(document.getElementById('channelChart24'));
    resizeObserver.observe(document.getElementById('channelChart58'));
    
    // Handle window resize
    window.addEventListener('resize', () => {
        if (chart24GHz) chart24GHz.resize();
        if (chart58GHz) chart58GHz.resize();
    });
    
    // Handle sidebar toggle
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            // Wait for sidebar transition to complete
            setTimeout(() => {
                if (chart24GHz) chart24GHz.resize();
                if (chart58GHz) chart58GHz.resize();
            }, 300); // Match this with your CSS transition duration
        });
    }
}

// Update chart data
function updateCharts(networks) {
    if (!chart24GHz || !chart58GHz) return;
    
    // Process 2.4GHz networks
    const channels24GHz = new Array(14).fill(0);
    networks.filter(n => n.frequency < 3000).forEach(network => {
        if (network.channel >= 1 && network.channel <= 14) {
            channels24GHz[network.channel - 1] = Math.max(
                channels24GHz[network.channel - 1],
                network.signalStrength
            );
        }
    });
    
    // Process 5.8GHz networks
    const channels58GHz = new Array(14).fill(0);
    networks.filter(n => n.frequency >= 5000).forEach(network => {
        if (network.channel >= 36 && network.channel <= 165) {
            const idx = Math.floor((network.channel - 36) / 4);
            if (idx >= 0 && idx < 14) {
                channels58GHz[idx] = Math.max(
                    channels58GHz[idx],
                    network.signalStrength
                );
            }
        }
    });
    
    // Update charts
    chart24GHz.setOption({
        series: [{
            data: channels24GHz
        }]
    });
    
    chart58GHz.setOption({
        series: [{
            data: channels58GHz
        }]
    });
}

// Initialize scanner
function initScanner() {
    console.log('Initializing WiFi Scanner...');
    
    // Load saved settings
    const savedSettings = localStorage.getItem('wifiScannerSettings');
    if (savedSettings) {
        const settings = JSON.parse(savedSettings);
        scannerState.autoRefresh = settings.autoRefresh;
        scannerState.refreshInterval = settings.refreshInterval;
        
        // Update UI
        document.getElementById('autoRefresh').checked = scannerState.autoRefresh;
        document.getElementById('refreshInterval').value = scannerState.refreshInterval;
    }
    
    // Initialize charts
    initCharts();
    
    // Load initial data
    loadInitialData();
    
    // Start initial scan if auto-refresh is enabled
    if (scannerState.autoRefresh) {
        startScan();
    }
}

// Load initial data
function loadInitialData() {
    // Trigger initial scan to fetch real data
    startScan();
}

// Start WiFi Scan
function startScan() {
    if (scannerState.isScanning) return;
    
    scannerState.isScanning = true;
    updateScannerStatus(true);
    
    // Start scanning
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    // Get current site from session storage or URL or global state
    let site = 'plamongan indah'; // Default
    try {
        if (window.systemData && window.systemData.currentSite) {
            site = window.systemData.currentSite;
        } else if (sessionStorage.getItem('currentSiteName')) {
            site = sessionStorage.getItem('currentSiteName');
        }
    } catch(e) {}
    
    fetch(`/api/wifi/scan?site=${encodeURIComponent(site)}`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json().catch(error => {
                // If response is not JSON, try to get text for debugging
                return response.text().then(text => {
                    console.error('Non-JSON response:', text);
                    throw new Error('Invalid JSON response from server');
                });
            });
        })
        .then(data => {
            updateNetworkData(data);
            if (scannerState.autoRefresh) {
                scheduleNextScan();
            }
        })
        .catch(error => {
            console.error('Scan error:', error);
            // Do not use dummy data; show empty results
            updateNetworkData({ networks: [], violations: [] });
            if (scannerState.autoRefresh) {
                scheduleNextScan();
            }
        });
}

// Stop WiFi Scan
function stopScan() {
    scannerState.isScanning = false;
    if (scannerState.refreshTimer) {
        clearTimeout(scannerState.refreshTimer);
        scannerState.refreshTimer = null;
    }
    updateScannerStatus(false);
}

// Schedule Next Scan
function scheduleNextScan() {
    if (scannerState.refreshTimer) {
        clearTimeout(scannerState.refreshTimer);
    }
    scannerState.refreshTimer = setTimeout(() => {
        if (scannerState.autoRefresh) {
            startScan();
        }
    }, scannerState.refreshInterval * 1000);
}

// Update Scanner Status
function updateScannerStatus(isActive) {
    const statusBadge = document.getElementById('scannerStatus');
    const startBtn = document.getElementById('startScan');
    const stopBtn = document.getElementById('stopScan');

    if (!statusBadge || !startBtn || !stopBtn) {
        return;
    }
    
    if (isActive) {
        statusBadge.className = 'badge bg-success';
        statusBadge.textContent = 'Active';
        startBtn.disabled = true;
        stopBtn.disabled = false;
    } else {
        statusBadge.className = 'badge bg-danger';
        statusBadge.textContent = 'Inactive';
        startBtn.disabled = false;
        stopBtn.disabled = true;
    }
}

// Update Network Data
function updateNetworkData(data) {
    if (!data || !Array.isArray(data.networks)) {
        data = { networks: [], violations: [] };
    }
    
    scannerState.networks = data.networks;
    scannerState.violations = data.violations;
    
    // Update statistics
    updateStatistics(data);
    
    // Update network list
    updateNetworkList();
    
    // Update violation list
    updateViolationList(data.violations);
    
    // Update charts
    updateCharts(data.networks);
    
    // Update last scan time
    const lastScanTime = document.getElementById('lastScanTime');
    if (lastScanTime) {
        lastScanTime.textContent = 'Last scan: Just now';
    }
}

// Update Statistics
function updateStatistics(data) {
    const stats = {
        total: data.networks.length,
        secure: data.networks.filter(n => n.security !== 'Open').length,
        open: data.networks.filter(n => n.security === 'Open').length,
        avgSignal: calculateAverageSignal(data.networks)
    };
    
    const totalNetworks = document.getElementById('totalNetworks');
    const secureNetworks = document.getElementById('secureNetworks');
    const openNetworks = document.getElementById('openNetworks');
    const avgSignalQuality = document.getElementById('avgSignalQuality');
    if (totalNetworks) totalNetworks.textContent = stats.total;
    if (secureNetworks) secureNetworks.textContent = stats.secure;
    if (openNetworks) openNetworks.textContent = stats.open;
    if (avgSignalQuality) avgSignalQuality.textContent = `${stats.avgSignal}%`;
}

// Calculate Average Signal Quality
function calculateAverageSignal(networks) {
    if (networks.length === 0) return 0;
    
    const totalQuality = networks.reduce((sum, network) => {
        // Convert dBm to percentage (assuming -100 dBm is 0% and -30 dBm is 100%)
        const quality = Math.min(100, Math.max(0, 
            ((network.signalStrength + 100) / 70) * 100
        ));
        return sum + quality;
    }, 0);
    
    return Math.round(totalQuality / networks.length);
}

// Update Network List
function updateNetworkList() {
    const tbody = document.getElementById('networkList');
    const searchWifiInput = document.getElementById('searchWifi');
    if (!searchWifiInput) return; // Prevent null reference error
    const searchTerm = searchWifiInput.value.toLowerCase();
    const showOpen = document.getElementById('showOpenNetworks').checked;
    const showSecure = document.getElementById('showSecureNetworks').checked;
    const showHidden = document.getElementById('showHiddenNetworks').checked;
    
    // Filter networks
    const filteredNetworks = scannerState.networks.filter(network => {
        const matchesSearch = network.ssid.toLowerCase().includes(searchTerm);
        const matchesSecurity = (network.security === 'Open' && showOpen) || 
                               (network.security !== 'Open' && showSecure);
        const matchesHidden = showHidden || !network.hidden;
        return matchesSearch && matchesSecurity && matchesHidden;
    });
    
    // Sort networks
    const sortType = document.querySelector('.sort-active')?.id;
    if (sortType) {
        sortNetworks(filteredNetworks, sortType);
    }
    
    // Update table with enhanced styling
    tbody.innerHTML = filteredNetworks.map(network => `
        <tr class="network-row" data-bssid="${network.bssid}">
            <td>
                <div class="d-flex align-items-center">
                    <div class="network-icon me-2">
                        ${network.hidden ? '<i class="bi bi-eye-slash text-muted"></i>' : 
                          network.security === 'Open' ? '<i class="bi bi-unlock text-warning"></i>' : 
                          '<i class="bi bi-lock text-success"></i>'}
                    </div>
                    <div>
                        <div class="fw-semibold">${network.ssid || 'Hidden Network'}</div>
                        <small class="text-muted">${network.bssid}</small>
                    </div>
                </div>
            </td>
            <td>
                <span class="badge bg-primary">Ch ${network.channel}</span>
                <div><small class="text-muted">${network.frequency} GHz</small></div>
            </td>
            <td>
                <div class="signal-strength-indicator">
                    <div class="signal-bars">
                        ${generateSignalBars(network.signalStrength)}
                    </div>
                    <span class="ms-2">${network.signalStrength} dBm</span>
                </div>
            </td>
            <td>
                <span class="badge ${network.security === 'Open' ? 'bg-warning text-dark' : 'bg-success'}">
                    ${network.security}
                </span>
            </td>
            <td>
                <span class="text-muted">${network.lastSeen}</span>
            </td>
            <td>
                <div class="btn-group btn-group-sm network-actions">
                    <button class="btn btn-outline-primary" onclick="showNetworkDetails('${network.bssid}')" 
                            title="View Details" data-bs-toggle="tooltip">
                        <i class="bi bi-info-circle"></i>
                    </button>
                    <button class="btn btn-outline-success" onclick="connectToNetwork('${network.bssid}')" 
                            title="Connect" data-bs-toggle="tooltip">
                        <i class="bi bi-plug"></i>
                    </button>
                    <button class="btn btn-outline-danger" onclick="reportNetwork('${network.bssid}')" 
                            title="Report" data-bs-toggle="tooltip">
                        <i class="bi bi-flag"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
    
    // Initialize tooltips
    initTooltips();
    
    // Add row hover effects
    addRowHoverEffects();
}

// Generate Signal Bars
function generateSignalBars(signalStrength) {
    const quality = Math.min(100, Math.max(0, ((signalStrength + 100) / 70) * 100));
    const barCount = 4;
    const activeBars = Math.ceil((quality / 100) * barCount);
    
    let bars = '';
    for (let i = 0; i < barCount; i++) {
        const isActive = i < activeBars;
        const className = isActive ? 
            (i < 2 ? 'active danger' : i < 3 ? 'active warning' : 'active') : 
            '';
        bars += `<div class="signal-bar ${className}"></div>`;
    }
    
    return bars;
}

// Show Network Details
function showNetworkDetails(bssid) {
    const network = scannerState.networks.find(n => n.bssid === bssid);
    if (!network) return;
    
    const modal = new bootstrap.Modal(document.getElementById('networkDetailsModal'));
    const content = document.getElementById('networkDetailsContent');
    
    content.innerHTML = `
        <div class="network-details-grid">
            <div class="network-detail-item">
                <label>SSID</label>
                <span>${network.ssid || 'Hidden Network'}</span>
            </div>
            <div class="network-detail-item">
                <label>BSSID</label>
                <span>${network.bssid}</span>
            </div>
            <div class="network-detail-item">
                <label>Channel</label>
                <span>${network.channel}</span>
            </div>
            <div class="network-detail-item">
                <label>Frequency</label>
                <span>${network.frequency} GHz</span>
            </div>
            <div class="network-detail-item">
                <label>Signal Strength</label>
                <span>${network.signalStrength} dBm</span>
            </div>
            <div class="network-detail-item">
                <label>Security</label>
                <span>${network.security}</span>
            </div>
            <div class="network-detail-item">
                <label>Last Seen</label>
                <span>${network.lastSeen}</span>
            </div>
            <div class="network-detail-item">
                <label>First Seen</label>
                <span>${network.firstSeen || 'Unknown'}</span>
            </div>
        </div>
    `;
    
    modal.show();
}

// Report Network
function reportNetwork(bssid) {
    const network = scannerState.networks.find(n => n.bssid === bssid);
    if (!network) return;
    
    if (confirm(`Are you sure you want to report network "${network.ssid || 'Hidden Network'}"?`)) {
        fetch('/api/wifi/report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ bssid })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Network reported successfully');
            } else {
                alert('Failed to report network');
            }
        })
        .catch(error => {
            console.error('Report error:', error);
            alert('Error reporting network');
        });
    }
}

// Export Networks
function exportNetworks() {
    const networks = scannerState.networks.map(n => ({
        SSID: n.ssid || 'Hidden Network',
        BSSID: n.bssid,
        Channel: n.channel,
        Frequency: `${n.frequency} GHz`,
        'Signal Strength': `${n.signalStrength} dBm`,
        Security: n.security,
        'Last Seen': n.lastSeen
    }));
    
    const csv = convertToCSV(networks);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `wifi_networks_${new Date().toISOString().slice(0,10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// Convert to CSV
function convertToCSV(arr) {
    const array = [Object.keys(arr[0])].concat(arr);
    return array.map(row => {
        return Object.values(row).map(value => {
            return `"${value}"`;
        }).join(',');
    }).join('\n');
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    console.log('WiFi Scanner DOM loaded');
    
    // Initialize scanner
    initScanner();
    
    // Scanner controls
    const startScanBtn = document.getElementById('startScan');
    const stopScanBtn = document.getElementById('stopScan');
    
    if (startScanBtn) {
        startScanBtn.addEventListener('click', startScan);
    }
    
    if (stopScanBtn) {
        stopScanBtn.addEventListener('click', stopScan);
    }
    
    // Auto refresh toggle
    const autoRefreshCheckbox = document.getElementById('autoRefresh');
    if (autoRefreshCheckbox) {
        autoRefreshCheckbox.addEventListener('change', (e) => {
            scannerState.autoRefresh = e.target.checked;
            if (scannerState.autoRefresh) {
                startScan();
            } else {
                stopScan();
            }
            saveSettings();
        });
    }
    
    // Refresh interval
    const refreshIntervalInput = document.getElementById('refreshInterval');
    if (refreshIntervalInput) {
        refreshIntervalInput.addEventListener('change', (e) => {
            scannerState.refreshInterval = parseInt(e.target.value);
            if (scannerState.autoRefresh) {
                startScan();
            }
            saveSettings();
        });
    }
    
    // Search
    const searchInput = document.getElementById('searchWifi');
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            updateNetworkList();
        });
    }
    
    // Filter toggles
    document.querySelectorAll('.form-check-input').forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            updateNetworkList();
        });
    });
    
    // Sort buttons
    document.querySelectorAll('[id^="sort"]').forEach(button => {
        button.addEventListener('click', () => {
            document.querySelectorAll('[id^="sort"]').forEach(btn => {
                btn.classList.remove('active', 'sort-active');
            });
            button.classList.add('active', 'sort-active');
            updateNetworkList();
        });
    });
    
    // Export button
    const exportBtn = document.getElementById('exportNetworks');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportNetworks);
    }
    
    // Refresh button
    const refreshBtn = document.getElementById('refreshNetworks');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            startScan();
        });
    }
    
    // Handle sidebar toggle
    initSidebarToggle();
    
    // Initialize tooltips after DOM is loaded
    setTimeout(initTooltips, 100);
    
    console.log('WiFi Scanner initialized successfully');
});

// Save Settings
function saveSettings() {
    const settings = {
        autoRefresh: scannerState.autoRefresh,
        refreshInterval: scannerState.refreshInterval
    };
    localStorage.setItem('wifiScannerSettings', JSON.stringify(settings));
}

// Sort Networks
function sortNetworks(networks, sortType) {
    switch (sortType) {
        case 'sortSignal':
            networks.sort((a, b) => b.signalStrength - a.signalStrength);
            break;
        case 'sortName':
            networks.sort((a, b) => {
                const nameA = (a.ssid || '').toLowerCase();
                const nameB = (b.ssid || '').toLowerCase();
                return nameA.localeCompare(nameB);
            });
            break;
        case 'sortChannel':
            networks.sort((a, b) => a.channel - b.channel);
            break;
        case 'sortSecurity':
            networks.sort((a, b) => a.security.localeCompare(b.security));
            break;
    }
}

// Handle sidebar toggle
function initSidebarToggle() {
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    const mainWrapper = document.querySelector('.main-wrapper');
    
    if (sidebarToggle && mainWrapper) {
        sidebarToggle.addEventListener('click', () => {
            mainWrapper.classList.toggle('sidebar-collapsed');
            mainWrapper.classList.toggle('sidebar-expanded');
            
            // Wait for sidebar transition to complete
            setTimeout(() => {
                if (chart24GHz) chart24GHz.resize();
                if (chart58GHz) chart58GHz.resize();
            }, 300); // Match this with your CSS transition duration
        });
    }
}

// Initialize tooltips
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Add row hover effects
function addRowHoverEffects() {
    const rows = document.querySelectorAll('.network-row');
    rows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.backgroundColor = 'rgba(74, 144, 226, 0.05)';
            this.style.transform = 'scale(1.01)';
            this.style.transition = 'all 0.2s ease';
        });
        
        row.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
            this.style.transform = 'scale(1)';
        });
    });
}

// Connect to network function
function connectToNetwork(bssid) {
    const network = scannerState.networks.find(n => n.bssid === bssid);
    if (!network) return;
    
    if (network.security === 'Open') {
        if (confirm(`Connect to open network "${network.ssid || 'Hidden Network'}"?`)) {
            // Simulate connection
            showConnectionStatus(network.ssid, 'Connecting...');
            setTimeout(() => {
                showConnectionStatus(network.ssid, 'Connected');
            }, 2000);
        }
    } else {
        const password = prompt(`Enter password for "${network.ssid || 'Hidden Network'}" (${network.security}):`);
        if (password) {
            showConnectionStatus(network.ssid, 'Connecting...');
            setTimeout(() => {
                showConnectionStatus(network.ssid, 'Connected');
            }, 3000);
        }
    }
}

// Show connection status
function showConnectionStatus(ssid, status) {
    const statusDiv = document.createElement('div');
    statusDiv.className = 'alert alert-info position-fixed top-0 end-0 m-3';
    statusDiv.style.zIndex = '9999';
    statusDiv.innerHTML = `
        <i class="bi bi-wifi me-2"></i>
        <strong>${ssid}:</strong> ${status}
        <button type="button" class="btn-close ms-2" onclick="this.parentElement.remove()"></button>
    `;
    
    document.body.appendChild(statusDiv);
    
    if (status === 'Connected') {
        setTimeout(() => {
            statusDiv.remove();
        }, 3000);
    }
}
