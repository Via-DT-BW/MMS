function loadResponseTimeChart() {
  let filters = {
    filter_area: $("#filter_area").val(),
    start_date: $("#start_date").val(),
    end_date: $("#end_date").val(),
    filter_shift: $("#filter_shift").val(),
  };

  $.ajax({
    url: "/api/get_average_response_time_stats_per_area",
    method: "GET",
    data: filters,
    success: function (data) {
      if (!data.length) {
        alert("Nenhum dado encontrado.");
        return;
      }

      let seriesData = data.map((item) => ({
        y: Math.round(item.avg_response_time),
        prod_line: item.prod_line,
      }));

      let categories = data.map((item) => item.prod_line);

      Highcharts.chart("mediaResponseTimeChart", {
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
          formatter: function () {
            return `<b>Linha: ${this.point.prod_line}</b><br/>
                    Tempo de Resposta: <b>${this.point.y} min</b>`;
          },
        },
        series: [
          {
            name: "Tempo de Resposta",
            data: seriesData,
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
