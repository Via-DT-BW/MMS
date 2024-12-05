$(document).ready(function () {
  $("#card_num").on("keypress", function (event) {
    if (event.key === "Enter") {
      event.preventDefault();

      const cardNum = $(this).val().trim();
      if (cardNum) {
        const formData = { card: cardNum };

        $.ajax({
          url: "/login_corrective",
          type: "POST",
          contentType: "application/json",
          data: JSON.stringify(formData),
          success: function (response) {
            if (response.success) {
              location.reload();
            } else {
              alert("Erro: " + response.error);
            }
          },
          error: function () {
            alert("Erro ao fazer login.");
          },
        });
      } else {
        alert("Por favor, insira um cartão válido.");
      }
    }
  });

  $("#loginForm").on("submit", function (event) {
    event.preventDefault();

    const cardNum = $("#card_num").val().trim();
    const username = $("#username").val().trim();
    const password = $("#password").val().trim();

    let formData = {};

    if (cardNum) {
      formData = { card: cardNum };
    } else if (username && password) {
      formData = { username: username, password: password };
    } else {
      alert("Por favor, preencha o cartão ou username/senha.");
      return;
    }

    $.ajax({
      url: "/login_corrective",
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify(formData),
      success: function (response) {
        if (response.success) {
          window.location.href = "/notifications";
        } else {
          alert("Erro: " + response.error);
        }
      },
      error: function () {
        alert("Erro ao fazer login.");
      },
    });
  });
});
