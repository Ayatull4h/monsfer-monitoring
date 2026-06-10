// System Info UI - Direct DOM Manipulation Version
// This version bypasses Vue conflicts by using direct DOM manipulation

console.log('=== SYSTEM INFO JS LOADED (DOM MANIPULATION) ===', new Date().toLocaleString());

// System Info data
let systemData = {
  deviceStatus: '-',
  lastUpdate: '-',
  uiVersion: '1.1.2',
  dbStatus: '-',
  currentSite: 'plamongan indah',
  // health metrics
  cpuUtil: null,
  cpuTemp: null,
  freeStorage: null,
  totalStorage: null,
  freeRAM: null,
  totalRAM: null,
  refreshInterval: null,
  anomaliesInterval: null
};

// Populate site selector from /api/user/sites
async function populateSiteSelector() {
  const sel = document.getElementById('site-selector');
  if (!sel) return;
  try {
    const resp = await fetch('/api/user/sites', { credentials: 'same-origin' });
    const data = await resp.json();
    const sites = Array.isArray(data.sites) ? data.sites : [];
    sel.innerHTML = '';
    if (!sites.length) {
      const opt = document.createElement('option');
      opt.value = 'plamongan indah';
      opt.textContent = 'Plamongan Indah';
      sel.appendChild(opt);
      systemData.currentSite = 'plamongan indah';
      const currentSiteElement = document.getElementById('current-site');
      if (currentSiteElement) currentSiteElement.textContent = systemData.currentSite;
      return;
    }
    sites.forEach(s => {
      const name = s.site_name || '';
      const label = (s.display_name || name || '').toString();
      const opt = document.createElement('option');
      opt.value = name;
      opt.textContent = label;
      sel.appendChild(opt);
    });
    if (!systemData.currentSite || !sites.find(x => x.site_name === systemData.currentSite)) {
      systemData.currentSite = sites[0].site_name;
    }
    sel.value = systemData.currentSite;
    const currentSiteElement = document.getElementById('current-site');
    if (currentSiteElement) currentSiteElement.textContent = systemData.currentSite;
  } catch (e) {
    sel.innerHTML = '';
    const opt = document.createElement('option');
    opt.value = 'plamongan indah';
    opt.textContent = 'Plamongan Indah';
    sel.appendChild(opt);
    systemData.currentSite = 'plamongan indah';
    const currentSiteElement = document.getElementById('current-site');
    if (currentSiteElement) currentSiteElement.textContent = systemData.currentSite;
  }
}

// Utility functions
function formatPercent(v) { 
  return v == null ? '-' : `${v.toFixed(1)}%`; 
}

function formatTemp(v) { 
  return v == null ? '-' : `${v.toFixed(1)} °C`; 
}

function formatGB(v) { 
  return v == null ? '-' : `${v.toFixed(1)} GB`; 
}

function formatMB(v) { 
  return v == null ? '-' : `${v.toFixed(0)} MB`; 
}

function storageUsedGB() {
  const free = systemData.freeStorage;
  const total = systemData.totalStorage;
  if (free == null || total == null || total <= 0) return null;
  return Math.max(0, total - free);
}

function storageUsedPct() {
  const used = storageUsedGB();
  const total = systemData.totalStorage;
  if (used == null || total == null || total <= 0) return null;
  return (used / total) * 100;
}

function memoryUsedMB() {
  const free = systemData.freeRAM;
  const total = systemData.totalRAM;
  if (free == null || total == null || total <= 0) return null;
  return Math.max(0, total - free);
}

function memoryUsedPct() {
  const used = memoryUsedMB();
  const total = systemData.totalRAM;
  if (used == null || total == null || total <= 0) return null;
  return (used / total) * 100;
}

function cpuTempToPct(temp) {
  if (temp == null) return null;
  // Convert temperature to percentage (0-100°C range)
  return Math.max(0, Math.min(100, (temp / 100) * 100));
}

