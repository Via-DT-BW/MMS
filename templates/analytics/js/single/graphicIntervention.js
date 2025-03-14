function loadInterventionChart(stoppedProdValue, containerId) {
  let filters = {
    filter_prod_line: $("#filter_prod_line").val(),
    start_date: $("#start_date").val(),
    end_date: $("#end_date").val(),
    filter_shift: $("#filter_shift").val(),
    stopped_prod: stoppedProdValue,
  };

  $.ajax({
    url: "/api/get_intervention_stats",
    method: "GET",
    data: filters,
    success: function (data) {
      if (!data.length) {
        alert("Nenhum dado encontrado.");
        return;
      }

      let totalDowntime = data.reduce((sum, item) => sum + item.downtime, 0);
      let totalTechnicianTime = data.reduce(
        (sum, item) => sum + item.technician_time,
        0
      );
      let nonTechnicianTime = totalDowntime - totalTechnicianTime;

      Highcharts.chart(containerId, {
        chart: {
          type: "bar",
        },
        title: {
          text: null,
        },
        xAxis: {
          categories: ["Tempo de Manutenção"],
        },
        yAxis: {
          min: 0,
          title: {
            text: "Tempo (min)",
          },
        },
        tooltip: {
          shared: true,
          valueSuffix: " min",
        },
        plotOptions: {
          series: {
            dataLabels: {
              enabled: true,
              format: "{point.y} min",
            },
          },
        },
        series: [
          {
            name: "Tempo Total",
            data: [totalDowntime],
            color: "#007bff",
          },
          {
            name: "Tempo em Manutenção",
            data: [totalTechnicianTime],
            color: "#28a745",
          },
          {
            name: "Tempo sem intervenção",
            data: [nonTechnicianTime],
            color: "#dc3545",
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
