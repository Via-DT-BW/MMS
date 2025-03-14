function loadScatterPlotChart() {
  let filters = {
    filter_area: $("#filter_area").val(),
    start_date: $("#start_date").val(),
    end_date: $("#end_date").val(),
    filter_shift: $("#filter_shift").val(),
  };

  $.ajax({
    url: "/api/get_scatter_data_per_area",
    method: "GET",
    data: filters,
    success: function (data) {
      if (!data.length) {
        alert("Nenhum dado encontrado.");
        return;
      }

      let dataByProdLine = {};
      data.forEach((item) => {
        if (!dataByProdLine[item.prod_line]) {
          dataByProdLine[item.prod_line] = [];
        }
        dataByProdLine[item.prod_line].push([
          item.responseTime,
          item.resolutionTime,
        ]);
      });

      let series = Object.keys(dataByProdLine).map((prodLine) => ({
        name: `Linha de Produção: ${prodLine}`,
        data: dataByProdLine[prodLine],
        marker: { radius: 5 },
        tooltip: {
          pointFormat:
            "Tempo de Resposta: {point.x} min, Tempo de Resolução: {point.y} min",
        },
      }));

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
              states: {
                hover: {
                  enabled: true,
                  lineColor: "rgb(100,100,100)",
                },
              },
            },
          },
        },
        series: series,
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
