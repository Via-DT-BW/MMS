$("#dailyDetailsModal").on("show.bs.modal", function (event) {
  var button = $(event.relatedTarget);
  var safetyComment = button.data("safety");
  var qualityComment = button.data("quality");
  var volumeComment = button.data("volume");
  var peopleComment = button.data("people");

  var modal = $(this);
  modal.find("#modalSafetyComment").val(safetyComment);
  modal.find("#modalQualityComment").val(qualityComment);
  modal.find("#modalVolumeComment").val(volumeComment);
  modal.find("#modalPeopleComment").val(peopleComment);
});