function donutStyle(percentage, color) {
  if (percentage == null || isNaN(percentage)) percentage = 0;
  const p = Math.max(0, Math.min(100, percentage));
  const bgColor = '#e5e7eb';
  return {
    background: `conic-gradient(${color} 0% ${p}%, ${bgColor} ${p}% 100%)`,
    WebkitMask: 'radial-gradient(farthest-side, #0000 calc(70% - 12px), #000 calc(70% - 6px))',
    mask: 'radial-gradient(farthest-side, #0000 calc(70% - 12px), #000 calc(70% - 6px))',
    borderRadius: '50%',
    width: '130px',
    height: '130px',
    position: 'relative'
  };
}

// DOM Update functions
function updateSystemInfoDisplay() {
  console.log('Updating System Info display with data:', systemData);
  
  // Update header info
  const siteElement = document.getElementById('current-site');
  if (siteElement) siteElement.textContent = systemData.currentSite || 'plamongan indah';
  
  const lastUpdateElement = document.getElementById('last-update-time');
  if (lastUpdateElement) lastUpdateElement.textContent = systemData.lastUpdate || '-';
  
  // Update System Information cards
  const deviceStatusElement = document.getElementById('device-status');
  if (deviceStatusElement) {
    deviceStatusElement.textContent = systemData.deviceStatus || '-';
    deviceStatusElement.className = 'badge ' + (systemData.deviceStatus === 'ONLINE' ? 'success' : 'error');
  }
  
  const infoLastUpdateElement = document.getElementById('info-last-update');
  if (infoLastUpdateElement) {
    infoLastUpdateElement.textContent = systemData.lastUpdate || '-';
  }
  
  const uiVersionElement = document.getElementById('ui-version');
  if (uiVersionElement) {
    uiVersionElement.textContent = systemData.uiVersion || '-';
  }
  
  const dbStatusElement = document.getElementById('db-status');
  if (dbStatusElement) {
    const dbStatus = (systemData.deviceStatus === 'ONLINE' ? 'CONNECTED' : (systemData.deviceStatus === 'OFFLINE' ? 'DISCONNECTED' : '-'));
    dbStatusElement.textContent = dbStatus;
    dbStatusElement.className = 'badge ' + (dbStatus === 'CONNECTED' ? 'success' : 'error');
  }
  
  // Update Health Monitor charts
  updateHealthCharts();
}

function updateAnomaliesDisplay(items) {
  const listEl = document.getElementById('anomalies-list');
  const emptyEl = document.getElementById('anomalies-empty');
  const countEl = document.getElementById('anomalies-count');
  if (!listEl || !emptyEl || !countEl) return;
  listEl.innerHTML = '';
  const active = items.filter(a => !a.dismissed);
  countEl.textContent = active.length;
  if (active.length === 0) {
    emptyEl.style.display = 'block';
    return;
  }
  emptyEl.style.display = 'none';
  active.forEach(a => {
    const li = document.createElement('li');
    li.className = 'list-group-item d-flex justify-content-between align-items-center';
    li.textContent = a.message;
    const btn = document.createElement('button');
    btn.className = 'btn btn-sm btn-outline-secondary';
    btn.textContent = 'Dismiss';
    btn.addEventListener('click', () => {
      a.dismissed = true;
      updateAnomaliesDisplay(items);
    });
    li.appendChild(btn);
    listEl.appendChild(li);
  });
}

