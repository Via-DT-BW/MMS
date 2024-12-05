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

      fetch("/api/authenticate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(loginData),
      })
        .then((response) => {
          response.json();
        })
        .then((data) => {
          if (data.success) {
            const technicianId = data.technician_id;
            startPreventive(orderNumber, technicianId);
            window.location.reload();
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
    .then((response) => {
      if (response.ok) {
        alert("Preventiva iniciada com sucesso!");
        location.reload();
      } else {
        alert("Erro ao iniciar a preventiva. Tente novamente.");
      }
    })
    .catch((error) => {
      console.error("Erro:", error);
      alert("Ocorreu um erro ao iniciar a preventiva.");
    });
}

function confirmEndPreventive(id) {
  const userConfirmed = confirm(
    "Tem certeza que deseja finalizar a preventiva?"
  );
  if (userConfirmed) {
    fetch(`/end-preventive`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ id: id }),
    })
      .then((response) => {
        if (response.ok) {
          alert("Preventiva finalizada com sucesso!");
          location.reload();
        } else {
          alert("Erro ao finalizar a preventiva. Tente novamente.");
        }
      })
      .catch((error) => {
        console.error("Erro:", error);
        alert("Ocorreu um erro ao finalizar a preventiva.");
      });
  }
}
