$(document).ready(function () {
  $("#elegivelSistemica").change(function () {
    if ($(this).is(":checked")) {
      $("#divDefinidaAcao").show();
    } else {
      $("#divDefinidaAcao").hide();
      $("#definidaNao").prop("checked", true);
    }
  });

  $("#commentsModal").on("show.bs.modal", function (event) {
    var button = $(event.relatedTarget);
    var idCorretiva = button.data("id-corretiva");
    var id = button.data("id");
    var prodLine = button.data("prod-line");

    fetchTipoAvarias(prodLine, "#select-avaria");

    $("#corretiva-id").text(idCorretiva);
    $("#corretiva-description").text(button.data("description"));
    $("#corretiva-equipament").text(button.data("equipament"));
    $("#corretiva-pedido-date").text(
      formatDateTime(button.data("pedido-date"))
    );
    $("#corretiva-prod-line").text(button.data("prod-line"));

    $("#comment").val("");

    $("#select-tecnico, #select-new-tecnico")
      .empty()
      .append('<option value="">Registe-se para comentar</option>');

    var tecnicoLogadoId = "{{ session['id_mt'] }}";
    var tecnicoLogadoNome = "{{ session['nome'] }}";
    var tecnicoLogadoNumero = "{{ session['numero_mt'] }}";

    var optionText = tecnicoLogadoNome + " - " + tecnicoLogadoNumero;
    var option = new Option(optionText, tecnicoLogadoId);
    $("#select-new-tecnico").append(option);
    $("#select-new-tecnico").prop("disabled", true);

    $("#elegivelSistemica").prop("checked", false);
    $("#divDefinidaAcao").hide();

    $.ajax({
      type: "GET",
      url: "/api/get_tecnicos_associados/" + idCorretiva,
      success: function (tecnicosAssociados) {
        var tecnicoSelecionado = false;

        tecnicosAssociados.forEach(function (tecnico) {
          var optionText = tecnico.nome + " - " + tecnico.n_tecnico;
          var option = new Option(optionText, tecnico.id);

          if (tecnico.id == tecnicoLogadoId) {
            $(option).prop("selected", true);
            tecnicoSelecionado = true;
          }

          $("#select-tecnico").append(option);
        });

        if (!tecnicoSelecionado) {
          $("#submitComment").prop("disabled", true);
        } else {
          $("#submitComment").prop("disabled", false);
        }
      },
      error: function () {
        alert("Erro ao carregar técnicos associados.");
      },
    });

    $("#finishMaintenance").on("click", function () {
      var maintenanceComment = $("#comment").val();
      var idCorretiva = $("#corretiva-id").text();
      var tipoAvariaId = $("#select-avaria").val();
      var parouProducao = $("#select-stop").val();

      var elegivelSistemica = $("#elegivelSistemica").is(":checked")
        ? "Sim"
        : "Não";
      var definidaAcao = $("#divDefinidaAcao").is(":visible")
        ? $("input[name='definida_acao']:checked").val()
        : "Não";

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
        data: { id_corretiva: idCorretiva, id_tecnico: tecnicoLogadoId },
        success: function (response) {
          if (response.status === "success") {
            $.ajax({
              type: "POST",
              url: "/finish_maintenance",
              data: {
                id_corretiva: idCorretiva,
                id: tecnicoLogadoId,
                maintenance_comment: maintenanceComment,
                id_tipo_avaria: tipoAvariaId,
                parou_producao: parouProducao,
                elegivel_sistemica: elegivelSistemica,
                definida_acao: definidaAcao,
              },
              success: function (response) {
                if (response.status === "success") {
                  alert("Manutenção finalizada com sucesso!");
                  window.location.reload();
                } else {
                  alert(response.message || "Erro ao finalizar a manutenção.");
                }
              },
              error: function (xhr) {
                alert(xhr.responseJSON?.message || "Erro ao processar a ação.");
              },
            });
          } else if (response.status === "warning") {
            alert(
              response.message ||
                "Ação não permitida devido a intervenções pendentes, por favor garanta que é o único técnico na manutenção."
            );
          } else {
            alert(
              response.message || "Erro ao verificar o status das intervenções."
            );
          }
        },
        error: function () {
          alert("Erro ao verificar o status das intervenções.");
        },
      });
    });
  });

  $("#submitComment").on("click", function () {
    var idCorretiva = $("#corretiva-id").text();
    var tecnicoId = $("#select-tecnico").val();
    var comentario = $("#comment").val();
    var tipoAvariaId = $("#select-avaria").val();
    var parou = $("#select-stop").val();

    var elegivelSistemica = $("#elegivelSistemica").is(":checked")
      ? "Sim"
      : "Não";
    var definidaAcao = $("#divDefinidaAcao").is(":visible")
      ? $("input[name='definida_acao']:checked").val()
      : "Não";

    if (!tecnicoId) {
      alert("Por favor, registe-se na manutenção para registar atividade.");
      return;
    }

    if (!comentario) {
      alert("Por favor, faça um comentário.");
      return;
    }

    if (!tipoAvariaId) {
      alert("Por favor, selecione um tipo de avaria.");
      return;
    }
    if (!parou) {
      alert("Por favor, selecione se impactou ou não a produção.");
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
        elegivel_sistemica: elegivelSistemica,
        definida_acao: definidaAcao,
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
});
