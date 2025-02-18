function loadAvariasPorTempoChart() {
  const filterLine = document.getElementById("filter_prod_line").value;
  const filterArea = document.getElementById("filter_area").value;
  const startDatetime = document.getElementById("start_date").value;
  const endDatetime = document.getElementById("end_date").value;

  const url = new URL("/api/avarias_por_tempo", window.location.origin);
  if (filterLine) url.searchParams.append("filter_line", filterLine);
  if (filterArea) url.searchParams.append("filter_area", filterArea);
  if (startDatetime) url.searchParams.append("start_datetime", startDatetime);
  if (endDatetime) url.searchParams.append("end_datetime", endDatetime);

  fetch(url)
    .then((response) => response.json())
    .then((data) => {
      console.log("Dados do gráfico de avarias:", data);
      if (data.error) {
        alert(data.error);
      } else {
        renderAvariasPorTempoChart(data);
      }
    })
    .catch((error) =>
      console.error("Erro ao carregar dados do gráfico de avarias:", error)
    );
}

function renderAvariasPorTempoChart(data) {
  if (!data || data.length === 0) {
    document.getElementById("avariasPorTempo").innerHTML =
      "<div class='text-center'>Sem registos</div>";
    return;
  }

  const seriesData = {};

  data.forEach((item) => {
    const key = `${item.TipoAvaria} - ${item.LinhaProducao}`;
    const date = `${item.Ano}-${String(item.Mes).padStart(2, "0")}-01`;

    if (!seriesData[key]) {
      seriesData[key] = [];
    }

    seriesData[key].push([new Date(date).getTime(), item.NumeroOcorrencias]);
  });

  const series = Object.keys(seriesData).map((key) => ({
    name: key,
    data: seriesData[key].sort((a, b) => a[0] - b[0]), // Ordena por data
  }));

  Highcharts.chart("avariasPorTempo", {
    chart: { type: "line" },
    title: { text: "Ocorrências de Avarias por Tipo ao Longo do Tempo" },
    xAxis: {
      type: "datetime",
      title: { text: "Tempo" },
    },
    yAxis: {
      title: { text: "Número de Ocorrências" },
    },
    series: series,
  });
}
