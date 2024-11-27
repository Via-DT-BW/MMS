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

  $(".check-association").on("click", function () {
    var button = $(this);
    var id = button.data("id");
    var tecnicoId = button.data("id-tecnico");

    $.ajax({
      type: "GET",
      url: "/api/check_association",
      data: { id_tecnico: tecnicoId },
      success: function (response) {
        if (response.associado) {
          var tecnicoLogadoNome = "{{ session['nome'] }}";
          var tecnicoLogadoNumero = "{{ session['numero_mt'] }}";

          var tecnicoTexto = tecnicoLogadoNome + " - " + tecnicoLogadoNumero;
          var option = new Option(tecnicoTexto, tecnicoId);

          $("#select-tecnico").append(option);
          $("#select-tecnico").val(tecnicoId);
          $("#commentsModal").modal("show");

          $("#corretiva-id").text(response.manutencao.id);
          $("#corretiva-description").text(response.manutencao.description);
          $("#corretiva-equipament").text(response.manutencao.equipament);
          $("#corretiva-prod-line").text(response.manutencao.prod_line);
          $("#corretiva-pedido-date").text(
            formatDateTime(response.manutencao.data_pedido)
          );

          $("#comment").val("");

          $("#technical-warning").fadeIn();

          setTimeout(function () {
            $("#technical-warning").fadeOut();
          }, 6000);

          //Comments
          $("#submitComment").on("click", function () {
            var idCorretiva = $("#corretiva-id").text();
            var tecnicoId = $("#select-tecnico").val();
            var comentario = $("#comment").val();
            var tipoAvariaId = $("#select-avaria").val();
            var parou = $("#select-stop").val();

            if (!tecnicoId) {
              alert(
                "Por favor, registe-se na manutenção para registar atividade."
              );
              return;
            }

            if (!comentario) {
              alert("Por favor, faça um comentário.");
              return;
            }

            $.ajax({
              type: "POST",
              url: "/api/update_comment",
              data: {
                id_corretiva: idCorretiva,
                id_tecnico: tecnicoId,
                comment: comentario,
                id_tipo_avaria: tipoAvariaId,
                stopped_prod: parou,
              },
              success: function (response) {
                if (response.status === "success") {
                  $("#commentsModal").modal("hide");
                  location.reload();
                } else {
                  alert(response.message);
                }
              },
              error: function () {
                alert("Erro ao adicionar o comentário.");
              },
            });
          });

          $("#finishMaintenance").on("click", function () {
            var maintenanceComment = $("#comment").val();
            var idCorretiva = $("#corretiva-id").text();
            var tipoAvariaId = $("#select-avaria").val();
            var parouProducao = $("#select-stop").val();

            if (
              !maintenanceComment ||
              !idCorretiva ||
              !tipoAvariaId ||
              !parouProducao
            ) {
              alert(
                "Preencha todos os campos obrigatórios antes de finalizar a manutenção."
              );
              return;
            }

            if (!id) {
              alert("Erro: ID da intervenção não encontrado.");
              return;
            }

            $.ajax({
              type: "GET",
              url: "/api/check_all_interventions_completed",
              data: { id_corretiva: idCorretiva, id_tecnico: tecnicoId },
              success: function (response) {
                if (response.status === "success") {
                  $.ajax({
                    type: "POST",
                    url: "/finish_maintenance",
                    data: {
                      id_corretiva: idCorretiva,
                      id: tecnicoId,
                      maintenance_comment: maintenanceComment,
                      id_tipo_avaria: tipoAvariaId,
                      parou_producao: parouProducao,
                    },
                    success: function (response) {
                      if (response.status === "success") {
                        alert("Manutenção finalizada com sucesso!");
                        location.reload();
                      } else {
                        alert(
                          response.message || "Erro ao finalizar a manutenção."
                        );
                      }
                    },
                    error: function (xhr) {
                      alert(
                        xhr.responseJSON?.message || "Erro ao processar a ação."
                      );
                    },
                  });
                } else if (response.status === "warning") {
                  alert(
                    response.message ||
                      "Ação não permitida devido a intervenções pendentes, por favor garanta que é o único técnico na manutenção."
                  );
                } else {
                  alert(
                    response.message ||
                      "Erro ao verificar o status das intervenções."
                  );
                }
              },
              error: function () {
                alert("Erro ao verificar o status das intervenções.");
              },
            });
          });
        } else {
          $("#takeModal").modal("show");

          $("#modal-id").val(id);
          $("#modal-pedido-date").val(
            formatDateTime(button.data("pedido-date"))
          );
          $("#modal-description-t").val(button.data("description"));
          $("#modal-equipament-t").val(button.data("equipament"));
          $("#modal-prod-line").val(button.data("prod-line"));
        }
      },
      error: function () {
        alert("Erro ao verificar associação do técnico.");
      },
    });
  });

  $("#takeModalForm").on("submit", function (e) {
    e.preventDefault();
    var tecnicoId = $("#select-tecnico-t").val();
    var id = $("#modal-id").val();

    console.log(tecnicoId, id);

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

  $("#rejectModal").on("show.bs.modal", function (event) {
    var button = $(event.relatedTarget);
    var id = button.data("id");
    var description = button.data("description");
    var prodLine = button.data("prod-line");
    var equipament = button.data("equipament");
    var pedidoDate = button.data("pedido-date");
    var idMt = button.data("id-mt");
    var nameT = button.data("nome-mt");

    var modal = $(this);
    modal.find("#modal-reject-description").val(description);
    modal.find("#modal-reject-prod-line").val(prodLine);
    modal.find("#modal-reject-equipament").val(equipament);
    modal.find("#modal-reject-pedido-date").val(formatDateTime(pedidoDate));
    $("#modal-reject-technician").val(nameT);

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
          technician_id: idMt,
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
