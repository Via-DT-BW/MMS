function loadScatterPlotChart() {
  let filters = {
    filter_prod_line: $("#filter_prod_line").val(),
    start_date: $("#start_date").val(),
    end_date: $("#end_date").val(),
    filter_shift: $("#filter_shift").val(),
  };

  $.ajax({
    url: "/api/get_scatter_data",
    method: "GET",
    data: filters,
    success: function (data) {
      if (!data.length) {
        alert("Nenhum dado encontrado.");
        return;
      }

      let scatterData = data.map((item) => [
        item.responseTime,
        item.resolutionTime,
      ]);

      Highcharts.chart("scatterPlotChart", {
        chart: {
          type: "scatter",
          zoomType: "xy",
        },
        title: {
          text: null,
        },
        xAxis: {
          title: {
            text: "Tempo de Resposta (min)",
          },
          startOnTick: true,
          endOnTick: true,
          showLastLabel: true,
        },
        yAxis: {
          title: {
            text: "Tempo de Resolução (min)",
          },
        },
        legend: {
          layout: "vertical",
          align: "left",
          verticalAlign: "top",
          x: 100,
          y: 70,
          floating: true,
          backgroundColor: Highcharts.defaultOptions.chart.backgroundColor,
          borderWidth: 1,
        },
        plotOptions: {
          scatter: {
            marker: {
              radius: 5,
              states: {
                hover: {
                  enabled: true,
                  lineColor: "rgb(100,100,100)",
                },
              },
            },
            tooltip: {
              headerFormat: "<b>{series.name}</b><br>",
              pointFormat: "{point.x} min, {point.y} min",
            },
          },
        },
        series: [
          {
            name: "Manutenções",
            color: "rgba(223, 83, 83, .5)",
            data: scatterData,
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
