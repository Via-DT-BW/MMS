function mostrarGamas(equipamentoId) {
  var gamasContainer = document.getElementById("gamas-" + equipamentoId);

  if (gamasContainer.style.display === "block") {
    gamasContainer.style.display = "none";
    return;
  }

  gamasContainer.style.display = "block";

  $.ajax({
    url: "/gamas_do_equipamento/" + equipamentoId,
    method: "GET",
    success: function (response) {
      var gamasBody = document.getElementById("gamas-body-" + equipamentoId);
      gamasBody.innerHTML = "";

      response.forEach(function (gama) {
        var row = `
          <tr>
            <td>${gama.gama_desc}</td>
            <td>${gama.periocity}</td>
            <td>
              <button class="btn btn-warning btn-sm" onclick="editarGama(${equipamentoId}, ${gama.gama_id}, event)">
                <i class="fa-solid fa-pen-to-square"></i>
              </button>
              <button class="btn btn-danger btn-sm" onclick="deleteLink(${equipamentoId}, ${gama.gama_id}, ${gama.periocity_id}, event)">
                <i class="fa-solid fa-link-slash"></i>
              </button>
            </td>
            
          </tr>
        `;
        gamasBody.innerHTML += row;
      });
    },
    error: function () {
      alert("Erro ao carregar as gamas.");
    },
  });
}

function deleteLink(equipamentoId, gamaId, periocity_id, event) {
  event.stopPropagation();

  if (
    !confirm(
      "Tem certeza que deseja remover este associação entre esta gama e equipamento?"
    )
  ) {
    return;
  }

  $.ajax({
    url: "/unlink_gama/",
    method: "DELETE",
    contentType: "application/json",
    data: JSON.stringify({
      id_equipment: equipamentoId,
      id_gama: gamaId,
      id_periocity: periocity_id,
    }),
    success: function (response) {
      console.log(response);
      alert("Vínculo removido com sucesso!");
      location.reload();
    },
    error: function () {
      alert("Erro ao remover o vínculo.");
    },
  });
}

function editarGama(equipamentoId, gamaId, event) {
  event.stopPropagation();

  $.ajax({
    url: "/get_gama_e_periocidade/" + gamaId,
    method: "GET",
    success: function (response) {
      console.log(response);
      document.getElementById("equipamentoEdit").value = response.equipamento;
      document.getElementById("gama").value = response.gama_desc;
      document.getElementById("periodicidade").value = response.periocity_id;

      document.getElementById("equipamentoId").value = response.equipamento_id;
      document.getElementById("gamaId").value = response.id_gama;
      document.getElementById("periocidadeOldId").value = response.periocity_id;

      $.ajax({
        url: "/get_periocities",
        method: "GET",
        success: function (periocidadesResponse) {
          console.log(periocidadesResponse);

          var selectPeriodicity = document.getElementById("periodicidade");

          selectPeriodicity.innerHTML = "";

          periocidadesResponse.forEach(function (periocity) {
            var option = document.createElement("option");
            option.value = periocity.id;
            option.textContent = periocity.periocity;
            selectPeriodicity.appendChild(option);
          });
          selectPeriodicity.value = response.periocity_id;
          $("#editGamaModal").modal("show");
        },
        error: function () {
          alert("Erro ao carregar as periocidades.");
        },
      });
    },
    error: function () {
      alert("Erro ao carregar os dados da gama.");
    },
  });
}

function salvarEdicao() {
  var equipamentoId = document.getElementById("equipamentoId").value;
  var gamaDesc = document.getElementById("gama").value;
  var periocityId = document.getElementById("periodicidade").value;
  var gamaId = document.getElementById("gamaId").value;
  var oldPeriocityId = document.getElementById("periocidadeOldId").value;

  $.ajax({
    url: "/update_gama_e_periocidade",
    method: "POST",
    contentType: "application/json",
    data: JSON.stringify({
      equipamentoId: equipamentoId,
      gamaDesc: gamaDesc,
      periocityId: periocityId,
      idGama: gamaId,
      oldPeriocityId: oldPeriocityId,
    }),
    success: function (response) {
      if (response.success) {
        location.reload();
      } else {
        alert("Erro ao atualizar a gama.");
      }
    },
    error: function () {
      alert("Erro ao salvar as alterações.");
    },
  });
}

function mostrarAdicionarGama() {
  carregarPeriocities();
  $("#modalAdicionarGama").modal("show");
}

function mostrarAdicionarEquip(cost_center) {
  document.getElementById("costCenter").value = cost_center;

  $("#adicionarEquipModal").modal("show");
}

function salvarEquipamento() {
  var costCenter = document.getElementById("costCenter").value;
  var equipamentoNome = document.getElementById("equipamentoNome").value;
  var equipamentoDesc = document.getElementById("equipamentoDesc").value;

  $.ajax({
    url: "/adicionar_equipamento",
    method: "POST",
    contentType: "application/json",
    data: JSON.stringify({
      costCenter: costCenter,
      equipment: equipamentoNome,
      descricao: equipamentoDesc,
    }),
    success: function (response) {
      if (response.success) {
        location.reload();
      } else {
        alert("Erro ao salvar o equipamento.");
      }
    },
    error: function () {
      alert("Erro ao salvar o equipamento.");
    },
  });
}
