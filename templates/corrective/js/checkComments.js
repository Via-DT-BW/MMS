function checkComments() {
  var tecnicoId = "{{ session['id_mt'] }}";

  var formData = {
    id_tecnico: tecnicoId,
  };

  $.ajax({
    url: "/api/check_comments",
    type: "POST",
    contentType: "application/json",
    data: JSON.stringify(formData),
    success: function (response) {
      const button = document.getElementById("comentariosPendentesBtn");
      const alertIcon = document.getElementById("alertIcon");

      if (response.status === "success") {
        if (response.has_pending_comments === "SIM") {
          button.style.backgroundColor = "#f39c12";
          alertIcon.style.display = "inline";
          button.style.color = "#00386C";
          button.style.fontWeight = "bold";
        } else {
          button.style.backgroundColor = "";
          alertIcon.style.display = "none";
        }
      } else {
        alert("Erro: " + response.message);
      }
    },
    error: function () {
      alert("Erro ao verificar os comentários.");
    },
  });
}

setInterval(checkComments, 600000);

checkComments();