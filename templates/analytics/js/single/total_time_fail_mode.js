function loadParetoChart() {
  let filters = {
    filter_prod_line: $("#filter_prod_line").val(),
    start_date: $("#start_date").val(),
    end_date: $("#end_date").val(),
    filter_shift: $("#filter_shift").val(),
  };

  $.ajax({
    url: "/api/total_time_fail_mode",
    method: "GET",
    data: filters,
    success: function (data) {
      if (!data.length) {
        alert("Nenhum dado encontrado.");
        return;
      }

      let categories = data.map((item) => item.equipament);
      let seriesData = {};
      let incidents = data.map((item) => item.n_incidents);

      data.forEach((item) => {
        Object.entries(item.fail_modes).forEach(([mode, minutes]) => {
          if (!seriesData[mode]) {
            seriesData[mode] = [];
          }
          seriesData[mode].push(minutes || 0);
        });
      });

      let series = Object.keys(seriesData).map((mode) => ({
        name: mode,
        data: seriesData[mode],
        stack: "equipaments",
      }));

      series.push({
        name: "Número de Incidentes",
        type: "spline",
        data: incidents,
        yAxis: 1,
        tooltip: {
          valueSuffix: " incidentes",
        },
      });

      Highcharts.chart("paretoChart", {
        chart: {
          type: "column",
        },
        title: {
          text: null,
        },
        xAxis: {
          categories: categories,
          title: { text: "Equipamentos" },
        },
        yAxis: [
          {
            min: 0,
            title: { text: "Minutos de Manutenção" },
            stackLabels: {
              enabled: true,
              formatter: function () {
                return this.total + " min";
              },
            },
          },
          {
            title: { text: "Número de Incidentes" },
            opposite: true,
          },
        ],
        tooltip: {
          shared: true,
          pointFormat:
            '<span style="color:{series.color}">\u25CF</span> {series.name}: <b>{point.y}</b><br/>',
        },
        plotOptions: {
          column: {
            stacking: "normal",
          },
        },
        series: series,
      });
    },
    error: function () {
      alert("Erro ao carregar os dados.");
    },
  });
}
