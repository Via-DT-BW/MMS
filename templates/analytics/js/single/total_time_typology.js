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

      // 1. Agregar os minutos por equipamento para ordená-los (maior para menor)
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

      // 2. Construir as séries de colunas para cada tipologia
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

      // 3. Estimar os incidentes por equipamento
      // Para cada tipologia, distribuímos os incidentes proporcionalmente ao tempo de manutenção de cada equipamento.
      let equipmentIncidents = {};
      data.forEach((item) => {
        let tipTotal = 0;
        // Soma total de minutos dessa tipologia (soma dos valores de todos os equipamentos)
        for (let equip in item.equipaments) {
          tipTotal += item.equipaments[equip];
        }
        // Para cada equipamento nessa tipologia, calcular a fração dos incidentes
        for (let equip in item.equipaments) {
          let incidentEst =
            tipTotal > 0
              ? (item.equipaments[equip] / tipTotal) * item.n_incidents
              : 0;
          if (!equipmentIncidents[equip]) equipmentIncidents[equip] = 0;
          equipmentIncidents[equip] += incidentEst;
        }
      });
      let splineData = equipmentCategories.map(
        (equip) => equipmentIncidents[equip] || 0
      );

      // 4. Construir o gráfico Pareto
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