function updateHealthCharts() {
  // CPU Utilization
  const cpuUtilPct = systemData.cpuUtil;
  const cpuCenterElement = document.getElementById('cpu-center');
  if (cpuCenterElement) {
    cpuCenterElement.textContent = cpuUtilPct == null ? '-' : (cpuUtilPct.toFixed(0) + '%');
  }
  const cpuDonutElement = document.getElementById('cpu-donut');
  if (cpuDonutElement) {
    Object.assign(cpuDonutElement.style, donutStyle(cpuUtilPct, 'var(--accent)'));
  }
  
  // Update CPU legend
  const cpuLegendUsed = document.getElementById('cpu-legend-used');
  if (cpuLegendUsed) {
    cpuLegendUsed.textContent = `Used (${formatPercent(cpuUtilPct)})`;
  }
  const cpuLegendAvailable = document.getElementById('cpu-legend-available');
  if (cpuLegendAvailable) {
    cpuLegendAvailable.textContent = `Available (${cpuUtilPct != null ? (100 - cpuUtilPct).toFixed(1) + '%' : '-'})`;
  }
  
  // CPU Temperature
  const cpuTempPct = cpuTempToPct(systemData.cpuTemp);
  const tempCenterElement = document.getElementById('temp-center');
  if (tempCenterElement) {
    tempCenterElement.textContent = systemData.cpuTemp == null ? '-' : (systemData.cpuTemp.toFixed(0) + '°C');
  }
  const tempDonutElement = document.getElementById('temp-donut');
  if (tempDonutElement) {
    Object.assign(tempDonutElement.style, donutStyle(cpuTempPct, '#f59e0b'));
  }
  
  // Update temperature legend
  const tempLegendCurrent = document.getElementById('temp-legend-current');
  if (tempLegendCurrent) {
    tempLegendCurrent.textContent = `Current (${formatTemp(systemData.cpuTemp)})`;
  }
  
  // Storage Usage
  const storagePct = storageUsedPct();
  const storageCenterElement = document.getElementById('storage-center');
  if (storageCenterElement) {
    storageCenterElement.textContent = storagePct == null ? '-' : (storagePct.toFixed(0) + '%');
  }
  const storageDonutElement = document.getElementById('storage-donut');
  if (storageDonutElement) {
    Object.assign(storageDonutElement.style, donutStyle(storagePct, '#10b981'));
  }
  
  // Update storage legend
  const storageLegendUsed = document.getElementById('storage-legend-used');
  if (storageLegendUsed) {
    storageLegendUsed.textContent = `Used (${formatGB(storageUsedGB())})`;
  }
  const storageLegendFree = document.getElementById('storage-legend-free');
  if (storageLegendFree) {
    storageLegendFree.textContent = `Free (${formatGB(systemData.freeStorage)})`;
  }
  
  // Memory Usage
  const memoryPct = memoryUsedPct();
  const memoryCenterElement = document.getElementById('memory-center');
  if (memoryCenterElement) {
    memoryCenterElement.textContent = memoryPct == null ? '-' : (memoryPct.toFixed(0) + '%');
  }
  const memoryDonutElement = document.getElementById('memory-donut');
  if (memoryDonutElement) {
    Object.assign(memoryDonutElement.style, donutStyle(memoryPct, '#8b5cf6'));
  }
  
  // Update memory legend
  const memoryLegendUsed = document.getElementById('memory-legend-used');
  if (memoryLegendUsed) {
    memoryLegendUsed.textContent = `Used (${formatMB(memoryUsedMB())})`;
  }
  const memoryLegendFree = document.getElementById('memory-legend-free');
  if (memoryLegendFree) {
    memoryLegendFree.textContent = `Free (${formatMB(systemData.freeRAM)})`;
  }
}

// Data fetching functions
async function fetchSystemHealth() {
  try {
    const site = systemData.currentSite || 'plamongan indah';
    console.log(`Fetching system health data for site: ${site}...`);
    // Use correct endpoint /api/system/metrics and pass site parameter
    const apiUrl = `/api/system/metrics?site=${encodeURIComponent(site)}`;
    console.log(`API URL: ${apiUrl}`);
    let response = await fetch(apiUrl);
    console.log(`Response status: ${response.status}`);
    let data;
    if (!response.ok) {
      console.warn('Primary health endpoint failed');
      throw new Error(`HTTP ${response.status}`);
    } else {
      const json = await response.json();
      data = json.data || json;
    }
    console.log('Received health data:', data);
    
    // Update system data
    systemData = { ...systemData, ...data };
    systemData.lastUpdate = data.lastUpdate || new Date().toLocaleString('id-ID');
    
    // Update display
    updateSystemInfoDisplay();
  } catch (err) {
    console.error('Error fetching system health:', err);
    systemData.deviceStatus = 'ERROR';
    systemData.lastUpdate = 'Error: ' + err.message;
    updateSystemInfoDisplay();
  }
}

