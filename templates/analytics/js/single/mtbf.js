function loadMTBFByEquipmentChart() {
  let filters = {
    filter_prod_line: $("#filter_prod_line").val(),
    start_date: $("#start_date").val(),
    end_date: $("#end_date").val(),
    filter_shift: $("#filter_shift").val(),
  };

  $.ajax({
    url: "/api/get_mtbf_by_equipment",
    method: "GET",
    data: filters,
    success: function (data) {
      if (!data.length) {
        alert("Nenhum dado encontrado.");
        return;
      }

      data.sort((a, b) => b.mtbf - a.mtbf);
      let categories = data.map((item) => item.equipment);
      let mtbfValues = data.map((item) => Math.round(item.mtbf));

      Highcharts.chart("averageTimeBetweenFailuresChart", {
        chart: {
          type: "column",
        },
        title: {
          text: null,
        },
        xAxis: {
          categories: categories,
          title: { text: "Equipamento" },
        },
        yAxis: {
          min: 0,
          title: { text: "Tempo (minutos)" },
        },
        tooltip: {
          pointFormat: "MTBF: <b>{point.y:.0f} min</b>",
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
            data: mtbfValues,
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
