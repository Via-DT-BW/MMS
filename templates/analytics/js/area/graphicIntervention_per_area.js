function loadInterventionChart(stoppedProdValue, containerId) {
  let filters = {
    filter_area: $("#filter_area").val(),
    start_date: $("#start_date").val(),
    end_date: $("#end_date").val(),
    filter_shift: $("#filter_shift").val(),
    stopped_prod: stoppedProdValue,
  };

  $.ajax({
    url: "/api/get_intervention_stats_per_area",
    method: "GET",
    data: filters,
    success: function (data) {
      if (!data.length) {
        alert("Nenhum dado encontrado.");
        return;
      }

      let categories = data.map((item) => item.prod_line);

      let totalDowntimeSeries = data.map((item) => item.downtime);
      let totalTechnicianTimeSeries = data.map((item) => item.technician_time);
      let nonTechnicianSeries = data.map(
        (item) => item.downtime - item.technician_time
      );

      Highcharts.chart(containerId, {
        chart: {
          type: "column",
        },
        title: {
          text: null,
        },
        xAxis: {
          categories: categories,
          title: { text: "Linha de Produção" },
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
            data: totalDowntimeSeries,
            color: "#007bff",
          },
          {
            name: "Tempo em Manutenção",
            data: totalTechnicianTimeSeries,
            color: "#28a745",
          },
          {
            name: "Tempo sem intervenção",
            data: nonTechnicianSeries,
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
