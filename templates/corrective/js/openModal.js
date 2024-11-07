$(document).ready(function () {
  $.ajax({
    type: "GET",
    url: "/api/tipo_avarias",
    success: function (tiposAvarias) {
      $("#tipo-avaria")
        .empty()
        .append('<option value="">Selecione um tipo de avaria</option>');

      tiposAvarias.forEach(function (tipo) {
        $("#tipo-avaria").append(new Option(tipo.tipo, tipo.id));
      });
    },
    error: function () {
      alert("Erro ao carregar tipos de avarias.");
    },
  });

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

    $.ajax({
      type: "GET",
      url: "/api/tecnicos",
      success: function (tecnicos) {
        var selectTecnico = $("#select-tecnico");
        selectTecnico.empty();
        selectTecnico.append('<option value="">Selecione um técnico</option>');

        tecnicos.forEach(function (tecnico) {
          selectTecnico.append(
            new Option(`${tecnico.nome} - ${tecnico.n_tecnico}`, tecnico.id)
          );
        });
      },
      error: function () {
        alert("Erro ao buscar técnicos.");
      },
    });

    $("#takeModalForm").on("submit", function (e) {
      e.preventDefault();
      var tecnicoId = $("#select-tecnico").val();
      var id = $("#modal-id").val();

      if (!tecnicoId) {
        alert("Selecione um técnico.");
        return;
      }

      $.ajax({
        type: "POST",
        url: "/change_to_inwork",
        data: {
          id: id,
          tecnico_id: tecnicoId,
        },
        success: function (response) {
          if (response.status === "success") {
            location.reload();
          } else {
            alert(response.message);
          }
        },
        error: function () {
          alert("Erro ao processar a ação.");
        },
      });
    });
  });

  $("#finishModalForm").on("submit", function (e) {
    e.preventDefault();
    var maintenanceComment = $("#maintenance_comment").val();
    var id = $("#modal-id").val();
    var tipoAvariaId = $("#tipo-avaria").val();

    $.ajax({
      type: "POST",
      url: "/finish_maintenance",
      data: {
        id: id,
        maintenance_comment: maintenanceComment,
        id_tipo_avaria: tipoAvariaId,
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
    });
  });

  $("#rejectModal").on("show.bs.modal", function (event) {
    var button = $(event.relatedTarget);
    var id = button.data("id");
    var description = button.data("description");
    var prodLine = button.data("prod-line");
    var equipament = button.data("equipament");
    var pedidoDate = button.data("pedido-date");

    var modal = $(this);
    modal.find("#modal-reject-description").val(description);
    modal.find("#modal-reject-prod-line").val(prodLine);
    modal.find("#modal-reject-equipament").val(equipament);
    modal.find("#modal-reject-pedido-date").val(formatDateTime(pedidoDate));

    $("#btn-reject-submit").on("click", function () {
      var modal = $("#rejectModal");
      var comment = modal.find("#modal-reject-comment").val();
      var notificationId = $(event.relatedTarget).data("id");

      if (!comment) {
        alert("Por favor, forneça um motivo para a rejeição.");
        return;
      }

      $.ajax({
        type: "POST",
        url: "/reject_corrective_notification",
        data: {
          id: notificationId,
          comment: comment,
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
      });
    });
  });
});
