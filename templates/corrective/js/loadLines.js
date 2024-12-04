function loadLines() {
  $.ajax({
    url: "/api/prod_lines",
    method: "GET",
    success: function (data) {
      let lineSelect = $('select[name="filter_prod_line"]');
      lineSelect.empty();
      lineSelect.append('<option value="">Selecione a linha</option>');

      data.sort((a, b) => a.line.localeCompare(b.line));

      data.forEach((line) => {
        lineSelect.append(`<option value="${line.line}">${line.line}</option>`);
      });

      let filterProdLineValue =
        '{{ request.args.get("filter_prod_line", "") }}';
      if (filterProdLineValue) {
        lineSelect.val(filterProdLineValue);
      }

      disableFields(true);
    },
    error: function () {
      alert("Erro ao carregar as linhas.");
    },
  });
}

$(document).ready(function () {
  loadLines();
});
