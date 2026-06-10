// Compatibility globals for System Info page
// Purpose: Prevent ReferenceError when the main #app Vue instance renders
//          the System Info template before the dedicated #sysinfo-app Vue
//          instance is mounted. These safe defaults ensure expressions like
//          `deviceStatus`, `donutStyle(...)`, etc. exist in the global scope.
//
// This file defines harmless fallbacks. The real values will be provided by
// the System Info Vue instance (static/js/system_info.js) once it mounts.

(function(){
  // Only define if not already present to avoid clobbering real data
  var g = (typeof window !== 'undefined') ? window : this;

  // Data fallbacks
  if (typeof g.deviceStatus === 'undefined') g.deviceStatus = '-';
  if (typeof g.lastUpdate === 'undefined') g.lastUpdate = '-';
  if (typeof g.uiVersion === 'undefined') g.uiVersion = '-';
  if (typeof g.dbStatus === 'undefined') g.dbStatus = '-';

  if (typeof g.cpuUtil === 'undefined') g.cpuUtil = null;
  if (typeof g.cpuTemp === 'undefined') g.cpuTemp = null;
  if (typeof g.freeStorage === 'undefined') g.freeStorage = null;
  if (typeof g.totalStorage === 'undefined') g.totalStorage = null;
  if (typeof g.freeRAM === 'undefined') g.freeRAM = null;
  if (typeof g.totalRAM === 'undefined') g.totalRAM = null;
  if (typeof g.storageUsedGB === 'undefined') g.storageUsedGB = null;
  if (typeof g.storageUsedPct === 'undefined') g.storageUsedPct = null;
  if (typeof g.memoryUsedMB === 'undefined') g.memoryUsedMB = null;
  if (typeof g.memoryUsedPct === 'undefined') g.memoryUsedPct = null;

  // Method fallbacks
  if (typeof g.donutStyle === 'undefined') {
    g.donutStyle = function(percentage, color){
      // Provide a minimal valid style object so the template can render
      var p = Number(percentage);
      if (!isFinite(p)) p = 0;
      var bgColor = '#e5e7eb';
      return {
        background: 'conic-gradient(' + (color || '#3b82f6') + ' 0% ' + p + '%, ' + bgColor + ' ' + p + '% 100%)',
        WebkitMask: 'radial-gradient(farthest-side, #0000 calc(70% - 12px), #000 calc(70% - 6px))',
        mask: 'radial-gradient(farthest-side, #0000 calc(70% - 12px), #000 calc(70% - 6px))',
        borderRadius: '50%',
        width: '130px',
        height: '130px',
        position: 'relative'
      };
    };
  }

  if (typeof g.cpuTempToPct === 'undefined') {
    g.cpuTempToPct = function(temp){
      var t = Number(temp);
      if (!isFinite(t)) return 0;
      return Math.max(0, Math.min(100, t));
    };
  }

  if (typeof g.formatPercent === 'undefined') {
    g.formatPercent = function(v){
      var n = Number(v);
      return isFinite(n) ? (n.toFixed(1) + '%') : '-';
    };
  }

  if (typeof g.formatTemp === 'undefined') {
    g.formatTemp = function(v){
      var n = Number(v);
      return isFinite(n) ? (n.toFixed(1) + ' °C') : '-';
    };
  }

  if (typeof g.formatGB === 'undefined') {
    g.formatGB = function(v){
      var n = Number(v);
      return isFinite(n) ? (n.toFixed(2) + ' GB') : '0 GB';
    };
  }

  if (typeof g.formatMB === 'undefined') {
    g.formatMB = function(v){
      var n = Number(v);
      return isFinite(n) ? (n.toFixed(0) + ' MB') : '0 MB';
    };
  }
})();
