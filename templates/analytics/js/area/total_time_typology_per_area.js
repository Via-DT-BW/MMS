function loadParetoChartTipologia() {
  let filters = {
    filter_area: $("#filter_area").val(),
    start_date: $("#start_date").val(),
    end_date: $("#end_date").val(),
    filter_shift: $("#filter_shift").val(),
  };

  $.ajax({
    url: "/api/total_time_tipologia_per_area",
    method: "GET",
    data: filters,
    success: function (data) {
      if (!data.length) {
        alert("Nenhum dado encontrado para tipologia.");
        return;
      }

      let categories = data.map(
        (item) => `${item.tipologia} (${item.prod_line})`
      );
      let minutesData = data.map((item) => item.total_minutes);
      let incidentsData = data.map((item) => item.total_incidents);
      let avgTime = data.map((item) => {
        return item.total_incidents > 0
          ? Math.round(item.total_minutes / item.total_incidents)
          : 0;
      });

      Highcharts.chart("paretoChartTipologia", {
        chart: {
          type: "column",
        },
        title: {
          text: null,
        },
        xAxis: {
          categories: categories,
          title: { text: "Tipologia" },
        },
        yAxis: [
          {
            title: {
              text: "Minutos de Manutenção",
            },
            labels: {
              format: "{value} min",
            },
          },
          {
            title: {
              text: "Número de Incidências",
            },
            labels: {
              format: "{value}",
            },
            opposite: true,
          },
        ],
        tooltip: {
          shared: true,
        },
        series: [
          {
            name: "Tempo de Manutenção (min)",
            type: "column",
            data: minutesData,
            tooltip: {
              valueSuffix: " min",
            },
          },
          {
            name: "Incidências",
            type: "spline",
            yAxis: 1,
            data: incidentsData,
            tooltip: {
              valueSuffix: "",
            },
          },
          {
            name: "Média de Tempo de Resolução (min)",
            type: "spline",
            yAxis: 1,
            data: avgTime,
            tooltip: {
              valueSuffix: " min",
            },
          },
        ],
        exporting: {
          buttons: {
            contextButton: {
              menuItems: [
                "viewFullscreen",
                "printChart",
                "downloadPNG",
                "downloadJPEG",
                "downloadSVG",
                "downloadCSV",
                "downloadXLS",
                "downloadPDF",
              ],
            },
          },
        },
      });
    },
    error: function () {
      alert("Erro ao carregar os dados de tipologia.");
    },
  });
}
