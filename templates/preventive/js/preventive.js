function parseFormattedDate(dateStr) {
  const parts = dateStr.split("-");
  if (parts.length !== 3) {
    return new Date(dateStr);
  }
  const day = parseInt(parts[0], 10);
  const month = parseInt(parts[1], 10) - 1;
  const year = parseInt(parts[2], 10);
  return new Date(year, month, day);
}

function formatDate(dateString) {
  const date = new Date(dateString);
  if (isNaN(date)) {
    return dateString;
  }
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const year = String(date.getFullYear());
  return `${day}-${month}-${year}`;
}

function updateRowColors() {
  const table = document.getElementById("orders");
  if (!table) return;

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const rows = table.querySelectorAll("tbody tr");
  rows.forEach((row) => {
    const dateCells = row.querySelectorAll(".data");
    if (dateCells.length < 2) return;

    const startDateStr = dateCells[0].textContent.trim();
    const endDateStr = dateCells[1].textContent.trim();

    const startDate = parseFormattedDate(startDateStr);
    const endDate = parseFormattedDate(endDateStr);

    if (!isNaN(startDate.getTime()) && !isNaN(endDate.getTime())) {
      if (endDate < today) {
        row.style.backgroundColor = "#f8d2d2";
      } else if (startDate <= today && endDate >= today) {
        row.style.backgroundColor = "#f8f8d2";
      } else if (startDate > today) {
        row.style.backgroundColor = "#d2f8d2";
      }
    }
  });
}

document.addEventListener("DOMContentLoaded", function () {
  $("#loginPreventive").on("shown.bs.modal", function (event) {
    const form = document.getElementById("loginForm");
    if (form) {
      form.reset();
    }

    var button = $(event.relatedTarget);
    const orderNumber = button.data("order");
    $(this).data("orderNumber", orderNumber);

    const cardNumField = document.getElementById("cardNum");
    if (cardNumField) {
      cardNumField.focus();
    } else {
      console.error("Elemento #cardNum não encontrado no DOM.");
    }
  });

  function formatDate(dateString) {
    const date = new Date(dateString);
    if (isNaN(date)) {
      return dateString;
    }
    const day = String(date.getDate()).padStart(2, "0");
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const year = String(date.getFullYear());
    return `${day}-${month}-${year}`;
  }

  function formatDatetime(dateString) {
    const date = new Date(dateString);

    if (isNaN(date.getTime())) {
      return dateString;
    }

    const day = String(date.getDate()).padStart(2, "0");
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const year = date.getFullYear();
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");

    return `${day}-${month}-${year} ${hours}:${minutes}`;
  }

  const dataCells = document.querySelectorAll(".data");
  dataCells.forEach((cell) => {
    cell.textContent = formatDate(cell.textContent.trim());
  });

  updateRowColors();

  document
    .getElementById("loginForm")
    .addEventListener("submit", function (event) {
      event.preventDefault();

      const cardNum = document.getElementById("cardNum")?.value || "";
      const username = document.getElementById("username")?.value || "";
      const password = document.getElementById("password")?.value || "";
      const orderNumber = $("#loginPreventive").data("orderNumber");

      if (!cardNum && (!username || !password)) {
        alert("Por favor, preencha o cartão ou as credenciais.");
        return;
      }

      const loginData = cardNum
        ? { card_number: cardNum }
        : { username: username, password: password };

      console.log(loginData);
      fetch("/api/authenticate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(loginData),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            const technicianId = data.technician_id;
            startPreventive(orderNumber, technicianId);
          } else {
            alert(data.message || "Erro na autenticação. Tente novamente.");
          }
        })
        .catch((error) => {
          console.error("Erro:", error);
          alert("Erro ao autenticar. Tente novamente.");
        });
    });
});

let ordemIdParaFinalizar = null;

function abrirModalFinalizar(id) {
  ordemIdParaFinalizar = id;
  $("#modalComentarioFinalizar").modal("show");
}

function startPreventive(orderNumber, technicianId) {
  fetch("/start-preventive", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      order_number: orderNumber,
      technician_id: technicianId,
    }),
  })
    .then(async (response) => {
      const data = await response.json();
      if (response.ok) {
        $("#preventiveModal").modal("hide");
        location.reload();
      } else {
        if (
          data.error &&
          data.error.includes("Já está a executar uma preventiva")
        ) {
          $("#preventiveModal").modal("hide");
          location.reload();
        } else {
          alert("Erro ao iniciar a preventiva: " + data.error);
        }
      }
    })
    .catch((error) => {
      console.error("Erro:", error);
      alert("Ocorreu um erro ao iniciar a preventiva.");
    });
}

function submeterFinalizacao() {
  const comentario = document
    .getElementById("comentarioFinalizar")
    .value.trim();

  if (!comentario) {
    alert("É necessário inserir um comentário para finalizar a preventiva.");
    return;
  }

  $("#modalComentarioFinalizar").modal("hide");

  fetch(`/end-preventive`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: ordemIdParaFinalizar, comentario: comentario }),
  })
    .then((response) => {
      if (response.ok) {
        location.reload();
      } else {
        alert("Erro ao finalizar a preventiva.");
      }
    })
    .catch((error) => {
      console.error("Erro:", error);
      alert("Ocorreu um erro ao finalizar a preventiva.");
    });
}

function pausarIntervencao(orderId) {
  if (confirm("Tem certeza de que deseja interromper esta intervenção?")) {
    $.ajax({
      url: "/pause_intervention/" + orderId,
      method: "POST",
      success: function (response) {
        alert(response.message);
        location.reload();
      },
      error: function () {
        alert("Erro ao pausar a intervenção.");
      },
    });
  }
}

function retomarIntervencao(orderId) {
  if (confirm("Tem certeza de que deseja retomar esta intervenção?")) {
    $.ajax({
      url: "/resume_intervention/" + orderId,
      method: "POST",
      success: function (response) {
        alert(response.message);
        location.reload();
      },
      error: function () {
        alert("Erro ao retomar a intervenção.");
      },
    });
  }
}
