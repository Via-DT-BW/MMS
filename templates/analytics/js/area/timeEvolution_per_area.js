function loadTimeEvolutionChart() {
  let filters = {
    filter_area: $("#filter_area").val(),
    start_date: $("#start_date").val(),
    end_date: $("#end_date").val(),
    filter_shift: $("#filter_shift").val(),
  };

  $.ajax({
    url: "/api/get_weekly_maintenance_evolution_per_area",
    method: "GET",
    data: filters,
    success: function (data) {
      if (!data.length) {
        alert("Nenhum dado encontrado.");
        return;
      }

      // Organiza os dados por linha de produção
      let dataByProdLine = {};
      data.forEach((item) => {
        if (!dataByProdLine[item.prod_line]) {
          dataByProdLine[item.prod_line] = [];
        }
        dataByProdLine[item.prod_line].push(item);
      });

      // Obtém todas as semanas ordenadas
      let allWeeks = [...new Set(data.map((item) => item.week_start))];
      allWeeks.sort((a, b) => new Date(a) - new Date(b));

      let series = [];
      Object.keys(dataByProdLine).forEach((prodLine) => {
        let prodLineData = dataByProdLine[prodLine];

        // Mapeia valores para o tempo de manutenção
        let minutesValues = allWeeks.map((week) => {
          let weekData = prodLineData.find((item) => item.week_start === week);
          return weekData ? weekData.total_minutes : 0;
        });

        // Mapeia valores para o número de incidentes
        let incidentsValues = allWeeks.map((week) => {
          let weekData = prodLineData.find((item) => item.week_start === week);
          return weekData ? weekData.total_incidents : 0;
        });

        series.push({
          name: `Tempo de Manutenção (min) - ${prodLine}`,
          type: "column",
          data: minutesValues,
          tooltip: { valueSuffix: " min" },
        });

        series.push({
          name: `Número de Incidentes - ${prodLine}`,
          type: "spline",
          data: incidentsValues,
          yAxis: 1,
          tooltip: { valueSuffix: "" },
        });
      });

      Highcharts.chart("timeEvolutionChart", {
        chart: { zoomType: "xy" },
        title: {
          text: null,
        },
        xAxis: {
          categories: allWeeks,
          title: { text: "Semana (início da semana)" },
        },
        yAxis: [
          {
            title: { text: "Tempo Total (minutos)" },
            min: 0,
          },
          {
            title: { text: "Número de Incidentes" },
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
