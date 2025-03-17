document
  .getElementById("saveEditedRecord")
  .addEventListener("click", function () {
    const form = document.getElementById("editDailyForm");
    const formData = new FormData(form);
    fetch("/api/edit_daily_record", {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.status === "success") {
          location.reload();
        } else {
          alert("Erro ao editar registo: " + data.message);
        }
      })
      .catch((error) => console.error("Erro:", error));
  });

$("#editDailyModal").on("show.bs.modal", function (event) {
  const button = $(event.relatedTarget);
  const id = button.data("id");
  const safety = button.data("safety");
  const quality = button.data("quality");
  const volume = button.data("volume");
  const people = button.data("people");

  const modal = $(this);
  modal.find("#commentId").val(id);
  modal.find("#safetyComment").val(safety);
  modal.find("#qualityComment").val(quality);
  modal.find("#volumeComment").val(volume);
  modal.find("#peopleComment").val(people);

  const imageContainer = modal.find("#existingImages");
  imageContainer.empty();

  $.ajax({
    url: `/api/get_images/${id}`,
    method: "GET",
    success: function (data) {
      if (data.status === "success") {
        data.images.forEach(function (image) {
          const imageElement = `
          <div class="image-wrapper" data-image-id="${image.id}">
            <img src="${image.url}" alt="Imagem associada" style="max-height: 150px;">
            <button type="button" class="btn btn-danger btn-sm remove-image-btn">
              <i class="fa-solid fa-trash"></i>
            </button>
          </div>`;
          imageContainer.append(imageElement);
        });
      }
    },
    error: function () {
      console.error("Erro ao carregar imagens.");
    },
  });
});
