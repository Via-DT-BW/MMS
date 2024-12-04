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

$(document).ready(function () {
  areas();
});