async function refreshAnomalies() {
  try {
    const resp = await fetch('/api/system/dashboard', { credentials: 'same-origin' });
    if (!resp.ok) return;
    const data = await resp.json();
    const sites = data.sites || {};
    const siteName = systemData.currentSite || 'plamongan indah';
    const s = sites[siteName] || {};
    const now = Date.now();
    const lastUpdate = s.lastUpdate ? new Date(s.lastUpdate).getTime() : now;
    const cpuTemp = typeof s.cpuTemp === 'number' ? s.cpuTemp : null;
    const freeStorage = typeof s.freeStorage === 'number' ? s.freeStorage : null;
    const totalStorage = typeof s.totalStorage === 'number' ? s.totalStorage : null;
    const storageUsedPct = totalStorage && totalStorage > 0 ? Math.max(0, Math.min(100, (1 - (freeStorage / totalStorage)) * 100)) : null;
    const deviceStatus = String(s.deviceStatus || '').toUpperCase();
    const anomalies = [];
    if (deviceStatus === 'OFFLINE' || (now - lastUpdate) >= (60 * 60 * 1000)) {
      anomalies.push({ id: `offline_${siteName}`, message: `OFFLINE ≥60m (${siteName})`, dismissed: false });
    }
    if (cpuTemp !== null && cpuTemp > 55) {
      anomalies.push({ id: `temp_${siteName}`, message: `cpuTemp ${cpuTemp.toFixed(1)}°C > 55 (${siteName})`, dismissed: false });
    }
    if (storageUsedPct !== null && storageUsedPct > 95) {
      anomalies.push({ id: `storage_${siteName}`, message: `Storage ${storageUsedPct.toFixed(1)}% > 95% (${siteName})`, dismissed: false });
    }
    updateAnomaliesDisplay(anomalies);
  } catch (e) {
    // silent
  }
}

async function prefillFromLatestLog() {
  try {
    console.log('Prefilling from latest log...');
    const response = await fetch('/api/system/health-from-logs');
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    console.log('Prefill data:', data);
    
    systemData = { ...systemData, ...data };
    systemData.lastUpdate = data.lastUpdate || new Date().toLocaleString('id-ID');
    
    updateSystemInfoDisplay();
  } catch (err) {
    console.error('Error prefilling from log:', err);
  }
}

// Site change handler
function handleSiteChange() {
  const siteSelector = document.getElementById('site-selector');
  if (siteSelector) {
    siteSelector.addEventListener('change', function() {
      const selectedSite = this.value;
      console.log('Site changed to:', selectedSite);
      systemData.currentSite = selectedSite;
      try {
        fetch('/api/user/select-site', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ site_name: selectedSite })
        }).catch(() => {});
      } catch (e) {}
      
      // Update current site display
      const currentSiteElement = document.getElementById('current-site');
      if (currentSiteElement) {
        currentSiteElement.textContent = selectedSite;
      }
      
      // Fetch new data for the selected site
      fetchSystemHealth();
    });
  }
}

function setupMetricsDownload() {
  const btn = document.getElementById('metrics-download');
  if (!btn) return;

  btn.addEventListener('click', function() {
    const daysEl = document.getElementById('metrics-days');
    const fmtEl = document.getElementById('metrics-format');
    const daysRaw = daysEl ? String(daysEl.value || '').trim() : '1';
    const fmt = fmtEl ? String(fmtEl.value || 'csv').trim().toLowerCase() : 'csv';

    let days = parseInt(daysRaw, 10);
    if (!Number.isFinite(days) || days < 1) days = 1;
    if (days > 31) days = 31;

    const site = systemData.currentSite || 'plamongan indah';
    const url = `/api/system/metrics/download?site=${encodeURIComponent(site)}&days=${encodeURIComponent(days)}&format=${encodeURIComponent(fmt)}`;
    window.location.href = url;
  });
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  console.log('DOM loaded, initializing System Info...');
  
  // Populate selector then set up site change handler
  populateSiteSelector().then(() => {
    handleSiteChange();
  }).catch(() => {
    handleSiteChange();
  });
  
  // Initial data load
  prefillFromLatestLog();

  setupMetricsDownload();
  
  // Set up auto-refresh
  if (systemData.refreshInterval) {
    clearInterval(systemData.refreshInterval);
  }
  systemData.refreshInterval = setInterval(fetchSystemHealth, 30000); // 30 seconds
  
  console.log('System Info initialized successfully');
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
  if (systemData.refreshInterval) {
    clearInterval(systemData.refreshInterval);
  }
  if (systemData.anomaliesInterval) {
    clearInterval(systemData.anomaliesInterval);
  }
});
