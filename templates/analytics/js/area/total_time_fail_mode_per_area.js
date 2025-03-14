function loadParetoChart() {
  let filters = {
    filter_area: $("#filter_area").val(),
    start_date: $("#start_date").val(),
    end_date: $("#end_date").val(),
    filter_shift: $("#filter_shift").val(),
  };

  $.ajax({
    url: "/api/total_time_fail_mode_per_area",
    method: "GET",
    data: filters,
    success: function (data) {
      if (!data.length) {
        alert("Nenhum dado encontrado.");
        return;
      }

      let categories = data.map(
        (item) => `${item.description} (${item.prod_line})`
      );
      let totalMinutes = data.map((item) => item.total_minutes);
      let incidents = data.map((item) => item.total_incidents);
      let avgTime = data.map((item) => {
        return item.total_incidents > 0
          ? Math.round(item.total_minutes / item.total_incidents)
          : 0;
      });

      Highcharts.chart("paretoChart", {
        chart: {
          zoomType: "xy",
        },
        title: {
          text: null,
        },
        xAxis: {
          categories: categories,
          crosshair: true,
          title: { text: "Descrição" },
        },
        yAxis: [
          {
            labels: {
              format: "{value} min",
            },
            title: {
              text: "Minutos de Manutenção",
            },
          },
          {
            title: {
              text: "Incidências / Média de Tempo (min)",
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
            data: totalMinutes,
            tooltip: {
              valueSuffix: " min",
            },
          },
          {
            name: "Incidências",
            type: "spline",
            yAxis: 1,
            data: incidents,
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
      alert("Erro ao carregar os dados.");
    },
  });
}
