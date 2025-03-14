function loadTechnicianInterventionsChart() {
  let filters = {
    filter_area: $("#filter_area").val(),
    start_date: $("#start_date").val(),
    end_date: $("#end_date").val(),
    filter_shift: $("#filter_shift").val(),
  };

  $.ajax({
    url: "/api/get_technician_interventions_per_area",
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
        dataByProdLine[item.prod_line].push(item);
      });

      let series = [];
      Object.keys(dataByProdLine).forEach((prodLine) => {
        let prodLineData = dataByProdLine[prodLine];

        prodLineData.sort((a, b) =>
          a.technician_name.localeCompare(b.technician_name)
        );

        let categories = prodLineData.map((item) => item.technician_name);
        let interventions = prodLineData.map(
          (item) => item.total_interventions
        );
        let avgResolutionTime = prodLineData.map((item) =>
          Math.round(item.avg_resolution_time)
        );

        series.push({
          name: `Intervenções - ${prodLine}`,
          type: "column",
          data: interventions,
          tooltip: { valueSuffix: "" },
        });

        series.push({
          name: `Tempo Médio de Resolução (min) - ${prodLine}`,
          type: "spline",
          data: avgResolutionTime,
          yAxis: 1,
          tooltip: { valueSuffix: " min" },
        });
      });

      Highcharts.chart("mtInterventions", {
        chart: { zoomType: "xy" },
        title: {
          text: null,
        },
        xAxis: {
          categories: [...new Set(data.map((item) => item.technician_name))],
          title: { text: "Técnico" },
        },
        yAxis: [
          {
            title: { text: "Número de Intervenções" },
            min: 0,
          },
          {
            title: { text: "Média de Tempo de Resolução (min)" },
            opposite: true,
            min: 0,
          },
        ],
        tooltip: {
          shared: true,
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
