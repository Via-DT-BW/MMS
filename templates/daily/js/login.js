document.getElementById("loginButton").addEventListener("click", function () {
  const form = document.getElementById("loginForm");
  const formData = new FormData(form);

  fetch("/login_daily", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        window.location.href = "/daily";
      } else {
        alert("Erro ao fazer login: " + data.error);
      }
    })
    .catch((error) => console.error("Erro:", error));
});
