// Override the initWaterfallChart to ensure Plotly heatmap is initialized even with empty data
(function () {
  function getVm() {
    const el = document.getElementById('app');
    return el && el.__vue__ ? el.__vue__ : null;
  }

  function installOverride(vm) {
    if (!vm || typeof Plotly === 'undefined') return;

    vm.initWaterfallChart = function () {
      if (typeof Plotly === 'undefined') {
        console.error('Plotly is not defined. Waiting for Plotly to load...');
        window.addEventListener('plotlyReady', () => {
          console.log('Plotly is now ready, initializing waterfall chart (override)...');
          this.initWaterfallChart();
        });
        return;
      }

      try {
        const el = document.getElementById(this.waterfallChartId || 'waterfallChart');
        if (!el) {
          console.warn('Waterfall chart element not found');
          return;
        }

        const config = this.getWaterfallConfig ? this.getWaterfallConfig() : {
          data: { type: 'heatmap', colorscale: 'Jet' },
          layout: { xaxis: { title: 'Frequency' }, yaxis: { title: 'Time' } },
          config: { displayModeBar: false, responsive: true }
        };

        // Initialize with an empty heatmap so the chart renders even before data arrives
        const plotData = [{
          ...config.data,
          z: [],
          x: [],
          y: []
        }];

        const startFreq = this.selectedData && this.selectedData.start_freq != null ? this.selectedData.start_freq : null;
        const stopFreq = this.selectedData && this.selectedData.stop_freq != null ? this.selectedData.stop_freq : null;
        const now = new Date();
        const yMin = new Date(now.getTime() - (this.getTimeRangeInMs ? this.getTimeRangeInMs() : 3600000));
        const yMax = now;

        const layout = {
          ...config.layout,
          xaxis: {
            ...config.layout.xaxis,
            range: startFreq !== null && stopFreq !== null ? [startFreq, stopFreq] : undefined,
            autorange: true
          },
          yaxis: {
            ...config.layout.yaxis,
            range: [yMin, yMax],
            autorange: true
          }
        };

        Plotly.newPlot(el, plotData, layout, config.config);

        // Immediately try to resize to actual container size
        try {
          const parent = el.parentElement;
          const width = (parent && (parent.clientWidth || parent.offsetWidth)) || el.clientWidth || 600;
          const height = (parent && (parent.clientHeight || parent.offsetHeight)) || el.clientHeight || 300;
          Plotly.relayout(el, { width, height, autosize: true });
          Plotly.Plots.resize(el);
        } catch (e) {
          console.warn('Plotly resize after init failed:', e);
        }

        // Bind zoom synchronization
        el.on('plotly_relayout', (eventdata) => {
          if (this.chart && eventdata['xaxis.range[0]'] !== undefined) {
            const startFreq = eventdata['xaxis.range[0]'];
            const endFreq = eventdata['xaxis.range[1]'];

            const spectrumOption = this.chart.getOption();
            const xAxis = spectrumOption.xAxis[0];
            const totalRange = xAxis.max - xAxis.min;

            const startPercent = ((startFreq - xAxis.min) / totalRange) * 100;
            const endPercent = ((endFreq - xAxis.min) / totalRange) * 100;

            this.chart.dispatchAction({ type: 'dataZoom', start: startPercent, end: endPercent });
          }
        });

        this.waterfallChart = el;
        // Trigger a global resize to ensure any observers and handlers recompute sizes
        try { window.dispatchEvent(new Event('resize')); } catch (e) {}
        console.log('Waterfall chart (override) initialized successfully');
      } catch (error) {
        console.error('Error initializing waterfall chart (override):', error);
        setTimeout(() => {
          console.log('Attempting to reinitialize waterfall chart (override) after error...');
          this.initWaterfallChart();
        }, 1000);
      }
    };

    // If current view is waterfall, initialize immediately
    if (vm.viewMode === 'waterfall') {
      vm.$nextTick(() => vm.initWaterfallChart());
    }
  }

  function tryInstall() {
    const vm = getVm();
    if (vm && typeof Plotly !== 'undefined') {
      installOverride(vm);
    } else {
      setTimeout(tryInstall, 300);
    }
  }

  tryInstall();
})();