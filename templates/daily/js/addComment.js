document
  .getElementById("saveDailyRecord")
  .addEventListener("click", function () {
    const form = document.getElementById("addDailyForm");
    const formData = new FormData(form);
    fetch("/api/add_daily_record", {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.status === "success") {
          location.reload();
        } else {
          alert("Erro ao adicionar registo: " + data.message);
        }
      })
      .catch((error) => console.error("Erro:", error));
  });
