$(document).ready(function () {
  $("#detailsModal").on("show.bs.modal", function (event) {
    var button = $(event.relatedTarget);
    var id = button.data("id");
    var description = button.data("description");
    var equipament = button.data("equipament");
    var functionalLocation = button.data("functional-location");
    var sapState = button.data("sap-state");
    var smsState = button.data("sms-state");
    var smsDate = button.data("sms-date");
    var workCenter = button.data("main-workcenter");

    if (smsState === 1) {
      smsStatusText = "Enviado";
    } else {
      smsStatusText = "Por Enviar";
    }

    if (sapState === 2) {
      sapStatusText = "Criado";
    } else {
      sapStatusText = "Por Criar";
    }

    var modal = $(this);
    modal.find("#modal-id").text(id);
    modal.find("#modal-description").text(description);
    modal.find("#modal-equipament").text(equipament);
    modal.find("#modal-functional-location").text(functionalLocation);
    modal.find("#modal-sap-state").text(sapStatusText);
    modal.find("#modal-sms-state").text(smsStatusText);
    modal.find("#modal-sms-date").text(formatDateTime(smsDate));
    modal.find("#modal-main-workcenter").text(workCenter);
  });
});
