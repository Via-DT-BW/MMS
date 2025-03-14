function loadMTBFByEquipmentChart() {
  let filters = {
    filter_area: $("#filter_area").val(),
    start_date: $("#start_date").val(),
    end_date: $("#end_date").val(),
    filter_shift: $("#filter_shift").val(),
  };
  $.ajax({
    url: "/api/get_mtbf_by_equipment_per_area",
    method: "GET",
    data: filters,
    success: function (data) {
      if (!data.length) {
        alert("Nenhum dado encontrado.");
        return;
      }

      data.sort((a, b) => b.mtbf - a.mtbf);

      let seriesData = data.map((item) => ({
        y: Math.round(item.mtbf),
        equipment: item.equipment,
        prod_line: item.prod_line,
      }));

      Highcharts.chart("averageTimeBetweenFailuresChart", {
        chart: {
          type: "column",
        },
        title: {
          text: null,
        },
        xAxis: {
          categories: data.map((item) => item.equipment),
          title: { text: "Equipamento" },
        },
        yAxis: {
          min: 0,
          title: { text: "Tempo (minutos)" },
        },
        tooltip: {
          formatter: function () {
            return `<b>${this.point.equipment}</b><br/>
              Linha: ${this.point.prod_line}<br/>
              MTBF: <b>${this.point.y} min</b>`;
          },
        },
        plotOptions: {
          column: {
            dataLabels: {
              enabled: true,
              format: "{point.y:.1f} min",
            },
          },
        },
        series: [
          {
            name: "MTBF",
            data: seriesData,
            color: "#007bff",
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
