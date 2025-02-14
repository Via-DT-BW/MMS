function criarOrdem(element, id) {
  const button = element;
  const originalContent = button.innerHTML;

  button.innerHTML =
    'A criar ordem...<br><img src="' +
    "{{ url_for('static', filename='content/loader.gif') }}" +
    '" alt="Carregando" />';
  button.disabled = true;

  $.ajax({
    url: "/pedido_spares/" + id,
    method: "POST",
    success: function (response) {
      button.innerHTML = response.message;
    },
    error: function () {
      button.innerHTML = "Erro ao criar ordem. Tente novamente.";
      button.disabled = false;
    },
  });
}
