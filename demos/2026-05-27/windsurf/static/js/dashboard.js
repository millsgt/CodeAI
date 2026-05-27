function updateChart(selectorId, chartType) {
    const select = document.getElementById(selectorId);
    if (!select || !select.value) {
        return;
    }

    const params = new URLSearchParams(window.location.search);
    params.set(chartType, select.value);
    window.location.search = params.toString();
}

document.addEventListener('DOMContentLoaded', () => {
    const histogramSelect = document.getElementById('histogramColumn');
    const barSelect = document.getElementById('barColumn');

    if (histogramSelect) {
        histogramSelect.addEventListener('change', () => updateChart('histogramColumn', 'histogram_column'));
    }

    if (barSelect) {
        barSelect.addEventListener('change', () => updateChart('barColumn', 'bar_column'));
    }
});
