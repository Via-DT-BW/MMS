$("#editTlModal").on("show.bs.modal", function (event) {
  var button = $(event.relatedTarget);
  var id = button.data("id");
  var username = button.data("username");
  var turno = button.data("turno");
  var area = button.data("area");
  var n_colaborador = button.data("n-colaborador");

  var modal = $(this);
  modal.find("#id").val(id);
  modal.find("#username").val(username);
  modal.find("#turno").val(turno);
  modal.find("#area").val(area);
  modal.find("#n_colaborador").val(n_colaborador);
});

$("#editMTModal").on("show.bs.modal", function (event) {
  var button = $(event.relatedTarget);
  var id = button.data("id");
  var username = button.data("username");
  var area = button.data("area");
  var n_colaborador = button.data("n-colaborador");

  var modal = $(this);
  modal.find("#id").val(id);
  modal.find("#username").val(username);
  modal.find("#area").val(area);
  modal.find("#n_colaborador").val(n_colaborador);
});
