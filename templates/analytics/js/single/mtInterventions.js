function loadTechnicianInterventionsChart() {
  let filters = {
    filter_prod_line: $("#filter_prod_line").val(),
    start_date: $("#start_date").val(),
    end_date: $("#end_date").val(),
    filter_shift: $("#filter_shift").val(),
  };

  $.ajax({
    url: "/api/get_technician_interventions",
    method: "GET",
    data: filters,
    success: function (data) {
      if (!data.length) {
        alert("Nenhum dado encontrado.");
        return;
      }

      data.sort((a, b) => a.technician_name.localeCompare(b.technician_name));

      let categories = data.map((item) => item.technician_name);
      let interventions = data.map((item) => item.total_interventions);
      let avgResolutionTime = data.map((item) =>
        Math.round(item.avg_resolution_time)
      );

      Highcharts.chart("mtInterventions", {
        chart: {},
        title: {
          text: null,
        },
        xAxis: {
          categories: categories,
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
        series: [
          {
            name: "Número de Intervenções",
            type: "column",
            data: interventions,
            tooltip: { valueSuffix: "" },
          },
          {
            name: "Média de Tempo de Resolução",
            type: "spline",
            data: avgResolutionTime,
            yAxis: 1,
            tooltip: { valueSuffix: " min" },
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
