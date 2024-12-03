function confirmStartPreventive(orderNumber) {
  const userConfirmed = confirm("Tem certeza que deseja iniciar a preventiva?");
  if (userConfirmed) {
    fetch(`/start-preventive`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ order_number: orderNumber }),
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
}

function confirmEndPreventive(id) {
  const userConfirmed = confirm(
    "Tem certeza que deseja finalizar a preventiva?"
  );
  if (userConfirmed) {
    fetch(`/start-preventive`, {
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
