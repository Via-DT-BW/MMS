function loadEquipmentPieChart() {
  let filters = {
    filter_area: $("#filter_area").val(),
    start_date: $("#start_date").val(),
    end_date: $("#end_date").val(),
    filter_shift: $("#filter_shift").val(),
  };

  $.ajax({
    url: "/api/get_equipment_stats_per_area",
    method: "GET",
    data: filters,
    success: function (data) {
      if (!data.length) {
        alert("Nenhum dado encontrado.");
        return;
      }

      let productionLines = {};
      data.forEach((item) => {
        if (!productionLines[item.prod_line]) {
          productionLines[item.prod_line] = {
            name: item.prod_line,
            y: 0,
          };
        }
        productionLines[item.prod_line].y += item.total_minutes;
      });

      let innerData = Object.values(productionLines).sort((a, b) =>
        a.name.localeCompare(b.name)
      );

      let outerData = data
        .map((item) => ({
          name: item.equipament,
          y: item.total_minutes,
          custom: { prod_line: item.prod_line },
        }))
        .sort((a, b) => a.custom.prod_line.localeCompare(b.custom.prod_line));

      let sunburstData = Object.values(productionLines).map((line) => {
        return {
          id: line.name,
          name: line.name,
          value: line.y,
          color: Highcharts.getOptions().colors[0],
        };
      });

      data.forEach((item) => {
        sunburstData.push({
          id: item.equipament,
          name: item.equipament,
          parent: item.prod_line,
          value: item.total_minutes,
          color: Highcharts.getOptions().colors[1],
        });
      });

      Highcharts.chart("equipmentPieChart", {
        chart: {
          type: "pie",
        },
        title: {
          text: null,
        },
        plotOptions: {
          pie: {
            shadow: false,
            center: ["50%", "50%"],
            startAngle: 0, // Define o ângulo de início
            dataLabels: {
              enabled: true,
              format: "<b>{point.name}</b>: {point.y} min",
            },
          },
        },
        series: [
          {
            name: "Linhas de Produção",
            data: innerData,
            size: "60%",
            dataLabels: {
              formatter: function () {
                return this.y > 5 ? this.point.name : null;
              },
              color: "#ffffff",
              distance: -30,
            },
            showInLegend: true,
          },
          {
            name: "Equipamentos",
            data: outerData,
            size: "80%",
            innerSize: "60%",
            dataLabels: {
              formatter: function () {
                return this.y > 1
                  ? `<b>${this.point.name}</b>: ${this.y} min`
                  : null;
              },
            },
            tooltip: {
              pointFormat: "<b>{point.name}</b>: {point.y} min",
            },
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
    },
    error: function () {
      alert("Erro ao carregar os dados.");
    },
  });
}
