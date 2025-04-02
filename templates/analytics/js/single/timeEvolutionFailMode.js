function loadTimeEvolutionChartFailMode() {
  let filters = {
    filter_prod_line: $("#filter_prod_line").val(),
    start_date: $("#start_date").val(),
    end_date: $("#end_date").val(),
    filter_shift: $("#filter_shift").val(),
  };

  $.ajax({
    url: "/api/get_weekly_maintenance_evolution_fail_mode",
    method: "GET",
    data: filters,
    success: function (data) {
      if (!data.length) {
        alert("Nenhum dado encontrado.");
        return;
      }

      data = data.filter((item) => item.description);

      let weeks = [...new Set(data.map((item) => item.week_start))].sort(
        (a, b) => new Date(a) - new Date(b)
      );

      let descriptions = [...new Set(data.map((item) => item.description))];

      let maintenanceDataByType = {};
      let incidentsDataByType = {};

      descriptions.forEach((tipo) => {
        maintenanceDataByType[tipo] = weeks.map(() => 0);
        incidentsDataByType[tipo] = weeks.map(() => 0);
      });

      data.forEach((item) => {
        let weekIndex = weeks.indexOf(item.week_start);
        maintenanceDataByType[item.description][weekIndex] = item.total_minutes;
        incidentsDataByType[item.description][weekIndex] = item.total_incidents;
      });

      let columnSeries = descriptions.map((tipo) => ({
        name: tipo,
        type: "column",
        data: maintenanceDataByType[tipo],
        tooltip: { valueSuffix: " min" },
        yAxis: 0,
        incidentsData: incidentsDataByType[tipo],
        events: {
          hide: function () {
            updateIncidentSeries();
          },
          show: function () {
            updateIncidentSeries();
          },
        },
      }));

      function updateIncidentSeries() {
        let aggregatedIncidents = weeks.map((_, weekIdx) => {
          let sum = 0;
          chart.series.forEach((s) => {
            if (s.type === "column" && s.visible) {
              sum += s.options.incidentsData[weekIdx];
            }
          });
          return sum;
        });
        if (incidentSeries) {
          incidentSeries.setData(aggregatedIncidents, false);
          chart.redraw();
        }
      }

      let chart = Highcharts.chart("timeEvolutionChartFailMode", {
        chart: {},
        title: { text: null },
        xAxis: {
          categories: weeks,
          title: { text: "Semana (início da semana)" },
        },
        yAxis: [
          {
            title: { text: "Tempo Total Manutenção (minutos)" },
            min: 0,
          },
          {
            title: { text: "Número de Incidentes" },
            opposite: true,
            min: 0,
          },
        ],
        tooltip: { shared: true },
        series: [
          ...columnSeries,
          {
            name: "Número de Incidentes",
            type: "spline",
            data: weeks.map((_, idx) => {
              let sum = 0;
              descriptions.forEach((tipo) => {
                sum += incidentsDataByType[tipo][idx];
              });
              return sum;
            }),
            tooltip: { valueSuffix: "" },
            yAxis: 1,
            showInLegend: false,
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

      let incidentSeries = chart.series.find((s) => s.type === "spline");
    },
    error: function () {
      alert("Erro ao carregar os dados.");
    },
  });
}
