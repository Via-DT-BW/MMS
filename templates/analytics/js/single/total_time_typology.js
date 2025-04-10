function loadParetoChartTipologia() {
  let filters = {
    filter_prod_line: $("#filter_prod_line").val(),
    start_date: $("#start_date").val(),
    end_date: $("#end_date").val(),
    filter_shift: $("#filter_shift").val(),
  };

  $.ajax({
    url: "/api/total_time_tipologia",
    method: "GET",
    data: filters,
    success: function (data) {
      if (!data.length) {
        alert("Nenhum dado encontrado para tipologia.");
        return;
      }

      let equipmentTotals = {};
      data.forEach((item) => {
        for (let equip in item.equipaments) {
          if (!equipmentTotals[equip]) equipmentTotals[equip] = 0;
          equipmentTotals[equip] += item.equipaments[equip];
        }
      });
      let equipmentCategories = Object.keys(equipmentTotals).sort(
        (a, b) => equipmentTotals[b] - equipmentTotals[a]
      );

      let seriesColumns = data.map((item) => {
        let dataArray = equipmentCategories.map(
          (equip) => item.equipaments[equip] || 0
        );
        return {
          name: item.tipologia,
          data: dataArray,
          stack: "tipologias",
        };
      });

      let equipmentIncidents = {};
      data.forEach((item) => {
        let tipTotal = 0;
        for (let equip in item.equipaments) {
          tipTotal += item.equipaments[equip];
        }
        for (let equip in item.equipaments) {
          let incidentEst =
            tipTotal > 0
              ? (item.equipaments[equip] / tipTotal) * item.n_incidents
              : 0;
          if (!equipmentIncidents[equip]) equipmentIncidents[equip] = 0;
          equipmentIncidents[equip] += incidentEst;
        }
      });
      let splineData = equipmentCategories.map((equip) =>
        Math.round(equipmentIncidents[equip] || 0)
      );

      Highcharts.chart("paretoChartTipologia", {
        chart: {
          type: "column",
        },
        title: {
          text: null,
        },
        xAxis: {
          categories: equipmentCategories,
          title: { text: "Equipamentos (ordenados do maior para o menor)" },
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
        series: [
          ...seriesColumns,
          {
            name: "Número de Incidentes",
            type: "spline",
            data: splineData,
            yAxis: 1,
            tooltip: { valueSuffix: " incidentes" },
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
      alert("Erro ao carregar os dados de tipologia.");
    },
  });
}
