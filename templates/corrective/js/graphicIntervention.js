function loadInterventionChartData() {
  const filterLine = document.getElementById("filter_prod_line").value;
  const filterArea = document.getElementById("filter_area").value;
  const startDatetime = document.getElementById("start_date").value;
  const endDatetime = document.getElementById("end_date").value;

  const url = new URL("/api/get_intervention_stats", window.location.origin);
  if (filterLine) url.searchParams.append("filter_line", filterLine);
  if (filterArea) url.searchParams.append("filter_area", filterArea);
  if (startDatetime) url.searchParams.append("start_datetime", startDatetime);
  if (endDatetime) url.searchParams.append("end_datetime", endDatetime);

  fetch(url)
    .then((response) => response.json())
    .then((data) => {
      if (data.error) {
        alert(data.error);
      } else {
        renderInterventionChart(data);
      }
    })
    .catch((error) =>
      console.error("Erro ao carregar dados do gráfico de intervenção:", error)
    );
}

function renderInterventionChart(data) {
  if (!data || data.length === 0) {
    document.getElementById("interventionChart").innerHTML =
      "<div class='text-center'>Sem registos</div>";
    return;
  }

  const categories = data.map((item) => item.prod_line);
  const downtimeSeries = data.map((item) => item.downtime);
  const techTimeSeries = data.map((item) => item.technician_time);

  Highcharts.chart("interventionChart", {
    chart: { type: "column" },
    title: { text: "Downtime (min) vs Tempo de Intervenção por Linha" },
    xAxis: {
      categories: categories,
      title: { text: "Linha de Produção" },
    },
    yAxis: {
      min: 0,
      title: { text: "Tempo (min)" },
    },
    tooltip: { shared: true, valueSuffix: " min" },
    series: [
      { name: "Downtime", data: downtimeSeries, color: "red" },
      { name: "Tempo de Intervenção", data: techTimeSeries, color: "#434348" },
    ],
  });
}

function clearInterventionFilters() {
  document.getElementById("filter_prod_line").value = "";
  document.getElementById("filter_area").value = "";
  document.getElementById("start_date").value = "";
  document.getElementById("end_date").value = "";
  loadInterventionChartData();
}
