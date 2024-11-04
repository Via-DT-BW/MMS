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
    console.log("Aba ativada:", targetTab);
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
      .append('<option value="">Selecione um técnico</option>');

    $.ajax({
      type: "GET",
      url: "/api/get_tecnicos_associados/" + idCorretiva,
      success: function (tecnicosAssociados) {
        tecnicosAssociados.forEach(function (tecnico) {
          var optionText = tecnico.nome + " - " + tecnico.n_tecnico;
          $("#select-tecnico").append(new Option(optionText, tecnico.id));
        });

        $.ajax({
          type: "GET",
          url: "/api/tecnicos",
          success: function (todosOsTecnicos) {
            $("#select-new-tecnico").empty();
            $("#select-new-tecnico").append(
              '<option value="">Selecione um técnico</option>'
            );

            todosOsTecnicos.forEach(function (tecnico) {
              if (!tecnicosAssociados.some((t) => t.id === tecnico.id)) {
                var optionText = tecnico.nome + " - " + tecnico.n_tecnico;
                $("#select-new-tecnico").append(
                  new Option(optionText, tecnico.id)
                );
              }
            });
          },
          error: function () {
            alert("Erro ao carregar todos os técnicos.");
          },
        });
      },
      error: function () {
        alert("Erro ao carregar técnicos associados.");
      },
    });

    toggleButtons("#commentSection");
  });

  $("#submitComment").on("click", function () {
    var idCorretiva = $("#corretiva-id").text();
    var tecnicoId = $("#select-tecnico").val();
    var comentario = $("#comment").val();

    if (!tecnicoId || !comentario) {
      alert("Por favor, selecione um técnico e adicione um comentário.");
      return;
    }

    $.ajax({
      type: "POST",
      url: "/api/update_comment",
      data: {
        id_corretiva: idCorretiva,
        id_tecnico: tecnicoId,
        comment: comentario,
      },
      success: function (response) {
        if (response.status === "success") {
          alert("Comentário adicionado com sucesso!");
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

  $("#associateTechnician").on("click", function () {
    var idCorretiva = $("#corretiva-id").text();
    var newTecnicoId = $("#select-new-tecnico").val();

    if (!newTecnicoId) {
      alert("Por favor, selecione um técnico para associar.");
      return;
    }

    $.ajax({
      type: "POST",
      url: "/api/associate_tecnico",
      data: {
        id_corretiva: idCorretiva,
        id_tecnico: newTecnicoId,
      },
      success: function (response) {
        if (response.status === "success") {
          alert("Técnico associado com sucesso!");
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
  });
});
