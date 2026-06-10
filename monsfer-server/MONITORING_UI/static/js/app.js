// Debounce utility
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func.apply(this, args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Vue.js application
new Vue({
    el: '#app',
    mixins: [window.pageMixin || {}],
    data: {
        isMonitoringPage: window.location.pathname === '/monitoring',
        hasSidebar: true,
        spectrumData: [],
        alerts: [],
        devices: [],
        chart: null,
        isWaterfallLoading: false,
        syncingZoom: false,
        enableZoomSync: false,
        _lastWaterfallUpdate: 0,
        isUpdatingWaterfall: false,
        isConnected: false,
        
        // Scale control options
        lowerScaleMode: 'auto',
        upperScaleMode: 'auto',
        fixedLowerScale: -100,
        fixedUpperScale: -40,
        
        // Store last valid values
        lastValidLowerScale: -100,
        lastValidUpperScale: -40,
        
        // Site selection data
        sites: [],
        currentSite: null,
        currentSiteName: '',
        currentSiteOwner: '',
        
        freqRange: {
            min: null,
            max: null
        },
        timeRange: '1h',
        viewMode: 'spectrum_waterfall',
        
        historicalData: [],
        stats: {
            avgPower: 0,
            peakPower: 0
        },
        
        deviceConfig: {
            name: '',
            location: '',
            freqMin: null,
            freqMax: null
        },
        deviceLogs: [],
        
        alertRule: {
            name: '',
            condition: 'power_above',
            threshold: 0,
            severity: 'low'
        },
        alertRules: [],
        
        theme: 'dark',
        preferences: {
            theme: 'dark',
            updateInterval: 5,
            defaultView: 'spectrum'
        },
        
        systemInfo: {
            version: '1.1.2',
            lastUpdate: '',
            dbStatus: 'connected',
            activeDevices: 0,
            totalAlerts: 0,
            wifi: [],
            processes: {}
        },
        selectedMonth: new Date().toISOString().slice(0, 7),
        selectedDate: new Date().toISOString().split('T')[0],
        selectedTimeRange: '1h',
        filteredData: [],
        spectrumChart: null,
        waterfallChart: null,
        currentData: null,
        
        // New spectrum options
        timeRangeMode: '12h',
        customTimeRange: '',
        showGrid: true,
        showMarkers: true,
        autoScale: true,
        isSidebarCollapsed: false,
        markers: [],
        selectedData: null,
        markerColorMode: 'default', // 'default' or 'random'
        
        // Unit mode: dBFS or dBm
        unitMode: localStorage.getItem('sdr_unit_mode') || 'dbfs',
        dbmOffset: parseFloat(localStorage.getItem('sdr_dbm_offset') || '0'),
        
        // Chart settings from config
        spectrumChartId: 'spectrumChart',
        waterfallChartId: 'waterfallChart',
        defaultViewMode: 'spectrum_waterfall',
        
        // Monitoring settings from config
        updateInterval: 5,  // seconds
        defaultTimeRange: '1h',
        
        // Subservice data
        subservices: [],
        selectedSubservice: null,
        error: null,
        lastUpdated: null,
        
        // --- System Info & Settings & UPT Management Safe Defaults ---
        // These prevent crashes if mixins fail or during initial render
        index: 0,
        upt: { id_upt: '' },
        site: null,
        log: null,
        marker: null,
        item: null,
        sub: null,
        downloadDays: '1',
        anomalies: [],
        upts: [],
        loading: false,
        sdrStatus: 'unknown',
        sdrLoading: false,
        heartbeatInterval: 300,
        agentIntervalMinutes: 10,
        hbLoading: false,
        agentIntervalLoading: false,
        newUpt: { id_upt: '', username: '', fullname: '', password: '' },
        newSite: { username: '', id_perangkat: '', site_name: '', token: '' },
        loadingAction: false,
        sdrActive: false,
        showDeviceList: false,
        gain: null,
        sampleRate: null,
        // -----------------------------------------------------------

        chartInitialized: false,
        chartInitAttempts: 0,
        maxChartInitAttempts: 10,
        // Store original values for reset
        defaultFilters: {
            freqRange: {
                min: null,
                max: null
            },
            timeRange: '1h',
            viewMode: 'spectrum_waterfall'
        },
        initRetryCount: 0,
        maxInitRetries: 5,
        initRetryDelay: 200, // ms
        maxMarkers: 20,
        markerColors: [
            '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF',
            '#00FFFF', '#FFA500', '#800080', '#008000', '#000080',
            '#FF4500', '#32CD32', '#4169E1', '#FFD700', '#DA70D6',
            '#20B2AA', '#FF6347', '#7CFC00', '#1E90FF', '#FF69B4'
        ],
        draggingMarker: null,
        contextMenuPoint: null,
        selectedFrequency: null,
        selectedTime: null,
        selectedLevel: null,
        allSpectrumData: [], // Store all spectrum data
        isDataLoading: false, // Flag to prevent multiple loads
        selectedDataFilename: null,
        
        // ---- System Info placeholders to avoid ReferenceError during parent compile ----
        deviceStatus: '-',
        lastUpdate: '-',
        uiVersion: '-',
        dbStatus: '-',
        cpuUtil: null,
        cpuTemp: null,
        freeStorage: null,
        totalStorage: null,
        freeRAM: null,
        totalRAM: null,
        // Computed placeholders for System Info (ensure parent #app can render the template safely)
        // These will be overridden by #sysinfo-app instance when it mounts
        storageUsedGB: null,
        storageUsedPct: null,
        memoryUsedMB: null,
        memoryUsedPct: null,
        
        // Request flags to prevent race conditions/resource exhaustion
        isFetchingAnomalies: false,
        isFetchingSystemInfo: false,
    },
    computed: {
        activeAlerts() {
            return this.alerts.filter(alert => !alert.dismissed).length;
        },
        selectedSiteLabel() {
            if (this.currentSiteName) return this.currentSiteName;
            if (this.currentSite && (this.currentSite.site_name || this.currentSite.Site)) {
                return this.currentSite.site_name || this.currentSite.Site;
            }
            return '-';
        },
        selectedSubserviceInfo() {
            if (!this.subservices || this.subservices.length === 0) return null;
            if (this.selectedSubservice) {
                return this.subservices.find(s => s.band_number === this.selectedSubservice) || null;
            }
            return this.subservices[0] || null;
        },
        selectedDataInfo() {
            if (this.selectedDataFilename && this.filteredData && this.filteredData.length > 0) {
                const found = this.filteredData.find(d => d.filename === this.selectedDataFilename);
                if (found) return found;
            }
            if (this.selectedData) return this.selectedData;
            if (this.filteredData && this.filteredData.length > 0) return this.filteredData[0];
            return null;
        },
        formattedDate: {
            get() {
                return this.selectedDate;
            },
            set(value) {
                this.selectedDate = value;
            }
        },
        availableDatesForMonth() {
            const rows = Array.isArray(this.allSpectrumData) ? this.allSpectrumData : [];
            const dates = rows
                .map(item => (item && item.date ? String(item.date) : ''))
                .filter(Boolean);
            const unique = Array.from(new Set(dates));
            unique.sort((a, b) => new Date(a) - new Date(b));
            return unique;
        },
        currentDateDisplay() {
            if (!this.selectedDate) return 'Select Date';
            const parts = this.selectedDate.split('-');
            if (parts.length === 3) {
                const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                const day = parts[2];
                const monthIdx = parseInt(parts[1], 10) - 1;
                const year = parts[0];
                if (monthIdx >= 0 && monthIdx < 12) {
                    return `${day} ${months[monthIdx]} ${year}`;
                }
            }
            return this.selectedDate;
        }
    },
    mounted: async function () {
        console.log('Vue instance mounted');

        // Listen for external site selection events (from monitoring.js or other scripts)
        window.addEventListener('external-site-selected', (e) => {
            const siteName = e.detail && e.detail.siteName;
            console.log('Received external-site-selected event:', siteName);
            if (siteName && this.sites.length > 0) {
                const site = this.sites.find(s => s.site_name === siteName);
                if (site) {
                    this.selectSite(site);
                } else {
                    console.warn('Site not found in available sites:', siteName);
                    // Try to load sites again just in case
                    this.loadSites().then(() => {
                        const refreshedSite = this.sites.find(s => s.site_name === siteName);
                        if (refreshedSite) this.selectSite(refreshedSite);
                    });
                }
            }
        });
        
        // --- System Info Logic Injection ---
        // If we are on system info page, start polling
        if (window.__MONSFER_AUTHENTICATED === true && window.location.pathname.includes('/system_info')) {
            this.fetchAnomalies();
            if (typeof this.loadSystemInfo === 'function') {
                this.loadSystemInfo();
                this._sysInfoTimer = setInterval(() => {
                    try { this.loadSystemInfo(); } catch (e) {}
                }, 30000);
            }
            // Poll for anomalies
            this._anomalyTimer = setInterval(this.fetchAnomalies, 30000);
        }
        // -----------------------------------
        
        // Get CSRF token from meta tag or cookie
        const getCsrfToken = () => {
            const metaToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
            if (metaToken) return metaToken;
            
            // Fallback to cookie if meta tag is not available
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                const [name, value] = cookie.trim().split('=');
                if (name === 'csrf_token') return value;
            }
            return null;
        };
        
        // Load scale settings from cookies
        this.loadScaleSettings();

        // Load user preferences (theme removed; keep other preferences only)
        this.loadPreferences();

        if (window.location.pathname === '/monitoring') {
            if (window.__MONSFER_PREVIEW_MODE === true) {
                this.viewMode = 'spectrum';
            }
            const defaultView = this.preferences && typeof this.preferences.defaultView === 'string'
                ? this.preferences.defaultView
                : null;
            if (window.__MONSFER_PREVIEW_MODE !== true) {
                if (defaultView === 'spectrum') this.viewMode = 'spectrum';
                if (defaultView === 'spectrum_waterfall') this.viewMode = 'spectrum_waterfall';
                if (defaultView === 'spectrum_3d') this.viewMode = 'spectrum_3d';
            }
        }
        
        const csrfToken = getCsrfToken();
        if (!csrfToken) {
            console.error('CSRF token not found');
            return;
        }
        
        // Set CSRF token in axios default headers (support both header names)
        axios.defaults.headers.common['X-CSRF-Token'] = csrfToken;
        axios.defaults.headers.common['X-CSRFToken'] = csrfToken;
        
        // Add CSRF token to all forms
        document.addEventListener('DOMContentLoaded', function() {
            const forms = document.querySelectorAll('form');
            forms.forEach(form => {
                if (!form.querySelector('input[name="csrf_token"]')) {
                    const csrfInput = document.createElement('input');
                    csrfInput.type = 'hidden';
                    csrfInput.name = 'csrf_token';
                    csrfInput.value = csrfToken;
                    form.appendChild(csrfInput);
                }
            });
        });
        
        // Override fetch to include CSRF token (if present), send cookies, and handle 401 globally
        const originalFetch = window.fetch;
        window.fetch = async function(url, options = {}) {
            if (!options.credentials) options.credentials = 'same-origin';
            if (options.method && options.method !== 'GET' && csrfToken) {
                options.headers = {
                    ...options.headers,
                    'X-CSRF-Token': csrfToken,
                    'X-CSRFToken': csrfToken
                };
            }
            const response = await originalFetch(url, options);
            if (response && response.status === 401) {
                console.warn('Unauthorized (401) detected in fetch.');
                // window.location.href = '/login'; // DISABLED to prevent loops
            }
            return response;
        };
        
        // Add error handler for CSRF errors and global 401 handling for axios
        axios.defaults.withCredentials = true;
        axios.interceptors.response.use(
            response => response,
            error => {
                if (error && error.response) {
                    if (error.response.status === 401) {
                        console.warn('Axios 401 Unauthorized detected.');
                        // window.location.href = '/login'; // DISABLED to prevent loops
                        return Promise.reject(error);
                    }
                    if (error.response.status === 400 && 
                        error.response.data && error.response.data.error === 'CSRF token missing or invalid') {
                        console.warn('CSRF Error detected. Please refresh manually.');
                        // window.location.reload(); // DISABLED to prevent loops
                    }
                }
                return Promise.reject(error);
            }
        );

        // Load sites for current user - this should happen on all pages
        // Await to ensure site selection completes before any page-specific data loads
        try {
            await this.loadSites();
        } catch (e) {
            console.error('Critical error loading sites:', e);
            this.error = 'Failed to load initial configuration';
        }

        // Force removal of v-cloak if it persists
        setTimeout(() => {
            const el = document.querySelector('.content-container');
            if (el) el.removeAttribute('v-cloak');
        }, 500);
        
        // Load sidebar state from cookie
        const savedSidebarState = this.getCookie('isSidebarCollapsed');
        if (savedSidebarState !== null) {
            this.isSidebarCollapsed = savedSidebarState === 'true';
        }
        
        // Only initialize monitoring features if on monitoring page
        if (this.isMonitoringPage) {
            // Load spectrum options state from cookie
            
            // Do NOT load data yet. It will be loaded after site-selected.
            
            this.$nextTick(async () => {
                console.log('DOM updated, initializing chart...');
                await this.ensureEchartsLoaded();
                await this.ensureChartInitialized();
                this.initWaterfallIfNeeded();
                console.log('Charts initialized, waiting for site selection to load data...');

                if (window.__MONSFER_PREVIEW_MODE === true) {
                    return;
                }
                
                // Set up ResizeObserver for both charts
                const setupResizeObserver = (elementId, isWaterfall = false) => {
                    const element = document.getElementById(elementId);
                    if (element) {
                        const resizeObserver = new ResizeObserver(entries => {
                            for (let entry of entries) {
                                const { width, height } = entry.contentRect;
                                if (isWaterfall && this.waterfallChart && typeof Plotly !== 'undefined') {
                                    Plotly.relayout('waterfallChart', {
                                        width: width,
                                        height: height,
                                        autosize: true
                                    });
                                } else if (!isWaterfall && this.chart) {
                                    this.chart.resize({
                                        width: width,
                                        height: height
                                    });
                                }
                            }
                        });
                        resizeObserver.observe(element);
                    }
                };

                // Setup observers for both charts
                setupResizeObserver('spectrumChart', false);
                setupResizeObserver('waterfallChart', true);

                // Initialize theme toggle button in the UI (top-right)
                if (typeof this.initThemeToggle === 'function') {
                    this.initThemeToggle();
                }
                
                // Load subservices first
                try {
                    const response = await fetch('/api/subservices');
                    if (!response.ok) {
                        throw new Error('Failed to load subservices');
                    }
                    const data = await response.json();
                    console.log('Received subservices data:', data);
                    
                    if (data.subservices && Array.isArray(data.subservices)) {
                        this.subservices = data.subservices.map(s => ({
                            band_number: s.band_number,
                            name: (s.name && s.name.trim()) ? s.name : `Band ${s.band_number}`,
                            start_freq: parseFloat(s.start_freq),
                            stop_freq: parseFloat(s.stop_freq),
                            step_bw: parseFloat(s.step_bw),
                            label: (s.name && s.name.trim()) ? s.name : `Band ${s.band_number}`
                        }));
                        console.log('Subservices loaded successfully:', this.subservices);
                        
                        // Auto-select first items in mobile view
                        if (window.innerWidth < 768) {
                            if (this.filteredData.length > 0) {
                                this.selectedData = this.filteredData[0];
                                this.loadSpectrumData(this.selectedData.filename);
                            }
                            if (this.subservices.length > 0) {
                                this.selectedSubservice = this.subservices[0].band_number;
                                this.showSpectrum(this.subservices[0]);
                            }
                        }
                        
                        if (this.subservices.length > 0 && !this.selectedSubservice) {
                            this.selectedSubservice = this.subservices[0].band_number;
                        }

                        if (this.filteredData.length > 0 && !this.currentData) {
                            const item = this.selectedDataFilename
                                ? (this.filteredData.find(d => d.filename === this.selectedDataFilename) || this.filteredData[0])
                                : this.filteredData[0];
                            const svc = this.selectedSubservice
                                ? (this.subservices.find(s => s.band_number === this.selectedSubservice) || this.subservices[0])
                                : this.subservices[0];
                            if (item && svc) {
                                this.loadSpectrumData(item.filename, svc.start_freq, svc.stop_freq);
                            }
                        }
                    } else {
                        throw new Error('Invalid subservices data format');
                    }
                } catch (error) {
                    console.error('Error loading subservices:', error);
                    this.error = 'Failed to load subservices. Please try again.';
                    this.subservices = []; // Reset subservices array
                }
            });
        }

        // Add window resize handler
        this._boundHandleResize = this.handleResize.bind(this);
        window.addEventListener('resize', this._boundHandleResize);
    },
    beforeDestroy() {
        // Remove window resize handler
        window.removeEventListener('resize', this._boundHandleResize);
        try { clearInterval(this._sysInfoTimer); } catch (e) {}
        try { clearInterval(this._anomalyTimer); } catch (e) {}
    },
    methods: {
        // ---- Unit conversion methods (dBFS <=> dBm) ----
        setUnitMode(mode) {
            this.unitMode = mode;
            localStorage.setItem('sdr_unit_mode', mode);
            this.applyUnitChange();
        },
        applyUnitChange() {
            localStorage.setItem('sdr_dbm_offset', String(this.dbmOffset || 0));
            if (this.currentData) this.updateChart(this.currentData);
            if (typeof this.updateChartMarkers === 'function') this.updateChartMarkers();
            window.dispatchEvent(new CustomEvent('sdr:unit-changed', {
                detail: { mode: this.unitMode, offset: parseFloat(this.dbmOffset || 0) }
            }));
        },
        displayPower(rawDbfs) {
            const v = parseFloat(rawDbfs);
            if (isNaN(v)) return rawDbfs;
            if (this.unitMode === 'dbm') {
                return (v + parseFloat(this.dbmOffset || 0)).toFixed(1);
            }
            return v.toFixed(1);
        },
        // -------------------------------------------------
        loadScriptOnce(url, globalName) {
            if (globalName && typeof window[globalName] !== 'undefined') {
                return Promise.resolve(window[globalName]);
            }
            if (!window.__monsferScriptPromises) window.__monsferScriptPromises = {};
            if (window.__monsferScriptPromises[url]) return window.__monsferScriptPromises[url];

            window.__monsferScriptPromises[url] = new Promise((resolve, reject) => {
                const existing = document.querySelector(`script[data-monsfer-src="${url}"]`);
                if (existing) {
                    const done = () => {
                        if (!globalName || typeof window[globalName] !== 'undefined') {
                            resolve(globalName ? window[globalName] : true);
                        } else {
                            reject(new Error(`Script loaded but global ${globalName} missing`));
                        }
                    };
                    if (existing.getAttribute('data-loaded') === 'true') {
                        done();
                        return;
                    }
                    existing.addEventListener('load', done, { once: true });
                    existing.addEventListener('error', () => reject(new Error(`Failed to load ${url}`)), { once: true });
                    return;
                }

                const script = document.createElement('script');
                script.src = url;
                script.async = true;
                script.setAttribute('data-monsfer-src', url);
                script.addEventListener('load', () => {
                    script.setAttribute('data-loaded', 'true');
                    if (!globalName || typeof window[globalName] !== 'undefined') {
                        resolve(globalName ? window[globalName] : true);
                    } else {
                        reject(new Error(`Script loaded but global ${globalName} missing`));
                    }
                }, { once: true });
                script.addEventListener('error', () => reject(new Error(`Failed to load ${url}`)), { once: true });
                document.head.appendChild(script);
            });

            return window.__monsferScriptPromises[url];
        },
        ensureEchartsLoaded() {
            if (typeof echarts !== 'undefined') return Promise.resolve(echarts);
            if (this._echartsLoadPromise) return this._echartsLoadPromise;
            
            const localUrl = '/js/components/echarts.js';
            const cdnUrl = 'https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js';
            
            this._echartsLoadPromise = this.loadScriptOnce(localUrl, 'echarts')
                .catch(e => {
                    console.warn('Local ECharts load failed, trying CDN...', e);
                    return this.loadScriptOnce(cdnUrl, 'echarts');
                });
            return this._echartsLoadPromise;
        },
        ensurePlotlyLoaded() {
            if (typeof Plotly !== 'undefined') return Promise.resolve(Plotly);
            if (this._plotlyLoadPromise) return this._plotlyLoadPromise;
            
            const localUrl = '/js/components/plot.js';
            const cdnUrl = 'https://cdn.plot.ly/plotly-2.27.0.min.js';
            
            this._plotlyLoadPromise = this.loadScriptOnce(localUrl, 'Plotly')
                .catch(e => {
                    console.warn('Local Plotly load failed, trying CDN...', e);
                    return this.loadScriptOnce(cdnUrl, 'Plotly');
                })
                .then((p) => {
                    try { window.dispatchEvent(new Event('plotlyReady')); } catch (e) {}
                    return p;
                });
            return this._plotlyLoadPromise;
        },
        initWaterfallIfNeeded() {
            if (!this.isMonitoringPage) return;
            if (this.viewMode === 'spectrum') return;
            if (this.waterfallChart) return;
            if (this.isWaterfallLoading) return;
            this.isWaterfallLoading = true;
            setTimeout(() => {
                this.ensurePlotlyLoaded()
                    .then(() => {
                        this.isWaterfallLoading = false;
                        this.initWaterfallChart();
                    })
                    .catch((e) => {
                        this.isWaterfallLoading = false;
                        console.error('Failed to load Plotly:', e);
                    });
            }, 0);
        },
        // --- System Info helper methods (safe fallbacks for parent #app) ---
        donutStyle(percentage, color) {
            if (percentage == null || isNaN(Number(percentage))) percentage = 0;
            const p = Math.max(0, Math.min(100, Number(percentage)));
            const bgColor = '#e5e7eb';
            return {
                background: `conic-gradient(${color || 'var(--accent)'} 0% ${p}%, ${bgColor} ${p}% 100%)`,
                WebkitMask: 'radial-gradient(farthest-side, #0000 calc(70% - 12px), #000 calc(70% - 6px))',
                mask: 'radial-gradient(farthest-side, #0000 calc(70% - 12px), #000 calc(70% - 6px))',
                borderRadius: '50%',
                width: '130px',
                height: '130px',
                position: 'relative'
            };
        },
        cpuTempToPct(temp) {
            if (temp == null) return 0;
            const t = Math.max(0, Math.min(100, Number(temp)));
            return t;
        },
        formatPercent(v) { return v == null ? '-' : `${Number(v).toFixed(1)}%`; },
        formatTemp(v) { return v == null ? '-' : `${Number(v).toFixed(1)} °C`; },
        formatGB(v) { return v == null ? '0 GB' : `${Number(v).toFixed(2)} GB`; },
        formatMB(v) { return v == null ? '0 MB' : `${Number(v).toFixed(0)} MB`; },
        formatMHz(v) {
            const x = Number(v);
            if (!isFinite(x)) return '-';
            return Number.isInteger(x) ? `${x}` : `${x.toFixed(2).replace(/\.00$/, '')}`;
        },
        formatKHz(v) {
            const x = Number(v);
            if (!isFinite(x)) return '-';
            return Number.isInteger(x) ? `${x}` : `${x.toFixed(2).replace(/\.00$/, '')}`;
        },
        formatSubserviceDetails(s) {
            return `Freq: ${this.formatMHz(s.start_freq)}-${this.formatMHz(s.stop_freq)} MHz, ${this.formatKHz(s.step_bw)} KHz`;
        },
        // --- System Info Methods ---
        downloadMetrics: function() {
            const site = (this.currentSite && (this.currentSite.site_name || this.currentSite.Site)) || (this.systemInfo && this.systemInfo.site) || 'plamongan indah';
            const days = (this.downloadDays || '1').toString();
            const url = `/api/system/metrics/download?site=${encodeURIComponent(site)}&days=${encodeURIComponent(days)}`;
            window.location.href = url;
        },
        fetchAnomalies: async function() {
            if (this.isFetchingAnomalies) return;
            this.isFetchingAnomalies = true;
            try {
                if (typeof axios === 'undefined') return;
                const siteName = (this.currentSite && (this.currentSite.site_name || this.currentSite.Site)) || 'plamongan indah';
                const response = await axios.get('/api/system/anomalies', {
                    params: { site: siteName }
                });
                this.anomalies = response.data.anomalies || [];
            } catch (e) {
                try {
                    const status = e && e.response && e.response.status;
                    if (status === 401 || status === 403) return;
                } catch (_) {}
            } finally {
                this.isFetchingAnomalies = false;
            }
        },
        // --- Settings Page Fallback Methods ---
        // These prevent ReferenceError if the mixin fails to load or merge
        saveAgentInterval: function() { console.warn('saveAgentInterval fallback called'); },
        controlSDR: function() { console.warn('controlSDR fallback called'); },
        saveHeartbeat: function() { console.warn('saveHeartbeat fallback called'); },
        savePreferences: function() { console.warn('savePreferences fallback called'); },
        // ---------------------------

        // Load sites for current user
        async loadSites() {
            try {
                console.log('Fetching user sites...');
                const response = await axios.get('/api/user/sites');
                this.sites = response.data.sites || [];
                console.log('Received sites:', this.sites);

                if (!this.sites || this.sites.length === 0) {
                    try {
                        const dashboardResp = await axios.get('/api/system/dashboard');
                        const dashboardSites = dashboardResp.data && dashboardResp.data.sites ? dashboardResp.data.sites : {};
                        const siteNames = Object.keys(dashboardSites || {});
                        if (siteNames.length > 0) {
                            this.sites = siteNames.map(name => ({
                                site_name: name,
                                display_name: name,
                                username: ''
                            }));
                        }
                    } catch (e) {
                        console.warn('Dashboard fallback failed:', e);
                    }
                }
                
                if (this.sites.length > 0) {
                    // Get last selected site from session storage
                    const lastSelectedSiteName = sessionStorage.getItem('currentSiteName');
                    const lastSelectedOwner = sessionStorage.getItem('currentSiteOwner') || '';
                    let selectedSite = null;

                    if (lastSelectedSiteName) {
                        // Try to find the last selected site in the sites list
                        selectedSite = this.sites.find(site => {
                            const siteName = (site.site_name || site.Site || '').trim();
                            const siteOwner = (site.username || '').trim();
                            const targetName = (lastSelectedSiteName || '').trim();
                            const targetOwner = (lastSelectedOwner || '').trim();
                            
                            // If owner remembered, match on both name and owner
                            if (targetOwner) {
                                return siteName === targetName && siteOwner === targetOwner;
                            }
                            // Otherwise match on site name only
                            return siteName === targetName;
                        });
                    }

                    // If last selected site not found or no last selection, use first site
                    if (!selectedSite) {
                        selectedSite = this.sites[0];
                    }

                    console.log('Selected site:', selectedSite);
                    // Select the site and load its data
                    // Use nextTick to ensure Vue has rendered the options
                    this.$nextTick(() => {
                        this.selectSite(selectedSite);
                    });
                }
            } catch (error) {
                console.error('Error loading sites:', error);
                // Fallback: if we have session storage but API failed, try to construct a dummy site to allow UI to render
                const lastSelectedSiteName = sessionStorage.getItem('currentSiteName');
                if (lastSelectedSiteName && (!this.sites || this.sites.length === 0)) {
                    console.warn('API failed but session has site. Using fallback site.');
                    const fallbackSite = { site_name: lastSelectedSiteName, display_name: lastSelectedSiteName, username: 'unknown' };
                    this.sites = [fallbackSite];
                    this.selectSite(fallbackSite);
                }
            }
        },
        
        // Helper to handle string-based selection from UI
        onSiteNameChange() {
            console.log('Site name changed to:', this.currentSiteName);
            const site = this.sites.find(s => (s.site_name || s.Site) === this.currentSiteName);
            if (site) {
                this.selectSite(site);
            }
        },

        // Select a site
        async selectSite(site) {
            if (!site) return;
            if (typeof site === 'string') {
                const siteName = site;
                const resolved = (this.sites || []).find(s => (s && (s.site_name || s.Site)) === siteName);
                site = resolved || { site_name: siteName, display_name: siteName, username: '' };
            }
            this.currentSite = site;
            this.currentSiteName = site.site_name; // Sync string model
            this.currentSiteOwner = site.username || ''; // Sync owner
            sessionStorage.setItem('currentSiteName', site.site_name);
            sessionStorage.setItem('currentSiteOwner', site.username || '');
            console.log('Selecting site:', site.site_name, 'Owner:', this.currentSiteOwner);
            
            try {
                // Update session on server
                const response = await axios.post('/api/user/select-site', { 
                    site_name: site.site_name,
                    username: this.currentSiteOwner
                });
                console.log('Site selection response:', response.data);
                // Emit global event so other pages can react to site changes
                try {
                    window.dispatchEvent(new CustomEvent('site-selected', { detail: { site: this.currentSite } }));
                } catch (evtErr) {
                    console.warn('Unable to dispatch site-selected event:', evtErr);
                }
                
                // Only load monitoring data if on monitoring page
                if (this.isMonitoringPage) {
                    if (window.__MONSFER_PREVIEW_MODE === true) {
                        await this.ensureEchartsLoaded();
                        await this.ensureChartInitialized();
                        await this.loadPreviewSpectrum();
                        return;
                    }
                    // After site is selected, load all data
                    await this.loadAllData();

                    // Ensure subservices are available before loading spectrum
                    await this.loadSubservicesIfNeeded();
                    
                    // Then load spectrum data if we have filtered data
                    if (this.filteredData.length > 0) {
                        const latestData = this.filteredData[0];
                        // Determine frequency range from selected/first subservice
                        let startFreq = null;
                        let stopFreq = null;
                        if (this.subservices && this.subservices.length > 0) {
                            let svc = null;
                            if (this.selectedSubservice) {
                                svc = this.subservices.find(s => s.band_number === this.selectedSubservice) || this.subservices[0];
                            } else {
                                svc = this.subservices[0];
                                this.selectedSubservice = svc.band_number;
                            }
                            if (svc) {
                                startFreq = svc.start_freq;
                                stopFreq = svc.stop_freq;
                            }
                        }
                        await this.loadSpectrumData(latestData.filename, startFreq, stopFreq);
                    }
                }
            } catch (error) {
                console.error('Error selecting site:', error);
                // If unauthorized, redirect to login
                if (error.response && error.response.status === 401) {
                    window.location.href = '/login';
                }
            }
        },
        // Ensure subservices loaded
        async loadSubservicesIfNeeded() {
            if (this.subservices && this.subservices.length > 0) {
                return;
            }
            try {
                const response = await fetch('/api/subservices');
                if (!response.ok) {
                    throw new Error('Failed to load subservices');
                }
                const data = await response.json();
                if (data.subservices && Array.isArray(data.subservices)) {
                    this.subservices = data.subservices;
                    // Auto-select first if none is selected
                    if (!this.selectedSubservice && this.subservices.length > 0) {
                        this.selectedSubservice = this.subservices[0].band_number;
                    }
                } else {
                    console.warn('Invalid subservices data format');
                    this.subservices = [];
                }
            } catch (err) {
                console.error('Error loading subservices:', err);
                this.subservices = [];
            }
        },
        async ensureChartInitialized() {
            return new Promise((resolve) => {
                const tryInit = () => {
                    if (this.chartInitialized) {
                        console.log('Chart already initialized');
                        resolve();
                        return;
                    }

                    if (this.initRetryCount >= this.maxInitRetries) {
                        console.warn('Max chart init retries reached, proceeding anyway...');
                        resolve();
                        return;
                    }

                    this.initChartWithRetry();
                    this.initRetryCount++;

                    if (!this.chartInitialized) {
                        console.log(`Retrying chart initialization (${this.initRetryCount}/${this.maxInitRetries})`);
                        setTimeout(() => {
                            tryInit();
                        }, this.initRetryDelay);
                    } else {
                        console.log('Chart initialization successful');
                        resolve();
                    }
                };

                tryInit();
            });
        },

        initChartWithRetry() {
            console.log('Attempting to initialize chart...');
            if (this.chartInitialized) {
                console.log('Chart already initialized, skipping');
                return;
            }

            const spectrumDom = document.getElementById('spectrumChart');
            if (!spectrumDom) {
                console.warn(`Spectrum chart container not found, attempt ${this.initRetryCount + 1}/${this.maxInitRetries}`);
                return;
            }

            // Ensure container has dimensions to prevent ECharts rendering issues
            if (spectrumDom.clientHeight === 0) {
                 console.warn('Spectrum chart container has 0 height, forcing min-height...');
                 spectrumDom.style.minHeight = '400px'; 
                 spectrumDom.style.width = '100%';
            }

            try {
                // Initialize Spectrum Chart
                console.log('Creating Spectrum ECharts instance...');
                this.chart = echarts.init(spectrumDom);
                this.chartInitialized = true;
                
                // Add context menu
                const contextMenu = document.createElement('div');
                contextMenu.className = 'context-menu';
                contextMenu.style.display = 'none';
                contextMenu.innerHTML = `
                    <ul>
                        <li class="add-marker">Add Marker</li>
                        <li class="add-delta-marker">Add Delta Marker</li>
                    </ul>
                `;
                document.body.appendChild(contextMenu);

                // Bind click events for context menu options
                contextMenu.addEventListener('click', (evt) => {
                    const target = evt.target;
                    if (!target || !target.classList) return;
                    // Determine which action to perform
                    if (target.classList.contains('add-marker')) {
                        if (this.contextMenuPoint) {
                            this.addMarkerAtPoint(this.contextMenuPoint);
                        }
                    } else if (target.classList.contains('add-delta-marker')) {
                        if (this.contextMenuPoint) {
                            this.addDeltaMarkerAtPoint(this.contextMenuPoint);
                        }
                    }
                    // Hide context menu after action
                    contextMenu.style.display = 'none';
                    this.contextMenuPoint = null;
                });

                // Hide context menu when clicking outside
                document.addEventListener('click', (e) => {
                    if (contextMenu.style.display === 'block') {
                        contextMenu.style.display = 'none';
                        this.contextMenuPoint = null;
                    }
                });

                // Hide context menu on Escape key
                document.addEventListener('keydown', (e) => {
                    if (e.key === 'Escape' && contextMenu.style.display === 'block') {
                        contextMenu.style.display = 'none';
                        this.contextMenuPoint = null;
                    }
                });

                // Bind click events for context menu options
                contextMenu.addEventListener('click', (evt) => {
                    const target = evt.target;
                    if (!target || !target.classList) return;
                    // Determine which action to perform
                    if (target.classList.contains('add-marker')) {
                        if (this.contextMenuPoint) {
                            this.addMarkerAtPoint(this.contextMenuPoint);
                        }
                    } else if (target.classList.contains('add-delta-marker')) {
                        if (this.contextMenuPoint) {
                            this.addDeltaMarkerAtPoint(this.contextMenuPoint);
                        }
                    }
                    // Hide context menu after action
                    contextMenu.style.display = 'none';
                    this.contextMenuPoint = null;
                });

                // Hide context menu when clicking outside
                document.addEventListener('click', (e) => {
                    if (contextMenu.style.display === 'block') {
                        contextMenu.style.display = 'none';
                        this.contextMenuPoint = null;
                    }
                });

                // Hide context menu on Escape key
                document.addEventListener('keydown', (e) => {
                    if (e.key === 'Escape' && contextMenu.style.display === 'block') {
                        contextMenu.style.display = 'none';
                        this.contextMenuPoint = null;
                    }
                });

                // Handle right-click
                this.chart.getZr().on('contextmenu', (params) => {
                    // Prevent default browser context menu
                    params.event.preventDefault();
                    
                    const pointInPixel = [params.offsetX, params.offsetY];
                    const pointInGrid = this.chart.convertFromPixel('grid', pointInPixel);
                    
                    // Find nearest data point
                    const series = this.chart.getOption().series[0];
                    if (!series || !series.data) return;
                    
                    const data = series.data;
                    let nearestPoint = null;
                    let minDistance = Infinity;
                    
                    data.forEach(point => {
                        const distance = Math.abs(point[0] - pointInGrid[0]);
                        if (distance < minDistance) {
                            minDistance = distance;
                            nearestPoint = point;
                        }
                    });

                    if (nearestPoint) {
                        contextMenu.style.display = 'block';
                        contextMenu.style.left = `${params.event.clientX}px`;
                        contextMenu.style.top = `${params.event.clientY}px`;
                        this.contextMenuPoint = nearestPoint;
                    }
                });

                if (this.enableZoomSync) this.chart.on('datazoom', (params) => {
                    if (!this.waterfallChart || this.isUpdatingWaterfall) return;
                    const spectrumOption = this.chart.getOption();
                    const xAxis = spectrumOption.xAxis[0];
                    const startPercent = spectrumOption.dataZoom[0].start;
                    const endPercent = spectrumOption.dataZoom[0].end;
                    const totalRange = xAxis.max - xAxis.min;
                    const startFreq = xAxis.min + (totalRange * (startPercent / 100));
                    const endFreq = xAxis.min + (totalRange * (endPercent / 100));
                    this.syncingZoom = true;
                    Plotly.relayout('waterfallChart', {
                        'xaxis.range': [startFreq, endFreq]
                    });
                    setTimeout(() => { this.syncingZoom = false; }, 0);
                });

                // Add mouse event handlers for click and drag zoom + marker dragging
                this.chart.getZr().on('mousedown', (params) => {
                    if (params.event.altKey || params.event.ctrlKey) {
                        this.chart.dispatchAction({
                            type: 'takeGlobalCursor',
                            key: 'dataZoomSelect',
                            dataZoomSelectActive: true
                        });
                    } else {
                        // Start dragging nearest marker if clicked near one
                        const clickX = params.event.offsetX;
                        const clickY = params.event.offsetY;
                        let nearestIndex = null;
                        let minDist = Infinity;
                        const threshold = 12; // px tolerance around marker
                        if (this.markers && this.markers.length > 0) {
                            for (let i = 0; i < this.markers.length; i++) {
                                const m = this.markers[i];
                                const px = this.chart.convertToPixel('grid', [parseFloat(m.frequency), parseFloat(m.power)]);
                                if (!px) continue;
                                const dx = px[0] - clickX;
                                const dy = px[1] - clickY;
                                const dist = Math.sqrt(dx * dx + dy * dy);
                                if (dist < minDist) {
                                    minDist = dist;
                                    nearestIndex = i;
                                }
                            }
                            if (nearestIndex !== null && minDist <= threshold) {
                                this.draggingMarker = nearestIndex;
                                document.body.style.cursor = 'grabbing';
                                // Hide context menu if open
                                const contextMenu = document.querySelector('.context-menu');
                                if (contextMenu && contextMenu.style.display === 'block') {
                                    contextMenu.style.display = 'none';
                                    this.contextMenuPoint = null;
                                }
                            } else {
                                this.draggingMarker = null;
                            }
                        }
                    }
                });

                // Update marker position while dragging
                this.chart.getZr().on('mousemove', (params) => {
                    if (this.draggingMarker !== null) {
                        const cursorX = params.event.offsetX;
                        const cursorY = params.event.offsetY;
                        const dataCoord = this.chart.convertFromPixel('grid', [cursorX, cursorY]);
                        if (dataCoord && Array.isArray(dataCoord)) {
                            const freq = parseFloat(dataCoord[0]);
                            const opt = this.chart.getOption();
                            const xMin = opt.xAxis[0].min;
                            const xMax = opt.xAxis[0].max;
                            const clampedFreq = Math.max(Math.min(freq, xMax), xMin);
                            const snapped = this.snapPointToSpectrum(clampedFreq);
                            this.markers[this.draggingMarker] = {
                                ...this.markers[this.draggingMarker],
                                frequency: snapped.frequency.toFixed(3),
                                power: snapped.power.toFixed(2)
                            };
                            this.updateChartMarkers();
                        }
                    }
                });

                this.chart.getZr().on('mouseup', () => {
                    this.chart.dispatchAction({
                        type: 'takeGlobalCursor',
                        key: 'dataZoomSelect',
                        dataZoomSelectActive: false
                    });
                    if (this.draggingMarker !== null) {
                        this.draggingMarker = null;
                        document.body.style.cursor = 'default';
                    }
                });

                // Set initial spectrum chart options
                console.log('Setting initial spectrum chart options...');
                const initialConfig = this.getSpectrumChartConfig();
                initialConfig.series = [{
                    type: 'line',
                    data: [],
                    symbol: 'none',
                    lineStyle: {
                        width: 2
                    },
                    animation: false,
                    markPoint: {
                        symbol: 'triangle',
                        symbolSize: 12,
                        symbolRotate: 180,
                        data: [],
                        draggable: true
                    }
                }];

                this.chart.setOption(initialConfig);

                // Handle resize
                window.addEventListener('resize', () => {
                    if (this.chart) {
                        this.chart.resize();
                    }
                });

                console.log('Spectrum chart initialized successfully');

                // Listen for unit changes (dBFS <=> dBm) dispatched by the monitoring page mixin
                window.addEventListener('sdr:unit-changed', () => {
                    if (this.currentData) {
                        this.updateChart(this.currentData);
                        this.updateChartMarkers();
                    }
                });

            } catch (error) {
                console.error('Error initializing spectrum chart:', error);
                this.error = 'Failed to initialize spectrum chart. Please refresh the page.';
            }
        },

        getSpectrumChartConfig() {
            return {
                animation: false,
                grid: {
                    left: '30px',
                    right: '20px',
                    bottom: '0px',
                    top: '10%',
                    containLabel: true,
                    // width: '100%'
                },
                dataZoom: [
                    {
                        type: 'slider',
                        show: false,
                        xAxisIndex: [0],
                        start: 0,
                        end: 100,
                        height: 8,
                        bottom: 0,
                        borderColor: 'transparent',
                        backgroundColor: 'rgba(0, 0, 0, 0.05)',
                        fillerColor: 'rgba(0, 0, 0, 0.1)',
                        handleStyle: {
                            color: '#666',
                            borderColor: '#666'
                        }
                    },
                    {
                        type: 'inside',
                        xAxisIndex: [0],
                        start: 0,
                        end: 100,
                        zoomOnMouseWheel: true,
                        moveOnMouseMove: true,
                        zoomLock: false,
                        throttle: 100,
                        filterMode: 'filter',
                        preventDefaultMouseMove: false,
                        rangeMode: ['value', 'value']
                    }
                ],
                tooltip: {
                    trigger: 'axis',
                    position: function(pos, params, dom, rect, size) {
                        const obj = {top: 10};
                        obj[['left', 'right'][+(pos[0] < size.viewSize[0] / 2)]] = 10;
                        return obj;
                    },
                    axisPointer: {
                        type: 'line',
                        snap: true,
                        label: {
                            show: false
                        }
                    },
                    formatter: function(params) {
                        const data = params[0];
                        return `Frequency: ${data.value[0].toFixed(3)} MHz<br>Level: ${data.value[1].toFixed(2)} dBfs`;
                    }
                },
                xAxis: {
                    type: 'value',
                    axisLine: { show: this.showGrid },
                    axisTick: { show: this.showGrid },
                    splitLine: { show: this.showGrid },
                    animation: false,
                    // name: 'Frequency (MHz)',
                    nameLocation: 'middle',
                    nameGap: 30,
                    axisLabel: {
                        formatter: function(value) {
                            return Number.isInteger(value) ? value : value.toFixed(1);
                        }
                    }
                },
                yAxis: {
                    type: 'value',
                    interval: 10,
                    axisLine: { show: this.showGrid },
                    axisTick: { show: this.showGrid },
                    splitLine: { show: this.showGrid },
                    animation: false,
                    name: 'Level (dBfs)',
                    nameLocation: 'middle',
                    nameGap: 40
                }
            };
        },

        getWaterfallConfig() {
            const isDark = true; // Force dark for industrial theme
            const bgColor = isDark ? '#161616' : '#fff';
            const textColor = isDark ? '#a3a3a3' : '#333';
            const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';

            return {
                data: {
                    type: 'heatmap',
                    colorscale: [
                        [0, 'rgb(0, 0, 0)'],        // Black
                        [0.25, 'rgb(0, 0, 255)'],   // Blue
                        [0.5, 'rgb(0, 255, 0)'],    // Green
                        [0.75, 'rgb(255, 255, 0)'], // Yellow
                        [1, 'rgb(255, 0, 0)']       // Red
                    ],
                    showscale: false,
                    hovertemplate: 'Freq: %{x:.3f} MHz<br>Time: %{y|%H:%M:%S}<br>Level: %{z:.2f} dBfs<extra></extra>'
                },
                layout: {
                    paper_bgcolor: bgColor,
                    plot_bgcolor: bgColor,
                    font: { color: textColor },
                    xaxis: {
                        title: {
                            text: 'Frequency (MHz)',
                            standoff: 0,
                            x: 0,
                            xanchor: 'left',
                            y: -0.2
                        },
                        showgrid: this.showGrid,
                        gridcolor: gridColor,
                        zeroline: false,
                        side: 'bottom'
                    },
                    yaxis: {
                        title: 'Time',
                        type: 'date',
                        showgrid: this.showGrid,
                        gridcolor: gridColor,
                        zeroline: false,
                        autosize: true,
                        autorange: 'reversed', // Oldest (00:00) at the top, newest (23:59) at the bottom
                        tickformat: '%H:00',
                        tickmode: 'auto',
                        nticks: 6,
                        tickangle: 0
                    },
                    margin: { t: 0, r: 20, b: 50, l: 62 }
                },
                config: {
                    responsive: true,
                    displayModeBar: false,  // Hide the toolbar
                    displaylogo: false
                }
            };
        },

        getWaterfall3DConfig() {
            return {
                data: {
                    type: 'surface',
                    colorscale: [
                        [0, 'rgb(0, 0, 0)'],
                        [0.25, 'rgb(0, 0, 255)'],
                        [0.5, 'rgb(0, 255, 0)'],
                        [0.75, 'rgb(255, 255, 0)'],
                        [1, 'rgb(255, 0, 0)']
                    ],
                    showscale: false,
                    hovertemplate: 'Freq: %{x:.3f} MHz<br>Idx: %{y}<br>Level: %{z:.2f} dBfs<extra></extra>'
                },
                layout: {
                    scene: {
                        xaxis: { title: 'Frequency (MHz)', showgrid: this.showGrid },
                        yaxis: { title: 'Time Index', showgrid: this.showGrid },
                        zaxis: { title: 'Level (dBfs)', showgrid: this.showGrid }
                    },
                    margin: { t: 0, r: 20, b: 50, l: 62 }
                },
                config: {
                    responsive: true,
                    displayModeBar: false,
                    displaylogo: false
                }
            };
        },

        processWaterfallData(historicalData, startFreq, stopFreq) {
            if (!historicalData || !historicalData.band || !historicalData.data || !historicalData.data.length) {
                console.warn('Invalid or missing historical data:', historicalData);
                return null;
            }

            console.log('Processing waterfall data:', {
                startFreq,
                stopFreq,
                actualStartFreq: historicalData.band.actual_start_freq,
                actualStopFreq: historicalData.band.actual_stop_freq,
                dataPoints: historicalData.data.length
            });

            const frequencies = [];
            const times = [];
            const levels = [];

            // Get actual frequency range from the response
            const actualStartFreq = parseFloat(historicalData.band.actual_start_freq);
            const actualStopFreq = parseFloat(historicalData.band.actual_stop_freq);

            // Generate frequency array
            const numPoints = historicalData.data[0]?.data.length || 0;
            if (numPoints === 0) {
                console.warn('No data points in historical data');
                return null;
            }

            const freqStep = (actualStopFreq - actualStartFreq) / (numPoints - 1);
            for (let i = 0; i < numPoints; i++) {
                frequencies.push(actualStartFreq + (i * freqStep));
            }
            // Ensure the last point is exactly actualStopFreq
            frequencies[frequencies.length - 1] = actualStopFreq;

            // Process data in chronological order (oldest first)
            const chronologicalData = [...historicalData.data].sort((a, b) => 
                new Date(a.timestamp) - new Date(b.timestamp)
            );
            
            for (const item of chronologicalData) {
                if (item.timestamp && item.data && Array.isArray(item.data)) {
                    times.push(new Date(item.timestamp));
                    levels.push(item.data);
                }
            }

            if (times.length === 0 || levels.length === 0) {
                console.warn('No valid time series data found');
                return null;
            }

            console.log('Processed waterfall data:', {
                frequencies: {
                    start: frequencies[0],
                    end: frequencies[frequencies.length - 1],
                    count: frequencies.length
                },
                times: {
                    start: times[0],
                    end: times[times.length - 1],
                    count: times.length
                },
                levels: {
                    count: levels.length,
                    pointsPerTime: levels[0]?.length || 0
                }
            });

            return { frequencies, times, levels };
        },

        updateWaterfall3DChart(data, startFreq, stopFreq) {
            if (!this.waterfallChart) {
                console.warn('Waterfall chart not initialized');
                return;
            }
            try {
                const { frequencies, times, levels } = data;
                const config3d = this.getWaterfall3DConfig();
                const timeIndices = times.map((_, idx) => idx);

                let minLevel = Infinity;
                let maxLevel = -Infinity;
                for (let i = 0; i < levels.length; i++) {
                    const row = levels[i];
                    if (!row || !Array.isArray(row)) continue;
                    for (let j = 0; j < row.length; j++) {
                        const v = row[j];
                        if (v < minLevel) minLevel = v;
                        if (v > maxLevel) maxLevel = v;
                    }
                }
                if (!isFinite(minLevel)) minLevel = 0;
                if (!isFinite(maxLevel)) maxLevel = minLevel + 15;

                const plotData = [{
                    ...config3d.data,
                    z: levels,
                    x: frequencies,
                    y: timeIndices
                }];
                const layout = {
                    ...config3d.layout,
                    scene: {
                        ...config3d.layout.scene,
                        xaxis: { ...config3d.layout.scene.xaxis, range: [startFreq, stopFreq] },
                        zaxis: { ...config3d.layout.scene.zaxis, range: [minLevel, Math.max(maxLevel, minLevel + 15)] }
                    }
                };
                Plotly.react('waterfallChart', plotData, layout, config3d.config);
            } catch (e) {
                console.error('Error updating 3D waterfall chart:', e);
            }
        },

        updateWaterfallChart(data, startFreq, stopFreq) {
            if (!this.waterfallChart) {
                console.warn('Waterfall chart not initialized');
                return;
            }

            try {
                console.log('Updating waterfall chart with data:', {
                    frequencies: data.frequencies.length,
                    times: data.times.length,
                    levels: data.levels.length
                });

                const config = this.getWaterfallConfig();
                const { frequencies, times, levels } = data;

                let timeStart, timeEnd;
                const month = (this.selectedMonth || '').trim();
                if (month) {
                    const monthParts = month.split('-').map(Number);
                    timeStart = new Date(monthParts[0], monthParts[1] - 1, 1, 0, 0, 0, 0);
                    timeEnd = new Date(monthParts[0], monthParts[1], 0, 23, 59, 59, 999);
                } else if (this.selectedDate) {
                    const parts = this.selectedDate.split('-').map(Number);
                    timeStart = new Date(parts[0], parts[1] - 1, parts[2], 0, 0, 0, 0);
                    timeEnd   = new Date(parts[0], parts[1] - 1, parts[2], 23, 59, 59, 999);
                } else {
                    const latestTime = new Date(Math.max(...times.map(t => new Date(t))));
                    const earliestTime = new Date(Math.min(...times.map(t => new Date(t))));
                    timeStart = new Date(earliestTime);
                    timeStart.setHours(0, 0, 0, 0);
                    timeEnd = new Date(latestTime);
                    timeEnd.setHours(23, 59, 59, 999);
                }

                // Calculate min and max levels for autoscale without spreading large arrays
                let minLevel = Infinity;
                let maxLevel = -Infinity;
                for (let i = 0; i < levels.length; i++) {
                    const row = levels[i];
                    if (!row || !Array.isArray(row)) continue;
                    for (let j = 0; j < row.length; j++) {
                        const v = row[j];
                        if (v < minLevel) minLevel = v;
                        if (v > maxLevel) maxLevel = v;
                    }
                }
                if (!isFinite(minLevel)) minLevel = 0;
                if (!isFinite(maxLevel)) maxLevel = minLevel + 15;

                // Calculate adjusted levels based on scale control settings
                let adjustedMinLevel, adjustedMaxLevel;

                // Set minimum level based on mode
                if (this.lowerScaleMode === 'auto') {
                    adjustedMinLevel = minLevel;
                    // Update lastValidLowerScale with the auto-calculated value
                    this.lastValidLowerScale = minLevel;
                } else {
                    adjustedMinLevel = this.fixedLowerScale;
                }

                // Set maximum level based on mode
                if (this.upperScaleMode === 'auto') {
                    adjustedMaxLevel = Math.max(maxLevel, adjustedMinLevel + 15);
                    // Update lastValidUpperScale with the auto-calculated value
                    this.lastValidUpperScale = adjustedMaxLevel;
                } else {
                    adjustedMaxLevel = this.fixedUpperScale;
                }

                const plotData = [{
                    ...config.data,
                    z: levels,
                    x: frequencies,
                    y: times,
                    zmin: adjustedMinLevel,
                    zmax: adjustedMaxLevel
                }];

                if (this.syncingZoom) return;
                const layout = {
                    ...config.layout,
                    xaxis: {
                        ...config.layout.xaxis,
                        range: [startFreq, stopFreq]
                    },
                    yaxis: {
                        ...config.layout.yaxis,
                        range: [timeStart, timeEnd],
                        autorange: 'reversed',
                        tickformat: month ? '%d' : '%H:00',
                        tickmode: 'auto',
                        nticks: 6
                    },
                    coloraxis: {
                        cmin: adjustedMinLevel,
                        cmax: adjustedMaxLevel,
                        colorscale: config.data.colorscale
                    }
                };

                this.syncingZoom = true;
                Plotly.react('waterfallChart', plotData, layout, config.config);
                setTimeout(() => { this.syncingZoom = false; }, 0);

                console.log('Waterfall chart updated successfully');
            } catch (error) {
                console.error('Error updating waterfall chart:', error);
            }
        },

        initWaterfallChart() {
            if (typeof Plotly === 'undefined') {
                this.isWaterfallLoading = true;
                this.ensurePlotlyLoaded();
                if (!this._plotlyReadyListenerAttached) {
                    this._plotlyReadyListenerAttached = true;
                    window.addEventListener('plotlyReady', () => {
                        this._plotlyReadyListenerAttached = false;
                        this.isWaterfallLoading = false;
                        this.initWaterfallChart();
                    }, { once: true });
                }
                return;
            }

            const waterfallContainerId = this.waterfallChartId || 'waterfallChart';
            const waterfallDom = document.getElementById(waterfallContainerId);
            if (!waterfallDom) {
                setTimeout(() => this.initWaterfallChart(), 200);
                return;
            }

            try {
                const config = this.getWaterfallConfig();
                // Determine initial frequency range
                let startFreq = null;
                let stopFreq = null;
                if (this.selectedData && this.selectedData.actual_start_freq && this.selectedData.actual_stop_freq) {
                    startFreq = this.selectedData.actual_start_freq;
                    stopFreq = this.selectedData.actual_stop_freq;
                } else if (this.selectedSubservice) {
                    const selectedService = this.subservices.find(s => s.band_number === this.selectedSubservice);
                    if (selectedService) {
                        startFreq = selectedService.start_freq;
                        stopFreq = selectedService.stop_freq;
                    }
                }
                if (startFreq === null || stopFreq === null) {
                    // Fallback default range
                    startFreq = 0;
                    stopFreq = 100;
                }

                // Prepare a minimal placeholder heatmap so the chart is visible even before data arrives
                let timeStart, timeEnd;
                const month = (this.selectedMonth || '').trim();
                if (month) {
                    const parts = month.split('-').map(Number);
                    timeStart = new Date(parts[0], parts[1] - 1, 1, 0, 0, 0, 0);
                    timeEnd = new Date(parts[0], parts[1], 0, 23, 59, 59, 999);
                } else if (this.selectedDate) {
                    const parts = this.selectedDate.split('-').map(Number);
                    timeStart = new Date(parts[0], parts[1] - 1, parts[2], 0, 0, 0, 0);
                    timeEnd = new Date(parts[0], parts[1] - 1, parts[2], 23, 59, 59, 999);
                } else {
                    const now = new Date();
                    timeStart = new Date(now);
                    timeStart.setHours(0, 0, 0, 0);
                    timeEnd = new Date(now);
                    timeEnd.setHours(23, 59, 59, 999);
                }
                const plotData = [{
                    ...config.data,
                    z: [
                        [0, 0],
                        [0, 0]
                    ],
                    x: [startFreq, stopFreq],
                    y: [timeStart, timeEnd]
                }];

                const layout = {
                    ...config.layout,
                    xaxis: {
                        ...config.layout.xaxis,
                        range: [startFreq, stopFreq],
                        autorange: true
                    },
                    yaxis: {
                        ...config.layout.yaxis,
                        range: [timeStart, timeEnd],
                        autorange: 'reversed',
                        tickformat: month ? '%d' : '%H:00'
                    }
                };

                try { Plotly.purge(waterfallContainerId); } catch (e) {}
                Plotly.newPlot(waterfallContainerId, plotData, layout, config.config);

                if (this.enableZoomSync) document.getElementById(waterfallContainerId).on('plotly_relayout', (eventdata) => {
                    if (this.isUpdatingWaterfall || this.syncingZoom) return;
                    if (this.chart && eventdata['xaxis.range[0]'] !== undefined) {
                        const startFreq = eventdata['xaxis.range[0]'];
                        const endFreq = eventdata['xaxis.range[1]'];
                        const spectrumOption = this.chart.getOption();
                        const xAxis = spectrumOption.xAxis[0];
                        const totalRange = xAxis.max - xAxis.min;
                        const startPercent = ((startFreq - xAxis.min) / totalRange) * 100;
                        const endPercent = ((endFreq - xAxis.min) / totalRange) * 100;
                        this.syncingZoom = true;
                        this.chart.dispatchAction({
                            type: 'dataZoom',
                            start: startPercent,
                            end: endPercent
                        });
                        setTimeout(() => { this.syncingZoom = false; }, 0);
                    }
                });

                this.waterfallChart = document.getElementById(waterfallContainerId);
                console.log('Waterfall chart initialized successfully');
            } catch (error) {
                console.error('Error initializing waterfall chart:', error);
                // Retry after a short delay
                setTimeout(() => {
                    console.log('Attempting to reinitialize waterfall chart after error...');
                    this.initWaterfallChart();
                }, 1000);
            }
        },

        async updateWaterfallData(startFreq = null, stopFreq = null) {
            if (typeof Plotly === 'undefined') return;
            if (!this.waterfallChart || !this.isMonitoringPage) return;
            const nowTs = Date.now();
            if (this._lastWaterfallUpdate && (nowTs - this._lastWaterfallUpdate) < 500) {
                console.warn('Skipping waterfall update due to throttle');
                return;
            }
            this._lastWaterfallUpdate = nowTs;
            if (this.isUpdatingWaterfall) {
                console.warn('Waterfall update already in progress, skipping nested call');
                return;
            }

            try {
                this.isUpdatingWaterfall = true;
                // Show loading overlay before API call
                this.isWaterfallLoading = true;
                console.log('Starting waterfall data update...');
                console.log('[WF] selectedDate =', this.selectedDate, ', timeRange =', this.getTimeRange());
                
                // If no frequency range provided but we have a selected subservice, use its range
                if (startFreq === null && stopFreq === null && this.selectedSubservice) {
                    const selectedService = this.subservices.find(s => s.band_number === this.selectedSubservice);
                    if (selectedService) {
                        startFreq = selectedService.start_freq;
                        stopFreq = selectedService.stop_freq;
                        console.log('Using frequency range from selected subservice:', { startFreq, stopFreq });
                    }
                }

                // If still no frequency range, don't update
                if (startFreq === null || stopFreq === null) {
                    console.log('No frequency range provided, skipping waterfall update');
                    this.isWaterfallLoading = false;
                    return;
                }

                console.log('Fetching waterfall data with time range:', this.getTimeRange(), 'month:', this.selectedMonth);

                const month = (this.selectedMonth || '').trim();
                const monthParam = month ? `&month=${encodeURIComponent(month)}` : '';
                const dateParam = month ? '' : `&date=${encodeURIComponent(this.selectedDate || new Date().toISOString().slice(0,10))}`;
                const wfUrl = `/api/spectrum/history?startFreq=${startFreq}&stopFreq=${stopFreq}&timeRange=${this.getTimeRange()}&maxRows=240&maxPoints=512${monthParam}${dateParam}`;
                
                // Make API call with same-origin credentials for session/cookies
                const response = await fetch(wfUrl, {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json'
                    },
                    credentials: 'same-origin'
                });

                if (!response.ok) {
                    console.warn(`Waterfall API returned ${response.status}. Skipping update.`);
                    this.isWaterfallLoading = false;
                    return;
                }

                const historicalData = await response.json();
                console.log('[WF] URL =', wfUrl);
                console.log('Received waterfall data, processing...');
                
                const processedData = this.processWaterfallData(historicalData, startFreq, stopFreq);
                
                if (processedData) {
                    console.log('Updating waterfall chart...');
                    if (this.viewMode === 'spectrum_3d') {
                        this.updateWaterfall3DChart(processedData, startFreq, stopFreq);
                    } else {
                        this.updateWaterfallChart(processedData, startFreq, stopFreq);
                    }
                } else {
                    console.warn('Processed waterfall data is empty for date:', this.selectedDate);
                }
            } catch (error) {
                console.error('Error updating waterfall data:', error);
                this.error = 'Failed to update waterfall display';
            } finally {
                // Hide loading overlay after API call is complete
                console.log('Waterfall data update completed');
                this.isWaterfallLoading = false;
                this.isUpdatingWaterfall = false;
            }
        },

        updateWaterfallOptions() {
            if (!this.waterfallChart) return;

            try {
                const config = this.getWaterfallConfig();
                Plotly.relayout('waterfallChart', {
                    xaxis: config.layout.xaxis,
                    yaxis: config.layout.yaxis
                });
            } catch (error) {
                console.error('Error updating waterfall options:', error);
            }
        },

        async loadAllData() {
            // Prevent requests when site belum dipilih
            if (!this.currentSite) {
                console.warn('Tidak ada site yang dipilih. loadAllData() dibatalkan sampai site dipilih.');
                return;
            }
            if (this.isDataLoading) {
                console.log('Data is already loading, skipping...');
                return;
            }

            this.isDataLoading = true;
            try {
                const month = (this.selectedMonth || '').trim();
                const response = await fetch(`/api/spectrum/month?month=${encodeURIComponent(month)}`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const monthData = await response.json();
                console.log('Available month data:', month, monthData);

                if (!Array.isArray(monthData) || monthData.length === 0) {
                    console.warn('No data available for selected month:', month);
                    this.allSpectrumData = [];
                    this.filteredData = [];
                    this.selectedData = null;
                    this.error = 'No data available';
                    if (this.chart && this.chartInitialized) {
                        this.chart.clear();
                    }
                    return;
                }

                this.allSpectrumData = monthData;

                const availableDates = monthData
                    .map(item => (item && item.date ? String(item.date) : ''))
                    .filter(Boolean)
                    .sort((a, b) => new Date(b) - new Date(a));

                if (!this.selectedDate || !availableDates.includes(this.selectedDate)) {
                    this.selectedDate = availableDates[0];
                }

                await this.filterDataForCurrentDate();
                
                // Load initial data
                await this.loadInitialData();
            } catch (error) {
                console.error('Error loading all data:', error);
                this.error = 'Failed to load data. Please try again.';
            } finally {
                this.isDataLoading = false;
            }
        },

        formatTimeLabel(timeStr) {
            const s = String(timeStr || '');
            const parts = s.split(':');
            if (parts.length >= 2) return `${parts[0].padStart(2, '0')}:${parts[1].padStart(2, '0')}`;
            return s;
        },

        async handleDateChange() {
            try {
                await this.filterDataForCurrentDate();
                const chosen = (this.filteredData && this.filteredData.length > 0) ? this.filteredData[0] : null;
                if (!chosen) return;
                this.selectedDataFilename = chosen.filename;
                this.selectedData = chosen;

                const svc = this.selectedSubservice
                    ? (this.subservices.find(s => s.band_number === this.selectedSubservice) || null)
                    : (this.subservices[0] || null);
                const startFreq = svc ? svc.start_freq : null;
                const stopFreq = svc ? svc.stop_freq : null;
                await this.loadSpectrumData(chosen.filename, startFreq, stopFreq);
            } catch (e) {
                console.error('Error handling date change:', e);
            }
        },

        async handleDateChangeFromList(dateStr) {
            this.selectedDate = String(dateStr || '');
            await this.handleDateChange();
        },

        async filterDataForCurrentDate() {
            const month = (this.selectedMonth || '').trim();
            console.log('Filtering data for month:', month);
            console.log('All spectrum data:', this.allSpectrumData);

            const items = [];
            const rows = Array.isArray(this.allSpectrumData) ? this.allSpectrumData : [];
            const dates = rows.map(r => (r && r.date ? String(r.date) : '')).filter(Boolean);
            const dateSet = Array.from(new Set(dates));
            dateSet.sort((a, b) => new Date(b) - new Date(a));

            if (!this.selectedDate && dateSet.length > 0) {
                this.selectedDate = dateSet[0];
            }
            const targetDate = this.selectedDate;
            const dateData = rows.find(r => r && String(r.date || '') === targetDate) || null;
            const timesRaw = dateData
                ? (Array.isArray(dateData.time) ? dateData.time : (dateData.time ? [dateData.time] : []))
                : [];
            for (const time of timesRaw) {
                if (!time) continue;
                const timeStr = String(time);
                const formattedTime = timeStr.replace(/:/g, '-');
                const filename = `${targetDate}_${formattedTime}.csv`;
                items.push({
                    date: targetDate,
                    time: timeStr,
                    time_label: this.formatTimeLabel(timeStr),
                    display_time: this.formatTimeLabel(timeStr),
                    filename
                });
            }

            items.sort((a, b) => {
                const ta = new Date(`${a.date}T${a.time}`);
                const tb = new Date(`${b.date}T${b.time}`);
                return tb - ta;
            });

            this.filteredData = items;

            if (!items.length) {
                this.error = 'No data available for the selected month';
                this.selectedData = null;
                this.selectedDataFilename = null;
                if (this.chart && this.chartInitialized) {
                    this.chart.clear();
                }
                return;
            }

            const selectedFilename = this.selectedDataFilename || (this.selectedData && this.selectedData.filename) || null;
            const selectedItem = selectedFilename ? (items.find(d => d.filename === selectedFilename) || null) : null;
            const chosen = selectedItem || items[0];
            this.selectedDataFilename = chosen.filename;
            this.selectedData = chosen;
            this.selectedDate = chosen.date;
        },

        async loadInitialData() {
            console.log('Loading initial data...');
            this.error = null;
            
            if (this.filteredData.length > 0) {
                const latestData = this.filteredData[0]; // Already sorted by time
                console.log('Loading latest spectrum data:', latestData);
                
                await this.ensureChartInitialized();

                if (latestData && latestData.date) {
                    this.selectedDate = latestData.date;
                }
                
                // Use the filename that was created in filterDataForCurrentDate
                const filename = latestData.filename;
                
                if (this.selectedSubservice && this.subservices.length > 0) {
                    const lastSubservice = this.subservices.find(s => s.band_number === this.selectedSubservice);
                    if (lastSubservice) {
                        await this.loadSpectrumData(
                            filename,
                            lastSubservice.start_freq,
                            lastSubservice.stop_freq
                        );
                    }
                }
                
                if (this.subservices.length > 0 && !this.selectedSubservice) {
                    const firstSubservice = this.subservices[0];
                    this.selectedSubservice = firstSubservice.band_number;
                    await this.loadSpectrumData(
                        filename,
                        firstSubservice.start_freq,
                        firstSubservice.stop_freq
                    );
                }
            }
        },

        async loadPreviewSpectrum() {
            try {
                this.error = null;
                await this.ensureChartInitialized();

                if (!this.selectedDate) {
                    this.selectedDate = new Date().toISOString().split('T')[0];
                }

                await this.loadSubservicesIfNeeded();

                if (this.viewMode === 'spectrum') {
                    this.viewMode = 'spectrum_waterfall';
                }

                let startFreq = null;
                let stopFreq = null;
                if (this.subservices && this.subservices.length > 0) {
                    if (!this.selectedSubservice) {
                        this.selectedSubservice = this.subservices[0].band_number;
                    }
                    const svc = this.subservices.find(s => s.band_number === this.selectedSubservice) || this.subservices[0];
                    if (svc) {
                        startFreq = svc.start_freq;
                        stopFreq = svc.stop_freq;
                    }
                }

                const qs = new URLSearchParams();
                if (isFinite(parseFloat(startFreq))) qs.set('startFreq', parseFloat(startFreq));
                if (isFinite(parseFloat(stopFreq))) qs.set('stopFreq', parseFloat(stopFreq));
                qs.set('maxPoints', '512');
                const latestUrl = `/api/spectrum/latest?${qs.toString()}`;

                const resp = await fetch(latestUrl, {
                    method: 'GET',
                    headers: { 'Accept': 'application/json' },
                    credentials: 'same-origin'
                });

                if (!resp.ok) {
                    this.error = 'No spectrum data available';
                    return;
                }

                const payload = await resp.json();
                const levels = payload && Array.isArray(payload.data) ? payload.data : [];
                if (!levels.length) {
                    this.error = 'No spectrum data available';
                    return;
                }

                const band = payload && payload.band ? payload.band : {};
                const actualStartFreq = parseFloat(band.actual_start_freq);
                const actualStopFreq = parseFloat(band.actual_stop_freq);
                if (!isFinite(actualStartFreq) || !isFinite(actualStopFreq) || levels.length < 2) {
                    this.error = 'No spectrum data available';
                    return;
                }

                const numPoints = levels.length;
                const step = (actualStopFreq - actualStartFreq) / (numPoints - 1);
                const frequencies = new Array(numPoints);
                for (let i = 0; i < numPoints; i++) {
                    frequencies[i] = actualStartFreq + (i * step);
                }

                this.currentData = { x: frequencies, y: levels };
                if (this.chart && this.chartInitialized) {
                    this.updateChart(this.currentData);
                }

                const nowLabel = new Date().toLocaleTimeString();
                const previewItem = {
                    filename: 'preview',
                    display_time: nowLabel,
                    time: nowLabel
                };
                this.filteredData = [previewItem];
                this.selectedData = previewItem;
                this.selectedDataFilename = previewItem.filename;
                this.lastUpdated = nowLabel;

                if (this.viewMode !== 'spectrum') {
                    this.initWaterfallIfNeeded();
                    const wfStart = isFinite(parseFloat(startFreq)) ? parseFloat(startFreq) : actualStartFreq;
                    const wfStop = isFinite(parseFloat(stopFreq)) ? parseFloat(stopFreq) : actualStopFreq;
                    if (isFinite(wfStart) && isFinite(wfStop) && wfStart < wfStop) {
                        const month = (this.selectedMonth || '').trim();
                        const monthParam = month ? `&month=${encodeURIComponent(month)}` : '';
                        const dateParam = month ? '' : `&date=${encodeURIComponent(this.selectedDate || new Date().toISOString().slice(0,10))}`;
                        const wfUrl = `/api/spectrum/history?startFreq=${wfStart}&stopFreq=${wfStop}&timeRange=${this.getTimeRange()}&maxRows=240&maxPoints=512${monthParam}${dateParam}`;
                        try {
                            const wfResp = await fetch(wfUrl, { credentials: 'same-origin' });
                            if (wfResp.ok) {
                                const historicalData = await wfResp.json();
                                const processed = this.processWaterfallData(historicalData, wfStart, wfStop);
                                if (processed) {
                                    if (this.viewMode === 'spectrum_3d') {
                                        this.updateWaterfall3DChart(processed, wfStart, wfStop);
                                    } else {
                                        this.updateWaterfallChart(processed, wfStart, wfStop);
                                    }
                                } else if (this.currentData && Array.isArray(this.currentData.y)) {
                                    const base = this.currentData.y;
                                    const t0 = new Date(Date.now() - 60000).toISOString();
                                    const t1 = new Date().toISOString();
                                    const synthetic = {
                                        band: { actual_start_freq: actualStartFreq, actual_stop_freq: actualStopFreq },
                                        data: [
                                            { timestamp: t0, data: base },
                                            { timestamp: t1, data: base.map(v => v + 1.5) }
                                        ]
                                    };
                                    const fallbackProcessed = this.processWaterfallData(synthetic, wfStart, wfStop);
                                    if (fallbackProcessed) {
                                        if (this.viewMode === 'spectrum_3d') {
                                            this.updateWaterfall3DChart(fallbackProcessed, wfStart, wfStop);
                                        } else {
                                            this.updateWaterfallChart(fallbackProcessed, wfStart, wfStop);
                                        }
                                    }
                                }
                            }
                        } catch (e) {
                        }
                    }
                }
            } catch (e) {
                this.error = 'No spectrum data available';
            }
        },

        async loadSpectrumData(filename, start_freq = null, stop_freq = null) {
            // Prevent multiple simultaneous loading
            if (this.isSpectrumLoading) {
                console.log('Spectrum data is already loading, skipping...');
                return;
            }

            console.log('Loading spectrum data:', { filename, start_freq, stop_freq });
            this.isSpectrumLoading = true;
            this.isWaterfallLoading = true; // Show waterfall loading overlay
            
            try {
                // If no frequency range provided but we have a selected subservice, use its range
                if (start_freq === null && stop_freq === null && this.selectedSubservice) {
                    const selectedService = this.subservices.find(s => s.band_number === this.selectedSubservice);
                    if (selectedService) {
                        start_freq = selectedService.start_freq;
                        stop_freq = selectedService.stop_freq;
                        console.log('Using frequency range from selected subservice:', { start_freq, stop_freq });
                    }
                }

                // Prepare request data for spectrum
                const requestData = {
                    filename: filename,
                    start_freq: parseFloat(start_freq),
                    stop_freq: parseFloat(stop_freq),
                    max_points: 2048
                };
                console.log('Requesting data with frequency range:', requestData);

                // Fetch spectrum data
                const spectrumResponse = await fetch('/api/spectrum/request', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(requestData)
                });

                if (!spectrumResponse.ok) {
                    const errorData = await spectrumResponse.json();
                    const errCode = errorData && errorData.error ? String(errorData.error) : '';
                    if (spectrumResponse.status === 404 || errCode === 'file_not_found') {
                        console.warn('Spectrum file not found:', {
                            status: spectrumResponse.status,
                            error: errorData,
                            filename
                        });
                        this.error = 'No spectrum data available for selected file';
                        return;
                    }
                    console.error('Spectrum request failed:', {
                        status: spectrumResponse.status,
                        error: errorData
                    });
                    throw new Error(errCode || 'Failed to fetch spectrum data');
                }

                const spectrumData = await spectrumResponse.json();
                console.log('Received spectrum data:', spectrumData);
                
                if (!spectrumData || !Array.isArray(spectrumData.data) || spectrumData.data.length === 0) {
                    this.error = 'No spectrum data available for selected file';
                    this.isSpectrumLoading = false;
                    this.isWaterfallLoading = false;
                    return;
                }
                
                // Store the current data using actual frequencies from response
                const actualStartFreq = parseFloat(spectrumData.band.actual_start_freq);
                const actualStopFreq = parseFloat(spectrumData.band.actual_stop_freq);
                
                // Generate frequencies array
                const numPoints = spectrumData.data.length;
                const step = (actualStopFreq - actualStartFreq) / (numPoints - 1);
                const frequencies = [];
                
                // Generate frequencies with exact step size
                for (let i = 0; i < numPoints; i++) {
                    const freq = actualStartFreq + (i * step);
                    frequencies.push(freq);
                }
                
                // Ensure the last point is exactly actualStopFreq
                frequencies[frequencies.length - 1] = actualStopFreq;
                
                console.log('Generated frequencies:', {
                    start: frequencies[0],
                    end: frequencies[frequencies.length - 1],
                    length: frequencies.length,
                    step: step
                });
                
                this.currentData = {
                    x: frequencies,
                    y: spectrumData.data
                };
                
                // Update current data and selected item with actual frequencies
                this.selectedData = {
                    filename: filename,
                    start_freq: start_freq,
                    stop_freq: stop_freq,
                    actual_start_freq: actualStartFreq,
                    actual_stop_freq: actualStopFreq
                };
                
                // Update timestamp
                this.lastUpdated = new Date().toLocaleTimeString();

                // Update selectedDataFilename for mobile view
                this.selectedDataFilename = filename;
                
                // Update chart if initialized
                if (this.chart && this.chartInitialized) {
                    this.updateChart(this.currentData);
                }

                // Fetch waterfall data if not in spectrum-only mode
                if (this.viewMode !== 'spectrum') {
                    console.log('Fetching waterfall data...');
                    try {
                        // Prefer requested subservice range if provided; otherwise use actual response range
                        const hasRequestedRange = isFinite(parseFloat(start_freq)) && isFinite(parseFloat(stop_freq));
                        const wfStart = hasRequestedRange ? parseFloat(start_freq) : parseFloat(actualStartFreq);
                        const wfStop = hasRequestedRange ? parseFloat(stop_freq) : parseFloat(actualStopFreq);

                        if (wfStart === null || wfStop === null || !isFinite(parseFloat(wfStart)) || !isFinite(parseFloat(wfStop))) {
                            console.warn('Skipping waterfall fetch: invalid frequency range', { wfStart, wfStop });
                        } else {
                            const month = (this.selectedMonth || '').trim();
                            const monthParam = month ? `&month=${encodeURIComponent(month)}` : '';
                            const dateParam = month ? '' : `&date=${encodeURIComponent(this.selectedDate)}`;
                            const waterfallUrl = `/api/spectrum/history?startFreq=${wfStart}&stopFreq=${wfStop}&timeRange=${this.getTimeRange()}&maxRows=240&maxPoints=512${monthParam}${dateParam}`;
                            const waterfallResponse = await fetch(waterfallUrl, { credentials: 'same-origin' });
                            if (!waterfallResponse.ok) {
                                console.warn('Waterfall API returned non-OK response, skipping:', {
                                    status: waterfallResponse.status,
                                    statusText: waterfallResponse.statusText,
                                    url: waterfallUrl
                                });
                            } else {
                                const historicalData = await waterfallResponse.json();
                                console.log('Received waterfall data:', historicalData);

                                if (historicalData && historicalData.data && historicalData.data.length > 0) {
                                    const processedData = this.processWaterfallData(historicalData, wfStart, wfStop);
                                    if (processedData) {
                                        if (this.viewMode === 'spectrum_3d') {
                                            this.updateWaterfall3DChart(processedData, wfStart, wfStop);
                                        } else {
                                            this.updateWaterfallChart(processedData, wfStart, wfStop);
                                        }
                                    }
                                } else {
                                    console.warn('No waterfall data available');
                                }
                            }
                        }
                    } catch (error) {
                        console.warn('Error fetching waterfall data (non-blocking):', error);
                        // Don't throw error here, just log it
                    }
                }

            } catch (error) {
                console.error('Error loading spectrum data:', error);
                this.error = error.message || 'Failed to load spectrum data';
                throw error;
            } finally {
                this.isSpectrumLoading = false;
                this.isWaterfallLoading = false; // Hide waterfall loading overlay
            }
        },

        updateChart(data) {
            if (!this.chart || !data) return;
            try {
                const config = this.getSpectrumChartConfig();

                // -- Unit conversion (dBFS → dBm) --
                const unitMode = (this.unitMode) || 'dbfs';
                const offset = parseFloat(this.dbmOffset || 0);
                const yRaw = data.y;
                const yDisplay = (unitMode === 'dbm')
                    ? yRaw.map(v => v + offset)
                    : yRaw;
                const unitLabel = (unitMode === 'dbm') ? 'dBm' : 'dBFS';

                const seriesData = data.x.map((x, i) => [x, yDisplay[i]]);
                
                // Update grid visibility
                config.xAxis.splitLine.show = this.showGrid;
                config.yAxis.splitLine.show = this.showGrid;
                config.xAxis.axisLine.show = this.showGrid;
                config.yAxis.axisLine.show = this.showGrid;
                config.yAxis.name = unitLabel;

                // Handle axis limits
                let minX = data.x[0];
                let maxX = data.x[data.x.length - 1];
                config.xAxis.min = minX;
                config.xAxis.max = maxX;

                // Adjust fixed scale by offset
                if (!this.autoScale && this.upperScaleMode === 'fixed' && this.lowerScaleMode === 'fixed') {
                    config.yAxis.min = this.fixedLowerScale + (unitMode === 'dbm' ? offset : 0);
                    config.yAxis.max = this.fixedUpperScale + (unitMode === 'dbm' ? offset : 0);
                } else if (this.autoScale) {
                    config.yAxis.min = null;
                    config.yAxis.max = null;
                }

                config.series = [{
                    type: 'line',
                    data: seriesData,
                    symbol: 'none',
                    lineStyle: { width: 2, color: '#3b82f6' }, // Blue accent
                    areaStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
                            { offset: 1, color: 'rgba(59, 130, 246, 0)' }
                        ])
                    },
                    animation: false,
                    markPoint: {
                        data: this.showMarkers ? this.markers.map((m, idx) => ({
                            name: `Marker ${idx + 1}`,
                            coord: [parseFloat(m.frequency), parseFloat(m.power) + (unitMode === 'dbm' ? offset : 0)],
                            value: m.power,
                            symbol: 'triangle',
                            symbolSize: 12,
                            symbolRotate: 180,
                            itemStyle: { color: this.markerColors[idx % this.markerColors.length] },
                            label: { show: true, formatter: `${idx + 1}`, position: 'top', color: this.theme === 'dark' ? '#fff' : '#000' }
                        })) : [],
                        animation: false
                    }
                }];

                // Add lower scale line if in fixed mode
                if (this.lowerScaleMode === 'fixed') {
                    config.series.push({
                        type: 'line',
                        data: [[minX, this.fixedLowerScale + (unitMode === 'dbm' ? offset : 0)], [maxX, this.fixedLowerScale + (unitMode === 'dbm' ? offset : 0)]],
                        symbol: 'none',
                        lineStyle: { color: '#ef4444', width: 1, type: 'dashed' },
                        animation: false,
                        silent: true
                    });
                }

                this.chart.setOption(config, { notMerge: true });
            } catch (error) {
                console.error('Error updating chart:', error);
            }
        },
        toggleOptions() {
            this.isSidebarCollapsed = !this.isSidebarCollapsed;
            // Save state to cookie
            this.setCookie('isSidebarCollapsed', this.isSidebarCollapsed);
            
            // Resize chart after animation completes
            setTimeout(() => {
                if (this.chart) {
                    this.chart.resize();
                }
                // Also resize waterfall chart
                if (this.waterfallChart) {
                    Plotly.Plots.resize('waterfallChart');
                }
            }, 300);
        },
        async fetchData() {
            try {
                console.log('fetchData called, viewMode:', this.viewMode);
                // Only update waterfall data if not in spectrum-only mode
                if (this.viewMode !== 'spectrum') {
                    // Ensure waterfall is initialized
                    if (!this.waterfallChart) {
                        await this.initWaterfallChart();
                    }
                    
                    if (this.selectedData) {
                        const selectedService = this.subservices.find(s => s.band_number === this.selectedSubservice);
                        if (selectedService) {
                            await this.updateWaterfallData(selectedService.start_freq, selectedService.stop_freq);
                        } else {
                            await this.updateWaterfallData();
                        }
                    }
                }
            } catch (error) {
                console.error('Error fetching spectrum data:', error);
            }
        },
        getTimeRange() {
            if (this.timeRangeMode === 'custom') {
                return this.customTimeRange;
            }
            return this.timeRangeMode;
        },
        applyCustomTimeRange() {
            if (this.customTimeRange) {
                this.fetchData();
            }
        },
        selectLog(item) {
            if (!item || !item.filename) return;
            if (item.date) {
                this.selectedDate = item.date;
            }
            this.selectedDataFilename = item.filename;
            this.selectedData = item;
            const svc = this.selectedSubservice ? this.subservices.find(s => s.band_number === this.selectedSubservice) : (this.subservices[0] || null);
            const startFreq = svc ? svc.start_freq : null;
            const stopFreq = svc ? svc.stop_freq : null;
            this.loadSpectrumData(item.filename, startFreq, stopFreq);
        },

        async applyFilter() {
            this.error = null;
            try {
                console.log('Applying filter for month:', this.selectedMonth);
                // Fetch new data for the selected date
                await this.loadAllData();
            } catch (error) {
                console.error('Error applying filter:', error);
                this.error = 'Failed to filter data: ' + error.message;
                this.filteredData = [];
                this.selectedData = null;
            }
        },

        async handleDatePickerChange() {
            const dateStr = String(this.selectedDate || '').trim();
            if (!/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) return;

            const nextMonth = dateStr.slice(0, 7);
            const prevMonth = String(this.selectedMonth || '').trim();
            this.selectedMonth = nextMonth;

            if (nextMonth !== prevMonth) {
                await this.applyFilter();
                return;
            }

            await this.handleDateChange();
        },
        formatDate(timestamp) {
            return new Date(timestamp).toLocaleTimeString();
        },
        exportChart() {
            const dataUrl = this.spectrumChart.getDataURL();
            const link = document.createElement('a');
            link.href = dataUrl;
            link.download = 'spectrum-analysis.png';
            link.click();
        },
        toggleFullscreen() {
            const element = document.getElementById('spectrumChart');
            if (element.requestFullscreen) {
                element.requestFullscreen();
            }
        },
        dismissAlert(alertId) {
            const alert = this.alerts.find(a => a.id === alertId);
            if (alert) {
                alert.dismissed = true;
            }
        },
        async saveDeviceConfig() {
            try {
                await axios.post('/api/devices/config', this.deviceConfig);
                this.fetchData();
            } catch (error) {
                console.error('Error saving device config:', error);
            }
        },
        async saveAlertRule() {
            try {
                await axios.post('/api/alerts/rules', this.alertRule);
                this.alertRules.push({...this.alertRule});
                this.alertRule = {
                    name: '',
                    condition: 'power_above',
                    threshold: 0,
                    severity: 'low'
                };
            } catch (error) {
                console.error('Error saving alert rule:', error);
            }
        },
        async deleteRule(ruleId) {
            try {
                await axios.delete(`/api/alerts/rules/${ruleId}`);
                this.alertRules = this.alertRules.filter(rule => rule.id !== ruleId);
            } catch (error) {
                console.error('Error deleting alert rule:', error);
            }
        },
        async savePreferences() {
            try {
                try {
                    await axios.post('/api/preferences', this.preferences);
                } catch (e) {}

                try {
                    localStorage.setItem('preferences', JSON.stringify(this.preferences));
                    localStorage.setItem('user_prefs', JSON.stringify(this.preferences));
                } catch (e) {}

                this.applyTheme(this.preferences && this.preferences.theme);
            } catch (error) {
                console.error('Error saving preferences:', error);
            }
        },
        loadPreferences() {
            let merged = { ...(this.preferences || {}) };
            try {
                const savedPreferences = localStorage.getItem('preferences');
                if (savedPreferences) merged = { ...merged, ...JSON.parse(savedPreferences) };
            } catch (e) {}
            try {
                const savedUserPrefs = localStorage.getItem('user_prefs');
                if (savedUserPrefs) merged = { ...merged, ...JSON.parse(savedUserPrefs) };
            } catch (e) {}
            this.preferences = merged;
            this.applyTheme(this.getStoredThemePreference());
        },

        initThemeToggle() {
            this.applyTheme(this.getStoredThemePreference());
        },
        getStoredThemePreference() {
            try {
                // Priority 1: Direct monsfer_theme setting (used by layout.html and toggleTheme)
                const stored = localStorage.getItem('monsfer_theme');
                if (stored === 'light' || stored === 'dark') return stored;
            } catch (e) {}
            
            try {
                // Priority 2: user_prefs fallback
                const storedPref = localStorage.getItem('user_prefs');
                if (storedPref) {
                    const parsed = JSON.parse(storedPref);
                    const pref = parsed && typeof parsed.theme === 'string' ? parsed.theme : null;
                    if (pref === 'light' || pref === 'dark') return pref;
                }
            } catch (e) {}
            
            // Priority 3: Component data preference
            const current = this.preferences && typeof this.preferences.theme === 'string' ? this.preferences.theme : null;
            if (current === 'light' || current === 'dark') return current;
            
            return 'dark'; // Default
        },
        applyTheme(themePreference) {
            const pref = (themePreference === 'light' || themePreference === 'dark' || themePreference === 'system')
                ? themePreference
                : 'dark';

            let resolved = pref;
            if (pref === 'system') {
                try {
                    resolved = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
                } catch (e) {
                    resolved = 'dark';
                }
            }

            this.theme = resolved;
            if (!this.preferences) this.preferences = { theme: pref, updateInterval: 5, defaultView: 'spectrum' };
            if (this.preferences.theme !== pref) this.preferences.theme = pref;

            try {
                document.documentElement.setAttribute('data-theme', resolved);
            } catch (e) {}
            try {
                localStorage.setItem('monsfer_theme', resolved);
            } catch (e) {}

            try {
                localStorage.setItem('user_prefs', JSON.stringify(this.preferences));
                localStorage.setItem('preferences', JSON.stringify(this.preferences));
            } catch (e) {}
        },
        toggleTheme() {
            const next = this.theme === 'dark' ? 'light' : 'dark';
            if (this.preferences) this.preferences.theme = next;
            this.applyTheme(next);
        },
        
        updateSystemInfo() {
            this.systemInfo.activeDevices = this.devices.filter(d => d.status === 'active').length;
            this.systemInfo.totalAlerts = this.alerts.length;
            this.systemInfo.lastUpdate = new Date().toLocaleString();
        },
        async loadSystemInfo() {
            if (this.isFetchingSystemInfo) return;
            this.isFetchingSystemInfo = true;
            try {
                const resp = await fetch('/api/system/info', {
                    method: 'GET',
                    headers: { 'Accept': 'application/json' },
                    credentials: 'same-origin'
                });
                if (!resp.ok) {
                    console.warn('System info API returned non-OK status:', resp.status, resp.statusText);
                    return;
                }
                const data = await resp.json();
                this.systemInfo = { ...this.systemInfo, ...data };
            } catch (error) {
                console.warn('Error loading system info (non-blocking):', error);
            } finally {
                this.isFetchingSystemInfo = false;
            }
        },
        async refreshDashboard() {
            try {
                const resp = await fetch('/api/system/dashboard');
                if (!resp.ok) {
                    console.warn('Dashboard API returned non-OK status:', resp.status, resp.statusText);
                    return;
                }
                const data = await resp.json();
                const alerts = [];
                const sites = data.sites || {};
                const now = Date.now();
                Object.keys(sites).forEach(siteName => {
                    const s = sites[siteName] || {};
                    const deviceStatus = String(s.deviceStatus || '').toUpperCase();
                    const lastUpdate = s.lastUpdate ? new Date(s.lastUpdate).getTime() : now;
                    const cpuTemp = typeof s.cpuTemp === 'number' ? s.cpuTemp : null;
                    const freeStorage = typeof s.freeStorage === 'number' ? s.freeStorage : null;
                    const totalStorage = typeof s.totalStorage === 'number' ? s.totalStorage : null;
                    const storageUsedPct = totalStorage && totalStorage > 0 ? Math.max(0, Math.min(100, (1 - (freeStorage / totalStorage)) * 100)) : null;
                    if (deviceStatus === 'OFFLINE' || (now - lastUpdate) >= (60 * 60 * 1000)) {
                        alerts.push({
                            id: `offline_${siteName}`,
                            site: siteName,
                            type: 'offline',
                            message: `OFFLINE ≥60m (${siteName})`,
                            dismissed: false
                        });
                    }
                    if (cpuTemp !== null && cpuTemp > 55) {
                        alerts.push({
                            id: `temp_${siteName}`,
                            site: siteName,
                            type: 'cpu_temp',
                            message: `cpuTemp ${cpuTemp.toFixed(1)}°C > 55 (${siteName})`,
                            dismissed: false
                        });
                    }
                    if (storageUsedPct !== null && storageUsedPct > 95) {
                        alerts.push({
                            id: `storage_${siteName}`,
                            site: siteName,
                            type: 'storage',
                            message: `Storage ${storageUsedPct.toFixed(1)}% > 95% (${siteName})`,
                            dismissed: false
                        });
                    }
                });
                this.alerts = alerts;
                this.systemInfo.totalAlerts = this.alerts.length;
            } catch (e) {
                console.warn('Error refreshing dashboard status:', e);
            }
        },
        async loadSubservices() {
            try {
                const response = await fetch('/api/subservices', {
                    method: 'GET',
                    headers: { 'Accept': 'application/json' },
                    credentials: 'same-origin'
                });
                if (!response.ok) {
                    console.warn('Subservices API returned non-OK status:', response.status, response.statusText);
                    this.subservices = [];
                    return;
                }
                const data = await response.json();
                this.subservices = Array.isArray(data.subservices) ? data.subservices : [];
            } catch (error) {
                console.warn('Error loading subservices (non-blocking):', error);
                this.subservices = [];
            }
        },
        
        selectSubservice(service) {
            this.selectedSubservice = this.selectedSubservice === service.band_number ? null : service.band_number;
        },

        // This method is called from monitoring/index.html to zoom into a subservice
        zoomToSubservice(sub) {
            if (!sub) return;
            console.log("Zooming to subservice (app.js):", sub.name, sub.start_freq, sub.stop_freq);
            this.selectedSubservice = sub.band_number;

            // Update Spectrum Chart (ECharts)
            if (this.chart) {
                this.chart.setOption({
                    xAxis: {
                        min: sub.start_freq,
                        max: sub.stop_freq
                    },
                    dataZoom: [{
                        startValue: sub.start_freq,
                        endValue: sub.stop_freq
                    }]
                });
            } else {
                console.warn("Spectrum chart instance not found!");
            }

            // Update Waterfall Chart (Plotly)
            const wfEl = document.getElementById('waterfallChart');
            if (wfEl && window.Plotly) {
                try {
                    Plotly.relayout(wfEl, {
                        'xaxis.range': [sub.start_freq, sub.stop_freq]
                    });
                } catch (e) {
                    console.error("Error updating waterfall:", e);
                }
            }
        },

        showSpectrum(service) {
            // Select the subservice
            this.selectedSubservice = service.band_number;
            
            // If we have a selected data item, load its spectrum
            if (this.selectedData) {
                this.loadSpectrumData(
                    this.selectedData.filename,
                    service.start_freq,
                    service.stop_freq
                );
            }
            
            if (this.viewMode !== 'spectrum') {
                this.updateWaterfallData(service.start_freq, service.stop_freq);
            }
        },

        // Filter methods
        applyFilters() {
            this.error = null;
            try {
                const min = this.freqRange ? this.freqRange.min : null;
                const max = this.freqRange ? this.freqRange.max : null;
                const hasMin = isFinite(parseFloat(min));
                const hasMax = isFinite(parseFloat(max));
                if ((hasMin && hasMax) && parseFloat(min) >= parseFloat(max)) {
                    this.error = 'Invalid frequency range: Min must be < Max';
                    return;
                }

                const filename = (this.selectedDataFilename || (this.selectedData && this.selectedData.filename) || (this.filteredData && this.filteredData[0] && this.filteredData[0].filename) || null);
                if (!filename) return;

                const startFreq = hasMin ? parseFloat(min) : null;
                const stopFreq = hasMax ? parseFloat(max) : null;
                this.loadSpectrumData(filename, startFreq, stopFreq);

                if (this.viewMode !== 'spectrum' && startFreq !== null && stopFreq !== null) {
                    this.updateWaterfallData(startFreq, stopFreq);
                }
            } catch (error) {
                console.error('Error applying filters:', error);
                this.error = 'Failed to apply filters: ' + error.message;
            }
        },
        
        resetFilters() {
            // Reset to default values
            this.freqRange = { ...this.defaultFilters.freqRange };
            this.timeRange = this.defaultFilters.timeRange;
            this.viewMode = this.defaultFilters.viewMode;
            
            // Apply reset filters
            this.applyFilters();
        },
        updateChartConfig() {
            if (this.currentData) {
                this.updateChart(this.currentData);
            }
            if (this.viewMode !== 'spectrum' && this.waterfallChart) {
                this.updateWaterfallOptions();
            }
        },
        snapPointToSpectrum(freq) {
            if (this.currentData && this.currentData.x && this.currentData.y && this.currentData.x.length > 0) {
                const xArr = this.currentData.x;
                const yArr = this.currentData.y;
                let nearestIdx = 0;
                let minDiff = Infinity;
                for (let j = 0; j < xArr.length; j++) {
                    const diff = Math.abs(xArr[j] - freq);
                    if (diff < minDiff) {
                        minDiff = diff;
                        nearestIdx = j;
                    }
                }
                return {
                    frequency: xArr[nearestIdx],
                    power: yArr[nearestIdx]
                };
            }
            return {
                frequency: freq,
                power: 0
            };
        },
        // Marker methods
        addMarkerManual() {
            this.addMarker();
        },
        addMarker() {
            if (!this.chart || !this.chartInitialized) return;

            try {
                // Get current mouse position from chart
                const pos = this.chart.getOption();
                const xAxis = pos.xAxis[0];

                // Use middle of current view if no specific position
                const freq = (xAxis.min + xAxis.max) / 2;
                const snapped = this.snapPointToSpectrum(freq);

                this.markers.push({
                    id: 'm-' + Date.now() + '-' + Math.floor(Math.random() * 1000),
                    frequency: snapped.frequency.toFixed(3),
                    power: snapped.power.toFixed(2)
                });

                this.updateChartMarkers();
            } catch (error) {
                console.error('Error adding marker:', error);
                this.error = 'Failed to add marker';
            }
        },

        removeMarker(id) {
            // Remove by ID if possible, otherwise fallback to index if passed as number (legacy)
            if (typeof id === 'number' && id < this.markers.length && !this.markers[id]?.id) {
                this.markers.splice(id, 1);
            } else {
                this.markers = this.markers.filter(m => m.id !== id);
            }
            this.updateChartMarkers();
        },

        clearMarkers() {
            this.markers = [];
            this.updateChartMarkers();
        },

        updateChartMarkers() {
            if (!this.chart || !this.chartInitialized) return;

            try {
                // Update markPoint data
                const markerData = this.markers.map((marker, idx) => {
                    let color;
                    if (this.markerColorMode === 'default') {
                        color = marker.label && marker.label.includes('Δ') ? '#00FF00' : '#FF0000';
                    } else {
                        color = this.markerColors[idx % this.markerColors.length];
                    }
                    return {
                        name: `Marker ${idx + 1}`,
                        coord: [parseFloat(marker.frequency), parseFloat(marker.power)],
                        value: marker.power,
                        symbol: 'triangle',
                        symbolSize: 12,
                        symbolRotate: 180,
                        symbolOffset: [0, -6],
                        label: {
                            show: true,
                            formatter: `${idx + 1}`,
                            position: 'top',
                            distance: 5,
                            fontSize: 10,
                            color: '#000000'
                        },
                        itemStyle: {
                            color: color,
                            borderColor: '#000000',
                            borderWidth: 1
                        },
                        draggable: true
                    };
                });

                // Update markLine data (Vertical Line)
                const lineData = this.markers.map((marker, idx) => {
                    let color;
                    if (this.markerColorMode === 'default') {
                        color = marker.label && marker.label.includes('Δ') ? '#00FF00' : '#FF0000';
                    } else {
                        color = this.markerColors[idx % this.markerColors.length];
                    }
                    return {
                        xAxis: parseFloat(marker.frequency),
                        lineStyle: {
                            color: color,
                            type: 'dashed',
                            width: 1
                        },
                        label: { show: false }
                    };
                });

                this.chart.setOption({
                    series: [{
                        markPoint: {
                            symbol: 'triangle',
                            symbolSize: 12,
                            symbolRotate: 180,
                            symbolOffset: [0, -6],
                            data: this.showMarkers ? markerData : [],
                            animation: false
                        },
                        markLine: {
                            symbol: 'none',
                            data: this.showMarkers ? lineData : [],
                            animation: false,
                            silent: true
                        }
                    }]
                }, { notMerge: false, lazyUpdate: true });
            } catch (error) {
                console.error('Error updating markers:', error);
            }
        },
        setViewMode(mode) {
            this.viewMode = mode;
            
            // Always ensure waterfall chart is initialized
            if (!this.waterfallChart) {
                this.initWaterfallChart();
            }
            
            // Update waterfall data if not in spectrum-only mode
            if (mode !== 'spectrum') {
                const selectedService = this.subservices.find(s => s.band_number === this.selectedSubservice);
                if (selectedService) {
                    this.updateWaterfallData(selectedService.start_freq, selectedService.stop_freq);
                } else {
                    this.updateWaterfallData();
                }
                // Force a resize after the DOM updates so Plotly gets a non-zero container size
                this.$nextTick(() => {
                    try {
                        const el = document.getElementById('waterfallChart');
                        if (el) {
                            const parent = el.parentElement;
                            const width = (parent && (parent.clientWidth || parent.offsetWidth)) || el.clientWidth || 600;
                            const height = (parent && (parent.clientHeight || parent.offsetHeight)) || el.clientHeight || 300;
                            Plotly.relayout(el, { width, height, autosize: true });
                            Plotly.Plots.resize(el);
                        }
                    } catch (e) {
                        console.warn('Forced resize after viewMode change failed:', e);
                    }
                });
            }
            
            // Update both charts
            if (this.currentData) {
                this.updateChart(this.currentData);
            }
        },

        showGrid() {
            this.showGrid = !this.showGrid;
            if (this.viewMode === 'waterfall') {
                this.updateWaterfallOptions();
            }
            this.updateChart(this.currentData);
        },

        showMarkers() {
            this.showMarkers = !this.showMarkers;
            if (this.viewMode === 'waterfall') {
                this.updateWaterfallOptions();
            }
            this.updateChart(this.currentData);
        },

        autoScale() {
            this.autoScale = !this.autoScale;
            this.updateChart(this.currentData);
        },

        addMarkerAtPoint(point) {
            if (!point) return;
            
            // Check if we've reached the maximum number of markers
            if (this.markers.length >= this.maxMarkers) {
                alert(`Maximum number of markers (${this.maxMarkers}) reached`);
                return;
            }
            
            console.log('Adding marker at point:', point);
            const snapped = this.snapPointToSpectrum(point[0]);
            this.markers.push({
                id: 'm-' + Date.now() + '-' + Math.floor(Math.random() * 1000),
                frequency: snapped.frequency.toFixed(3),
                power: snapped.power.toFixed(2)
            });
            
            this.updateChartMarkers();
            // Force update the chart data
            if (this.currentData) {
                this.updateChart(this.currentData);
            }
        },

        addDeltaMarkerAtPoint(point) {
            if (!point || this.markers.length === 0) return;
            
            const lastMarker = this.markers[this.markers.length - 1];
            const snapped = this.snapPointToSpectrum(point[0]);
            const deltaFreq = (snapped.frequency - parseFloat(lastMarker.frequency)).toFixed(3);
            const deltaPower = (snapped.power - parseFloat(lastMarker.power)).toFixed(2);
            
            console.log('Adding delta marker at point:', point);
            this.markers.push({
                id: 'm-' + Date.now() + '-' + Math.floor(Math.random() * 1000),
                frequency: snapped.frequency.toFixed(3),
                power: snapped.power.toFixed(2),
                label: `ΔF: ${deltaFreq}MHz, ΔP: ${deltaPower}dB`
            });
            
            this.updateChartMarkers();
            // Force update the chart data
            if (this.currentData) {
                this.updateChart(this.currentData);
            }
        },

        // Helper method to convert time range to milliseconds
        getTimeRangeInMs() {
            const timeRange = this.getTimeRange();
            switch(timeRange) {
                case '1h': return 60 * 60 * 1000;
                case '12h': return 12 * 60 * 60 * 1000;
                case '24h': return 24 * 60 * 60 * 1000;
                case '7d': return 7 * 24 * 60 * 60 * 1000;
                default: return 60 * 60 * 1000; // Default to 1 hour
            }
        },

        handleResize: debounce(function() {
            // Get container dimensions for both charts
            const spectrumElement = document.getElementById('spectrumChart');
            const waterfallElement = document.getElementById('waterfallChart');
            
            if (this.chart && spectrumElement) {
                const container = spectrumElement.parentElement;
                const width = container.offsetWidth;
                const height = container.offsetHeight;
                
                this.chart.resize({
                    width: width,
                    height: height
                });
            }
            
            if (this.waterfallChart && waterfallElement) {
                const container = waterfallElement.parentElement;
                const width = container.offsetWidth;
                const height = container.offsetHeight;
                
                Plotly.relayout('waterfallChart', {
                    width: width,
                    height: height,
                    autosize: true
                });
            }

            // Auto-select first items when switching to mobile view
            if (window.innerWidth < 768) {
                if (this.filteredData.length > 0 && !this.selectedData) {
                    this.selectedData = this.filteredData[0];
                    if (this.selectedData && this.selectedData.date) {
                        this.selectedDate = this.selectedData.date;
                    }
                    this.loadSpectrumData(this.selectedData.filename);
                }
                if (this.subservices.length > 0 && !this.selectedSubservice) {
                    this.selectedSubservice = this.subservices[0].band_number;
                    this.showSpectrum(this.subservices[0]);
                }
            }
        }, 250),

        prevDate() {
            const current = String(this.selectedDate || '').trim();
            const base = /^\d{4}-\d{2}-\d{2}$/.test(current) ? new Date(`${current}T00:00:00`) : new Date();
            base.setDate(base.getDate() - 1);
            this.selectedDate = base.toISOString().slice(0, 10);
            this.handleDatePickerChange();
        },

        nextDate() {
            const current = String(this.selectedDate || '').trim();
            const base = /^\d{4}-\d{2}-\d{2}$/.test(current) ? new Date(`${current}T00:00:00`) : new Date();
            base.setDate(base.getDate() + 1);
            this.selectedDate = base.toISOString().slice(0, 10);
            this.handleDatePickerChange();
        },

        // Add cookie handling methods
        setCookie(name, value, days = 365) {
            const date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            const expires = "expires=" + date.toUTCString();
            document.cookie = name + "=" + value + ";" + expires + ";path=/";
        },

        getCookie(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
            return null;
        },

        // Save scale settings to cookies
        saveScaleSettings() {
            this.setCookie('lowerScaleMode', this.lowerScaleMode);
            this.setCookie('upperScaleMode', this.upperScaleMode);
            this.setCookie('fixedLowerScale', this.fixedLowerScale);
            this.setCookie('fixedUpperScale', this.fixedUpperScale);
            // Also save last valid values
            this.setCookie('lastValidLowerScale', this.lastValidLowerScale);
            this.setCookie('lastValidUpperScale', this.lastValidUpperScale);
        },

        // Load scale settings from cookies
        loadScaleSettings() {
            const lowerScaleMode = this.getCookie('lowerScaleMode');
            const upperScaleMode = this.getCookie('upperScaleMode');
            const fixedLowerScale = this.getCookie('fixedLowerScale');
            const fixedUpperScale = this.getCookie('fixedUpperScale');
            const lastValidLowerScale = this.getCookie('lastValidLowerScale');
            const lastValidUpperScale = this.getCookie('lastValidUpperScale');

            if (lowerScaleMode) this.lowerScaleMode = lowerScaleMode;
            if (upperScaleMode) this.upperScaleMode = upperScaleMode;
            if (fixedLowerScale) {
                this.fixedLowerScale = parseInt(fixedLowerScale);
                this.lastValidLowerScale = parseInt(fixedLowerScale);
            }
            if (fixedUpperScale) {
                this.fixedUpperScale = parseInt(fixedUpperScale);
                this.lastValidUpperScale = parseInt(fixedUpperScale);
            }
            if (lastValidLowerScale) this.lastValidLowerScale = parseInt(lastValidLowerScale);
            if (lastValidUpperScale) this.lastValidUpperScale = parseInt(lastValidUpperScale);
        },

        applyScaleSettings() {
            if (this.viewMode !== 'spectrum' && this.currentData) {
                try {
                    // Validate scale values
                    if (this.upperScaleMode === 'fixed' && this.lowerScaleMode === 'fixed') {
                        if (this.fixedUpperScale <= this.fixedLowerScale) {
                            // Restore last valid values
                            this.fixedUpperScale = this.lastValidUpperScale;
                            this.fixedLowerScale = this.lastValidLowerScale;
                            return;
                        }
                    }

                    // Show loading state
                    this.isWaterfallLoading = true;
                    
                    // Get the current waterfall chart data
                    const plotlyData = document.getElementById('waterfallChart').data;
                    if (!plotlyData || !plotlyData[0]) {
                        console.warn('No waterfall data available');
                        return;
                    }

                    const waterfallData = {
                        frequencies: plotlyData[0].x,
                        times: plotlyData[0].y,
                        levels: plotlyData[0].z
                    };

                    // Update the waterfall chart with current data and new scale settings
                    this.updateWaterfallChart(
                        waterfallData,
                        this.selectedData.start_freq,
                        this.selectedData.stop_freq
                    );
                    
                    // Save settings to cookies after successful update
                    this.saveScaleSettings();
                    
                    console.log('Scale settings applied and saved successfully');
                } catch (error) {
                    console.error('Error applying scale settings:', error);
                    this.error = 'Failed to apply scale settings';
                } finally {
                    this.isWaterfallLoading = false;
                }
            }
        }
    },
    watch: {
        viewMode: {
            handler(newValue) {
                if (this.isMonitoringPage) {
                    console.log('View mode changed to:', newValue);
                    if (newValue !== 'spectrum') {
                        this.initWaterfallIfNeeded();
                        // Update waterfall data only when view mode changes
                        const selectedService = this.subservices.find(s => s.band_number === this.selectedSubservice);
                        if (selectedService) {
                            this.updateWaterfallData(selectedService.start_freq, selectedService.stop_freq);
                        } else {
                            this.updateWaterfallData();
                        }

                        // Force Plotly to recalculate size even if data has not loaded yet
                        this.$nextTick(() => {
                            const wfEl = document.getElementById('waterfallChart');
                            if (wfEl && typeof Plotly !== 'undefined') {
                                const container = wfEl.parentElement;
                                const width = (container && (container.clientWidth || container.offsetWidth)) || wfEl.clientWidth || 600;
                                const height = (container && (container.clientHeight || container.offsetHeight)) || wfEl.clientHeight || 300;
                                try {
                                    Plotly.relayout('waterfallChart', { width, height, autosize: true });
                                    Plotly.Plots.resize('waterfallChart');
                                    console.log('Forced waterfall resize after viewMode change:', { width, height });
                                } catch (e) {
                                    console.warn('Failed to resize waterfall after viewMode change:', e);
                                }
                            }
                        });
                    }
                }
            },
            immediate: false
        },
        showGrid() {
            this.updateChartConfig();
        },
        showMarkers() {
            this.updateChartConfig();
        },
        autoScale() {
            this.updateChartConfig();
        },

        timeRangeMode: {
            handler(newValue) {
                if (this.isMonitoringPage) {
                    console.log('Time range changed to:', newValue);
                    if (this.viewMode !== 'spectrum') {
                        // Update waterfall data when time range changes
                        const selectedService = this.subservices.find(s => s.band_number === this.selectedSubservice);
                        if (selectedService) {
                            this.updateWaterfallData(selectedService.start_freq, selectedService.stop_freq);
                        } else {
                            this.updateWaterfallData();
                        }
                    }
                }
            },
            immediate: true
        },
        fixedUpperScale: {
            handler(newValue) {
                // Convert to number to ensure proper comparison
                const upperValue = Number(newValue);
                const lowerValue = Number(this.fixedLowerScale);
                
                if (this.lowerScaleMode === 'fixed' && upperValue <= lowerValue) {
                    this.error = 'Upper scale must be higher than lower scale';
                    // Restore last valid value
                    this.fixedUpperScale = this.lastValidUpperScale;
                } else {
                    // Store valid value
                    this.lastValidUpperScale = upperValue;
                }
            }
        },
        fixedLowerScale: {
            handler(newValue) {
                // Convert to number to ensure proper comparison
                const lowerValue = Number(newValue);
                const upperValue = Number(this.fixedUpperScale);
                
                if (this.upperScaleMode === 'fixed' && upperValue <= lowerValue) {
                    this.error = 'Lower scale must be lower than upper scale';
                    // Restore last valid value
                    this.fixedLowerScale = this.lastValidLowerScale;
                } else {
                    // Store valid value
                    this.lastValidLowerScale = lowerValue;
                    // Update chart to show new lower scale line
                    if (this.currentData && this.lowerScaleMode === 'fixed') {
                        this.updateChart(this.currentData);
                    }
                }
            }
        },
        lowerScaleMode: {
            handler(newValue) {
                // Update chart to show/hide lower scale line
                if (this.currentData) {
                    this.updateChart(this.currentData);
                }
            }
        }
    }
});

// Add debounce utility function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const context = this;
        const later = () => {
            clearTimeout(timeout);
            // Preserve Vue instance context
            func.apply(context, args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
