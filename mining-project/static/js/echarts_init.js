window.renderEChart = function(domId, options) {
    const dom = document.getElementById(domId);
    const chart = echarts.init(dom);
    chart.setOption(options);
    return chart;
};