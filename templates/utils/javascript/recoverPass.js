document.addEventListener("DOMContentLoaded", function () {
  $("a[data-toggle='modal'][data-target='#modalForgotPassword']").on(
    "click",
    function () {
      $(".modal").modal("hide");
    }
  );

  document
    .getElementById("forgotPasswordForm")
    .addEventListener("submit", function (e) {
      e.preventDefault();

      const recoverUsername = document.getElementById("recover-username").value;

      fetch("/recover_password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username: recoverUsername }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.message) {
            alert(data.message);
            $("#modalForgotPassword").modal("hide");
            window.location.reload();
          } else if (data.error) {
            alert(data.error);
          }
        })
        .catch((error) => {
          console.error("Erro:", error);
          alert("Houve um erro ao enviar o e-mail de recuperação.");
        });
    });
});
