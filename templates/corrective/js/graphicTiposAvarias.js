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

  const productionLines = new Set();
  Object.keys(seriesData).forEach((key) => {
    const parts = key.split(" - ");
    if (parts.length > 1) {
      productionLines.add(parts[1]);
    }
  });
  const productionLinesArray = Array.from(productionLines);

  let dropdownHTML = "";
  if (productionLinesArray.length > 1) {
    dropdownHTML += `<div style="margin-bottom:10px;"><label for="lineSelector">Selecione a Linha: </label>`;
    dropdownHTML += `<select id="lineSelector" onchange="filterChartByLine()" class="form-control" style="width:200px; display:inline-block; margin-left:10px;">`;
    dropdownHTML += `<option value="all">Todas as Linhas</option>`;
    productionLinesArray.forEach((line) => {
      dropdownHTML += `<option value="${line}">${line}</option>`;
    });
    dropdownHTML += `</select></div>`;
  }

  const container = document.getElementById("avariasPorTempo");
  container.innerHTML =
    dropdownHTML +
    `<div id="chartContainerAvarias" style="min-height:400px;"></div>`;

  const allAvariasSeries = Object.keys(seriesData).map((key) => ({
    name: key,
    data: seriesData[key].sort((a, b) => a[0] - b[0]),
  }));

  container.dataset.allSeries = JSON.stringify(allAvariasSeries);

  renderAvariasChart(allAvariasSeries);
}

function renderAvariasChart(series) {
  Highcharts.chart("chartContainerAvarias", {
    chart: { type: "line" },
    title: { text: "Ocorrências de Avarias por Tipo ao Longo do Tempo" },
    xAxis: {
      type: "datetime",
      title: { text: "Tempo" },
    },
    yAxis: {
      title: { text: "Número de Ocorrências" },
    },
    tooltip: { shared: true },
    series: series,
  });
}

function filterChartByLine() {
  const selector = document.getElementById("lineSelector");
  const selectedLine = selector.value;
  const container = document.getElementById("avariasPorTempo");
  const allSeries = JSON.parse(container.dataset.allSeries || "[]");
  let filteredSeries;
  if (selectedLine === "all") {
    filteredSeries = allSeries;
  } else {
    filteredSeries = allSeries.filter((s) =>
      s.name.endsWith(" - " + selectedLine)
    );
  }
  renderAvariasChart(filteredSeries);
}
