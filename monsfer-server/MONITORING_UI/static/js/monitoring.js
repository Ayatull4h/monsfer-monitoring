/**
 * Monitoring Page JavaScript
 * Dynamic data loading and site overview
 */

(function() {
  'use strict';

  // Configuration
  const CONFIG = {
    API_ENDPOINTS: {
      health: '/api/system/health'
    },
    REFRESH_INTERVAL: 30000 // 30 seconds
  };

  // State
  let monitoringState = {
    sites: {},
    lastUpdate: null,
    refreshTimer: null,
    currentSite: 'plamongan indah',
    siteNames: []
  };

  // Initialize
  async function initMonitoring() {
    console.log('Initializing Monitoring Page...');
    await loadUserSites();
    await loadSiteData();
    startAutoRefresh();
    setupEventListeners();
  }

  async function loadUserSites() {
    try {
      const resp = await fetch('/api/user/sites');
      const data = await resp.json();
      const sites = Array.isArray(data.sites) ? data.sites : [];
      monitoringState.siteNames = sites.map(s => s.site_name).filter(Boolean);
      if (monitoringState.siteNames.length > 0) {
        monitoringState.currentSite = monitoringState.siteNames[0];
      }
    } catch (e) {
      monitoringState.siteNames = ['plamongan indah'];
    }
  }

  // Load site data
  async function loadSiteData() {
    try {
      console.log('Loading monitoring data...');
      
      // Fetch data for all sites
      const sitesData = {};
      const targetSites = (monitoringState.siteNames && monitoringState.siteNames.length)
        ? monitoringState.siteNames
        : ['plamongan indah'];
      for (const site of targetSites) {
        try {
          const response = await fetch(`${CONFIG.API_ENDPOINTS.health}?site=${encodeURIComponent(site)}`);
          if (response.ok) {
            const data = await response.json();
            sitesData[site] = data;
          } else {
            sitesData[site] = createOfflineSiteData(site);
          }
        } catch (error) {
          console.error(`Error fetching data for site ${site}:`, error);
          sitesData[site] = createOfflineSiteData(site);
        }
      }
      
      monitoringState.sites = sitesData;
      monitoringState.lastUpdate = new Date();
      
      // Update UI (overview removed)
      updateDataTable();
      updateLastUpdateTime();
      
    } catch (error) {
      console.error('Error loading monitoring data:', error);
      showError('Failed to load monitoring data');
    }
  }

  // Create offline site data
  function createOfflineSiteData(siteName) {
    return {
      site: siteName,
      deviceStatus: 'OFFLINE',
      cpuUtil: 0,
      cpuTemp: 0,
      freeStorage: 0,
      totalStorage: 0,
      freeRAM: 0,
      totalRAM: 0,
      lastUpdate: new Date().toISOString(),
      source: 'offline'
    };
  }

  // Update site overview removed
  
  // Update quick statistics
  function updateQuickStats() {
    const sites = Object.values(monitoringState.sites);
    const totalSites = sites.length;
    const onlineSites = sites.filter(site => site.deviceStatus === 'ONLINE').length;
    const offlineSites = totalSites - onlineSites;
    
    // Calculate average CPU temp
    const cpuTemps = sites.filter(site => site.cpuTemp > 0).map(site => site.cpuTemp);
    const avgCpuTemp = cpuTemps.length > 0 ? 
      (cpuTemps.reduce((sum, temp) => sum + temp, 0) / cpuTemps.length).toFixed(1) : 0;
    
    // Update UI
    document.getElementById('totalSites').textContent = totalSites;
    document.getElementById('onlineSites').textContent = onlineSites;
    document.getElementById('offlineSites').textContent = offlineSites;
    document.getElementById('avgCpuTemp').textContent = `${avgCpuTemp}°C`;
  }

  // Site overview card removed

  // Update data table
  function updateDataTable() {
    const tbody = document.getElementById('monitoringTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    const sites = Object.entries(monitoringState.sites);
    if (sites.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="8" class="text-center text-muted">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">No data available</p>
          </td>
        </tr>
      `;
      return;
    }
    
    sites.forEach(([siteName, siteData]) => {
      const row = document.createElement('tr');
      const lastUpdate = siteData.lastUpdate || 'Unknown';
      const cpuTemp = siteData.cpuTemp != null ? `${siteData.cpuTemp.toFixed(1)}°C` : '-';
      const cpuUsage = siteData.cpuUtil != null ? `${siteData.cpuUtil.toFixed(1)}%` : '-';
      const memory = siteData.totalRAM && siteData.freeRAM ? 
        `${((siteData.totalRAM - siteData.freeRAM) / siteData.totalRAM * 100).toFixed(1)}%` : '-';
      const storage = siteData.totalStorage && siteData.freeStorage ? 
        `${((siteData.totalStorage - siteData.freeStorage) / siteData.totalStorage * 100).toFixed(1)}%` : '-';
      const status = siteData.deviceStatus || 'UNKNOWN';
      const statusBadge = status === 'ONLINE' ? 
        '<span class="badge bg-success">ONLINE</span>' : 
        '<span class="badge bg-danger">OFFLINE</span>';
      
      row.innerHTML = `
        <td><small>${formatDateTime(lastUpdate)}</small></td>
        <td><strong>${formatSiteName(siteName)}</strong></td>
        <td><span class="badge bg-warning text-dark">${cpuTemp}</span></td>
        <td><span class="badge bg-primary">${cpuUsage}</span></td>
        <td><span class="badge bg-info">${memory}</span></td>
        <td><span class="badge bg-secondary">${storage}</span></td>
        <td>${statusBadge}</td>
        <td>
          <div class="btn-group btn-group-sm">
            <button class="btn btn-outline-primary" onclick="viewSiteDetails('${siteName}')" title="View Details">
              <i class="bi bi-eye"></i>
            </button>
            <button class="btn btn-outline-success" onclick="viewSiteGraph('${siteName}')" title="View Graph">
              <i class="bi bi-graph-up"></i>
            </button>
          </div>
        </td>
      `;
      
      tbody.appendChild(row);
    });
    
    // Add table search functionality
    setupTableSearch();
  }
  
  // Setup table search
  function setupTableSearch() {
    const searchInput = document.getElementById('tableSearch');
    if (searchInput) {
      searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const rows = document.querySelectorAll('#monitoringTableBody tr');
        
        rows.forEach(row => {
          const text = row.textContent.toLowerCase();
          row.style.display = text.includes(searchTerm) ? '' : 'none';
        });
      });
    }
  }

  // Setup event listeners
  function setupEventListeners() {
    // Site select dropdown
    const siteSelect = document.getElementById('siteSelect');
    if (siteSelect) {
      siteSelect.addEventListener('change', function() {
        monitoringState.currentSite = this.value;
        loadSiteData();
      });
    }
    
    // Make site cards clickable to go to system info
    const siteCards = document.querySelectorAll('.site-card');
    siteCards.forEach(card => {
      card.addEventListener('click', function() {
        const siteName = this.dataset.site;
        if (siteName) {
          window.location.href = `/system_info?site=${encodeURIComponent(siteName)}`;
        }
      });
    });
    
    // Load data button
    const loadButton = document.querySelector('button[onclick="loadMonitoringData()"]');
    if (loadButton) {
      loadButton.addEventListener('click', loadSiteData);
    }
    
    // Refresh button
    const refreshButton = document.querySelector('button[onclick="refreshData()"]');
    if (refreshButton) {
      refreshButton.addEventListener('click', loadSiteData);
    }
  }

  // Auto refresh
  function startAutoRefresh() {
    if (monitoringState.refreshTimer) {
      clearInterval(monitoringState.refreshTimer);
    }
    
    monitoringState.refreshTimer = setInterval(() => {
      console.log('Auto-refreshing monitoring data...');
      loadSiteData();
    }, CONFIG.REFRESH_INTERVAL);
  }

  // Utility functions
  function formatSiteName(siteName) {
    return siteName.replace(/-/g, ' ').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  function formatDateTime(timestamp) {
    if (!timestamp || timestamp === 'Unknown') return 'Unknown';
    try {
      const date = new Date(timestamp);
      return date.toLocaleString('id-ID');
    } catch {
      return timestamp;
    }
  }

  function updateLastUpdateTime() {
    const element = document.getElementById('last-update-display');
    if (element && monitoringState.lastUpdate) {
      element.textContent = `Last Update: ${monitoringState.lastUpdate.toLocaleString('id-ID')}`;
    }
  }

  function showError(message) {
    const container = document.getElementById('monitoringTableBody');
    if (container) {
      container.innerHTML = `
        <tr>
          <td colspan="6" class="text-center text-danger">
            <i class="bi bi-exclamation-triangle me-2"></i>${message}
          </td>
        </tr>
      `;
    }
  }

  // Cleanup
  function cleanup() {
    if (monitoringState.refreshTimer) {
      clearInterval(monitoringState.refreshTimer);
    }
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMonitoring);
  } else {
    initMonitoring();
  }

  // Cleanup on unload
  window.addEventListener('beforeunload', cleanup);

  // View site details
  function viewSiteDetails(siteName) {
    window.location.href = `/system_info?site=${encodeURIComponent(siteName)}`;
  }
  
  // View site graph
  function viewSiteGraph(siteName) {
    console.log(`viewSiteGraph called for: ${siteName}`);
    
    // 1. Store selection in session storage for persistence
    sessionStorage.setItem('currentSiteName', siteName);
    
    // 2. Dispatch event for Vue app to pick up if running
    window.dispatchEvent(new CustomEvent('external-site-selected', { 
        detail: { siteName: siteName } 
    }));

    // 3. Update global state
    monitoringState.currentSite = siteName;
    
    // 4. Redirect if not on monitoring page
    if (window.location.pathname !== '/monitoring') {
        window.location.href = '/monitoring';
    } else {
        // If already on monitoring page, the event above should trigger update.
        // But if Vue isn't ready or listening, we might need to force reload or rely on app.js logic.
        // We can also try to find the Vue instance if exposed, but event is cleaner.
    }
  }
  
  // Toggle chart type
  function toggleChartType(chartType) {
    console.log(`Chart type changed to: ${chartType}`);
    // This function can be extended to actually change the chart type
    // For now, it's a placeholder for future chart implementation
  }
  
  // Export data function
  function exportData() {
    const data = Object.entries(monitoringState.sites).map(([siteName, siteData]) => ({
      Site: siteName,
      Status: siteData.deviceStatus,
      'CPU Temp (°C)': siteData.cpuTemp || 0,
      'CPU Usage (%)': siteData.cpuUtil || 0,
      'Memory Used (%)': siteData.totalRAM ? ((siteData.totalRAM - siteData.freeRAM) / siteData.totalRAM * 100).toFixed(1) : 0,
      'Storage Used (%)': siteData.totalStorage ? ((siteData.totalStorage - siteData.freeStorage) / siteData.totalStorage * 100).toFixed(1) : 0,
      'Last Update': siteData.lastUpdate || 'Unknown'
    }));
    
    const csv = convertToCSV(data);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `monitoring_data_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }
  
  // Export table data
  function exportTableData() {
    exportData(); // Use the same export function
  }
  
  // Convert to CSV helper
  function convertToCSV(data) {
    const headers = Object.keys(data[0]);
    const csvContent = [
      headers.join(','),
      ...data.map(row => headers.map(header => `"${row[header] || ''}"`).join(','))
    ].join('\n');
    return csvContent;
  }
  
  // Load monitoring data (new function for chart data)
  function loadMonitoringData() {
    console.log('Loading monitoring chart data...');
    // This function can be extended to load specific chart data
    loadSiteData(); // For now, refresh the site data
  }
  
  // Expose functions globally
  window.monitoring = {
    refresh: loadSiteData,
    getState: () => monitoringState,
    viewSiteDetails,
    viewSiteGraph,
    toggleChartType,
    exportData,
    exportTableData,
    loadMonitoringData
  };

})();
