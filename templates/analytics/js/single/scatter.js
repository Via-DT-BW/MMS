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

      let xValues = scatterData.map((p) => p[0]);
      let yValues = scatterData.map((p) => p[1]);

      let xMin = Math.min(...xValues);
      let xMax = Math.max(...xValues);
      let yMin = Math.min(...yValues);
      let yMax = Math.max(...yValues);

      let getOptimalTickInterval = (min, max) => {
        let range = max - min;
        if (range < 10) return 1;
        if (range < 50) return 5;
        if (range < 100) return 10;
        return Math.ceil(range / 10);
      };

      let xTickInterval = getOptimalTickInterval(xMin, xMax);
      let yTickInterval = getOptimalTickInterval(yMin, yMax);

      xMin = Math.floor(xMin / xTickInterval) * xTickInterval;
      xMax = Math.ceil(xMax / xTickInterval) * xTickInterval;
      yMin = Math.floor(yMin / yTickInterval) * yTickInterval;
      yMax = Math.ceil(yMax / yTickInterval) * yTickInterval;

      Highcharts.chart("scatterPlotChart", {
        chart: {
          type: "scatter",
          zoomType: "xy",
        },
        title: {
          text: "Correlação entre Tempo de Resposta e Resolução",
        },
        xAxis: {
          title: {
            text: "Tempo de Resposta (min)",
          },
          min: xMin,
          max: xMax,
          tickInterval: xTickInterval,
          startOnTick: true,
          endOnTick: true,
        },
        yAxis: {
          title: {
            text: "Tempo de Resolução (min)",
          },
          min: yMin,
          max: yMax,
          tickInterval: yTickInterval,
        },
        legend: {
          enabled: false,
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
