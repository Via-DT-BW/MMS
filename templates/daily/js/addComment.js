document
  .getElementById("saveDailyRecord")
  .addEventListener("click", function () {
    const form = document.getElementById("addDailyForm");
    const formData = new FormData(form);
    console.log(formData);
    fetch("/api/add_daily_record", {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          location.reload();
        } else {
          alert("Erro ao adicionar registo: " + data.error);
        }
      })
      .catch((error) => console.error("Erro:", error));
  });
