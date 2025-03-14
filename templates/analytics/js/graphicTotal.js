function loadChartData() {
  const filterProdLine = document.getElementById("filter_prod_line").value;
  const startDate = document.getElementById("start_date").value;
  const endDate = document.getElementById("end_date").value;

  const url = new URL("/api/get_corrective_stats", window.location.origin);
  if (filterProdLine)
    url.searchParams.append("filter_prod_line", filterProdLine);
  if (startDate) url.searchParams.append("start_date", startDate);
  if (endDate) url.searchParams.append("end_date", endDate);

  fetch(url)
    .then((response) => response.json())
    .then((data) => {
      console.log("Dados recebidos:", data);
      if (data.error) {
        alert(data.error);
      } else {
        renderChart(data, filterProdLine);
      }
    })
    .catch((error) => console.error("Erro ao carregar dados:", error));
}

function renderChart(data, filterProdLine) {
  if (!data || data.length === 0) {
    document.getElementById("totalState").innerHTML =
      "<div class='text-center'>Sem registos</div>";
    return;
  }

  const titleText = filterProdLine
    ? `Pedidos de Manutenção por Estado - ${filterProdLine}`
    : "Pedidos de Manutenção por Estado";

  Highcharts.chart("totalState", {
    chart: { type: "pie" },
    title: { text: titleText },
    tooltip: {
      pointFormat: "{series.name}: <b>{point.percentage:.1f}%</b>",
    },
    series: [
      {
        name: "Pedidos",
        data: data.map((item) => ({
          name: item.estado,
          y: item.count,
        })),
        colorByPoint: true,
        dataLabels: {
          enabled: true,
          format: "{point.name}: {point.y}",
          style: {
            fontWeight: "bold",
            color: "black",
          },
          inside: true,
        },
      },
    ],
  });
}
