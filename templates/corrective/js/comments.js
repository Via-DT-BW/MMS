$(document).ready(function () {
  function toggleButtons(tabId) {
    if (tabId === "#commentSection") {
      $("#submitComment").show();
      $("#associateTechnician").hide();
    } else if (tabId === "#associateSection") {
      $("#associateTechnician").show();
      $("#submitComment").hide();
    }
  }

  $('#commentsTabs a[data-toggle="pill"]').on("click", function (event) {
    var targetTab = $(event.target).attr("href");
    toggleButtons(targetTab);
  });

  $("#commentsModal").on("show.bs.modal", function (event) {
    var button = $(event.relatedTarget);
    var idCorretiva = button.data("id");

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

    $.ajax({
      type: "GET",
      url: "/api/tipo_avarias",
      success: function (tiposAvarias) {
        $("#select-avaria")
          .empty()
          .append('<option value="">Selecione um tipo de avaria</option>');

        tiposAvarias.forEach(function (tipo) {
          $("#select-avaria").append(new Option(tipo.tipo, tipo.id));
        });
      },
      error: function () {
        alert("Erro ao carregar tipos de avarias.");
      },
    });

    toggleButtons("#commentSection");
  });

  $("#submitComment").on("click", function () {
    var idCorretiva = $("#corretiva-id").text();
    var tecnicoId = $("#select-tecnico").val();
    var comentario = $("#comment").val();
    var tipoAvariaId = $("#select-avaria").val();
    var parou = $("#select-stop").val();

    if (!tecnicoId) {
      alert("Por favor, registe-se na manutenção para registar atividade.");
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

  $("#associate-pill").on("click", function () {
    var idCorretiva = $("#corretiva-id").text();
    var tecnicoLogadoId = "{{ session['id_mt'] }}";

    if (!tecnicoLogadoId) {
      alert("Por favor, selecione um técnico para associar.");
      return;
    }

    $.ajax({
      type: "GET",
      url: "/api/check_association",
      data: {
        id_corretiva: idCorretiva,
        id_tecnico: tecnicoLogadoId,
      },
      success: function (data) {
        if (data.associado) {
          alert("Você já está associado a esta manutenção.");
          return;
        }

        var confirmation = confirm(
          "Tem a certeza de que deseja se associar a esta manutenção?"
        );

        if (confirmation) {
          $.ajax({
            type: "POST",
            url: "/api/associate_tecnico",
            data: {
              id_corretiva: idCorretiva,
              id_tecnico: tecnicoLogadoId,
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
              alert("Erro ao associar o técnico.");
            },
          });
        } else {
          console.log("Associação cancelada.");
        }
      },
      error: function () {
        alert("Erro ao verificar a associação.");
      },
    });
  });
});
