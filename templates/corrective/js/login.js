$(document).ready(function () {
  $("#loginForm").on("submit", function (event) {
    event.preventDefault();

    const formData = {
      username: $("#username").val(),
      password: $("#password").val(),
    };

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
      error: function (error) {
        alert("Erro ao fazer login.");
      },
    });
  });
});
