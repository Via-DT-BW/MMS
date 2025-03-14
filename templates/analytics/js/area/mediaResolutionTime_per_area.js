function loadAverageResolutionTimeChart() {
  let filters = {
    filter_area: $("#filter_area").val(),
    start_date: $("#start_date").val(),
    end_date: $("#end_date").val(),
    filter_shift: $("#filter_shift").val(),
  };

  $.ajax({
    url: "/api/get_average_resolution_time_stats_per_area",
    method: "GET",
    data: filters,
    success: function (data) {
      if (!data.length) {
        alert("Nenhum dado encontrado.");
        return;
      }

      let categories = data.map((item) => item.prod_line);
      let avgResolutionTimes = data.map((item) => item.avg_resolution_time);

      Highcharts.chart("averageResolutionTimeChart", {
        chart: {
          type: "column",
          height: 300,
        },
        title: {
          text: null,
        },
        xAxis: {
          categories: categories,
          title: {
            text: "Linha de Produção",
          },
        },
        yAxis: {
          min: 0,
          title: {
            text: "Minutos",
          },
        },
        tooltip: {
          shared: true,
          valueSuffix: " min",
        },
        series: [
          {
            name: "Tempo de Resolução",
            data: avgResolutionTimes,
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
      alert("Erro ao carregar os dados.");
    },
  });
}
