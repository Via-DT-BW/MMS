$.ajax({
  type: "GET",
  url: "/api/tipo_avarias",
  success: function (tiposAvarias) {
    $("#select-avaria")
      .empty()
      .append('<option value="">Selecione um tipo de avaria</option>');

    tiposAvarias.forEach(function (tipo) {
      $("#select-avaria").append(new Option(tipo.tipo, tipo.id));
    });
  },
  error: function () {
    alert("Erro ao carregar tipos de avarias.");
  },
});
