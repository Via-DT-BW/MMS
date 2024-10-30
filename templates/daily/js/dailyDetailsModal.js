$("#dailyDetailsModal").on("show.bs.modal", function (event) {
  var button = $(event.relatedTarget); // O botão que abriu o modal
  var safetyComment = button.data("safety"); // Extraindo os dados
  var qualityComment = button.data("quality");
  var volumeComment = button.data("volume");
  var peopleComment = button.data("people");

  // Atualizando os valores no modal
  var modal = $(this);
  modal.find("#modalSafetyComment").val(safetyComment);
  modal.find("#modalQualityComment").val(qualityComment);
  modal.find("#modalVolumeComment").val(volumeComment);
  modal.find("#modalPeopleComment").val(peopleComment);
});
