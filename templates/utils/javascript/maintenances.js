$(document).ready(function () {
  $("#modalCorrective").on("show.bs.modal", function () {
    loadLines();

    $("#linha-select").change(function () {
      const linhaSelecionada = $(this).val();

      if (linhaSelecionada) {
        $.ajax({
          url: `/api/corrective?machine=${linhaSelecionada}`,
          type: "GET",
          success: function (data) {
            populateModalFields(data);
            $("#equipament_var, #var_descricao, #var_numero_operador").prop(
              "disabled",
              false
            );
          },
          error: function () {
            alert("Erro ao carregar dados do modal");
          },
        });
      }
    });
  });

  function loadLines() {
    $.ajax({
      url: "/api/prod_lines",
      method: "GET",
      success: function (data) {
        let lineSelect = $('select[name="production_line"]');
        lineSelect.empty();
        lineSelect.append('<option value="">Selecione a linha</option>');
        data.sort((a, b) => a.line.localeCompare(b.line));

        data.forEach((line) => {
          lineSelect.append(
            `<option value="${line.line}">${line.line}</option>`
          );
        });

        disableFields(true);
      },
      error: function () {
        alert("Erro ao carregar as linhas.");
      },
    });
  }

  $("#createOrder").on("click", function () {
    var tecnicoId = "{{ session['id_mt'] }}";

    $.ajax({
      type: "GET",
      url: "/api/check_association",
      data: { id_tecnico: tecnicoId },
      success: function (response) {
        if (response.associado) {
          alert(
            "Você já está associado a outra manutenção. Finalize-a antes de iniciar uma nova."
          );
          return;
        } else {
          $("#modalCorrectiveOrder").modal("show");

          loadLines();

          const tecnicoSelect = $("#tecnico-select");

          $("#linha-select")
            .off("change")
            .on("change", function () {
              const linhaSelecionada = $(this).val();

              if (linhaSelecionada) {
                $.ajax({
                  url: `/api/corrective?machine=${linhaSelecionada}`,
                  type: "GET",
                  success: function (data) {
                    populateModalFields(data);
                    $(
                      "#equipament_var, #var_descricao, #var_numero_tecnico"
                    ).prop("disabled", false);
                  },
                  error: function () {
                    alert("Erro ao carregar dados do modal");
                  },
                });
              }
            });
        }
      },
      error: function () {
        alert("Erro ao verificar a associação do técnico.");
      },
    });
  });

  function disableFields(disable) {
    $('select[name="var_descricao"]').prop("disabled", disable);
    $('select[name="equipament_var"]').prop("disabled", disable);
    $('select[name="var_numero_operador"]').prop("disabled", disable);
    $('select[name="paragem_producao"]').prop("disabled", disable);
    $('select[name="tipo_manutencao"]').prop("disabled", disable);
  }

  $('select[name="production_line"]').change(function () {
    let selectedLine = $(this).val();
    if (selectedLine) {
      $.ajax({
        url: "/api/corrective",
        method: "GET",
        data: { machine: selectedLine },
        success: function (data) {
          populateModalFields(data);
          disableFields(false);
        },
        error: function () {
          alert("Erro ao carregar dados da linha.");
        },
      });
    } else {
      disableFields(true);
    }
  });

  function populateModalFields(data) {
    const descriptionSelect = $('select[name="var_descricao"]');
    const equipamentSelect = $('select[name="equipament_var"]');
    const operatorSelect = $('select[name="var_numero_operador"]');
    const tecnicos = $('select[name="var_numero_tecnico"]');

    descriptionSelect.empty();
    equipamentSelect.empty();
    operatorSelect.empty();

    if (data.select_description_fiori.length > 0) {
      descriptionSelect.append(
        '<option value="">Selecione a descrição da avaria.</option>'
      );
      data.select_description_fiori.forEach((desc) => {
        descriptionSelect.append(
          `<option value="${desc.descricao}">${desc.descricao}</option>`
        );
      });
    } else {
      descriptionSelect.append(
        '<option value="">Sem descrições registadas</option>'
      );
    }

    if (data.maquinas_sap.length > 0) {
      equipamentSelect.append(
        '<option value="">Selecione o número da máquina.</option>'
      );
      data.maquinas_sap.forEach((machine) => {
        equipamentSelect.append(
          `<option value="${machine.id}">${machine.id} - ${machine.description}</option>`
        );
      });
    } else {
      equipamentSelect.append(
        '<option value="">Sem equipamentos registados</option>'
      );
    }

    if (data.ongoing_operators.length > 0) {
      operatorSelect.append('<option value="">Selecione o Operador</option>');
      data.ongoing_operators.forEach((operator) => {
        operatorSelect.append(
          `<option value="${operator.usernumber}">${operator.usernumber} - ${operator.nome}</option>`
        );
      });
    } else {
      operatorSelect.append(
        '<option value="">Sem operadores registados</option>'
      );
    }
  }
});
