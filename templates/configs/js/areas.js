function areas() {
  $.ajax({
    url: "/api/get_areas",
    method: "GET",
    success: function (data) {
      data.forEach((area) => {
        let option = $("<option></option>")
          .attr("value", area.area)
          .text(area.area);

        if (area.area === "{{ filtro_area }}") {
          option.attr("selected", "selected");
        }

        $("#area").append(option);
      });
    },
    error: function () {
      alert("Erro ao carregar as áreas.");
    },
  });
}

function loadAreasForForm() {
  $.ajax({
    url: "/api/get_areas",
    method: "GET",
    success: function (data) {
      $("#area_form").empty();
      $("#area_form").append('<option value="">Selecione a área</option>');

      data.forEach((area) => {
        let option = $("<option></option>")
          .attr("value", area.area)
          .text(area.area);

        $("#area_form").append(option);
      });
    },
    error: function () {
      alert("Erro ao carregar as áreas.");
    },
  });
}

$(document).ready(function () {
  areas();
  loadAreasForForm();
});
