$("#dailyDetailsModal").on("show.bs.modal", function (event) {
  var button = $(event.relatedTarget);
  var safetyComment = button.data("safety");
  var qualityComment = button.data("quality");
  var volumeComment = button.data("volume");
  var peopleComment = button.data("people");
  var dailyId = button.data("id");

  var modal = $(this);
  modal.find("#modalSafetyComment").val(safetyComment);
  modal.find("#modalQualityComment").val(qualityComment);
  modal.find("#modalVolumeComment").val(volumeComment);
  modal.find("#modalPeopleComment").val(peopleComment);

  var imageContainer = modal.find("#dailyImagesContainer");
  imageContainer.empty();

  $.ajax({
    url: `/api/get_images/${dailyId}`,
    method: "GET",
    success: function (data) {
      console.log("Resposta do AJAX:", data);
      if (data.status === "success") {
        data.images.forEach(function (image) {
          var imageElement = `
          <div class="daily-image-wrapper" data-image-id="${image.id}">
            <img src="${image.url}" alt="Imagem associada" style="max-height: 150px;">
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

$(document).on("click", ".daily-image-wrapper img", function (event) {
  event.preventDefault();
  $(this).toggleClass("enlarged");
});
