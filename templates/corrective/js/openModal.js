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
    var inicioMan = button.data("inicio-man");
    var fimMan = button.data("fim-man");
    var comment = button.data("comment");
    var tempo_man = button.data("tempo-man");

    var smsStatusText = smsState === 1 ? "Enviado" : "Por Enviar";
    var sapStatusText = sapState === 2 ? "Criado" : "Por Criar";
    var formattedSmsDate = smsDate
      ? formatDateTime(smsDate)
      : "A Aguardar Envio";

    var modal = $(this);
    modal.find("#modal-description").val(description);
    modal.find("#modal-equipament").val(equipament);
    modal.find("#modal-functional-location").val(functionalLocation);
    modal.find("#modal-sap-state").val(sapStatusText);
    modal.find("#modal-sms-state").val(smsStatusText);
    modal.find("#modal-sms-date").val(formattedSmsDate);
    modal.find("#modal-main-workcenter").val(workCenter);

    if (inicioMan) {
      modal.find("#modal-inicio-man").val(formatDateTime(inicioMan));
      $("#inicio-man-row").removeClass("d-none");
    } else {
      $("#inicio-man-row").addClass("d-none");
    }

    if (tempo_man) {
      modal.find("#modal-tempo-man").val(tempo_man);
      $("#tempo-row").removeClass("d-none");
    } else {
      $("#tempo-row").addClass("d-none");
    }

    if (fimMan) {
      modal.find("#modal-fim-man").val(formatDateTime(fimMan));
      $("#inicio-man-row").removeClass("d-none");
    } else {
      $("#inicio-man-row").addClass("d-none");
    }

    if (comment) {
      modal.find("#modal-comment").val(comment);
      $("#comment-row").removeClass("d-none");
    } else {
      $("#comment-row").addClass("d-none");
    }
  });

  $("#takeModal").on("show.bs.modal", function (event) {
    var button = $(event.relatedTarget);
    var id = button.data("id");
    var description = button.data("description");
    var equipament = button.data("equipament");
    var pedidoDate = button.data("pedido-date");
    var prodLine = button.data("prod-line");

    var modal = $(this);
    modal.find("#modal-id").val(id);
    modal.find("#modal-pedido-date").val(formatDateTime(pedidoDate));
    modal.find("#modal-description").val(description);
    modal.find("#modal-equipament").val(equipament);
    modal.find("#modal-prod-line").val(prodLine);
    modal.find("#n_tecnico").val("");

    $("#takeModalForm").on("submit", function (e) {
      e.preventDefault();
      var n_tecnico = $("#n_tecnico").val();
      var id = $("#modal-id").val();

      console.log(id, n_tecnico);
      $.ajax({
        type: "POST",
        url: "/change_to_inwork",
        data: {
          id: id,
          n_tecnico: n_tecnico,
        },
        success: function (response) {
          if (response.status === "success") {
            location.reload();
          } else {
            alert(response.message);
          }
        },
        error: function (xhr) {
          alert(xhr.responseJSON.message || "Erro ao processar a ação");
        },
        error: function () {
          alert("Erro ao processar a ação");
        },
      });
    });
  });

  $("#finishModal").on("show.bs.modal", function (event) {
    var button = $(event.relatedTarget);
    var id = button.data("id");
    var description = button.data("description");
    var equipament = button.data("equipament");
    var pedidoDate = button.data("pedido-date");
    var iniDate = button.data("ini-date");
    console.log(id, description, equipament, pedidoDate, iniDate);

    var modal = $(this);
    modal.find("#modal-id").val(id);
    modal.find("#modal-pedido-date").val(formatDateTime(pedidoDate));
    modal.find("#modal-ini-date").val(formatDateTime(iniDate));
    modal.find("#modal-description").val(description);
    modal.find("#modal-equipament").val(equipament);
    modal.find("#maintenance_comment").val("");

    $("#finishModalForm").on("submit", function (e) {
      e.preventDefault();
      var maintenanceComment = $("#maintenance_comment").val();
      var id = $("#modal-id").val();
      console.log(maintenance_comment);

      $.ajax({
        type: "POST",
        url: "/finish_maintenance",
        data: {
          id: id,
          maintenance_comment: maintenanceComment,
        },
        success: function (response) {
          if (response.status === "success") {
            location.reload();
          } else {
            alert(response.message);
          }
        },
        error: function (xhr) {
          alert(xhr.responseJSON.message || "Erro ao processar a ação");
        },
        error: function () {
          alert("Erro ao processar a ação");
        },
      });
    });
  });
});
