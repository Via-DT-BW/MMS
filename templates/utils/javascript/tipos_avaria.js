function fetchTipoAvarias(prodLine, id) {
  $.ajax({
    type: "GET",
    url: "/api/tipo_avarias",
    data: { prod_line: prodLine },
    success: function (tiposAvarias) {
      $(id)
        .empty()
        .append('<option value="">Selecione um tipo de avaria</option>');

      tiposAvarias.forEach(function (tipo) {
        $(id).append(new Option(tipo.tipo, tipo.id));
      });
    },
    error: function (error) {
      alert(error.responseJSON.error || "Erro ao carregar tipos de avarias.");
    },
  });
}
