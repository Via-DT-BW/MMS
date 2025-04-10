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

      data.sort((a, b) => {
        const totalA = Object.values(a.fail_modes).reduce(
          (acc, curr) => acc + Number(curr),
          0
        );
        const totalB = Object.values(b.fail_modes).reduce(
          (acc, curr) => acc + Number(curr),
          0
        );
        return totalB - totalA;
      });
      let categories = data.map((item) => item.equipament);

      let allFailModes = new Set();
      data.forEach((item) => {
        Object.keys(item.fail_modes).forEach((mode) => {
          allFailModes.add(mode);
        });
      });

      let series = [];
      allFailModes.forEach((mode) => {
        let modeData = data.map((item) => {
          return item.fail_modes[mode] || 0;
        });
        series.push({
          name: mode,
          data: modeData,
          stack: "equipaments",
        });
      });

      let incidents = data.map((item) => item.n_incidents);
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
