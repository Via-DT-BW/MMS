function toggleComments(id) {
  const row = document.getElementById(`comments-${id}`);
  if (row.style.display === "table-row") {
    row.style.display = "none";
  } else {
    fetch(`/api/get-corretiva-comments?idCorretiva=${id}`)
      .then((response) => response.json())
      .then((data) => {
        if (data && data.length > 0) {
          const commentsTableBody = row.querySelector(".comments-table-body");
          commentsTableBody.innerHTML = "";

          data.forEach((comment) => {
            const row = document.createElement("tr");
            row.innerHTML = `
                              <td data-label="Técnico">${
                                comment.tecnico_nome
                              } - ${comment.n_tecnico}</td>
                              <td data-label="Comentário">${
                                comment.maintenance_comment
                              }</td>
                              <td data-label="Tipo de Avaria">${
                                comment.tipo_avaria
                              }</td>
                              <td data-label="Duração">${
                                comment.duracao_intervencao
                              } minutos</td>
                              <td data-label="Data de Início">${formatDateTime(
                                comment.data_inicio
                              )}</td>
                              <td data-label="Data de Fim">${formatDateTime(
                                comment.data_fim
                              )}</td>
                              <td data-label="Fotos"><button class="btn btn-primary" onclick="showPhotos(${
                                comment.id
                              })"><i class="fas fa-images"></i></button></td> 
                          `;
            commentsTableBody.appendChild(row);
          });
        } else {
          const commentsTableBody = row.querySelector(".comments-table-body");
          commentsTableBody.innerHTML =
            '<tr><td colspan="7" class="text-muted text-center">Sem comentários disponíveis</td></tr>';
        }
      })
      .catch((error) => {
        console.error("Erro ao carregar os comentários:", error);
      });

    row.style.display = "table-row";
  }
}

function showPhotos(id) {
  fetch(`/api/get-ct-photos?id=${id}`)
    .then((response) => response.json())
    .then((data) => {
      if (data && data.length > 0) {
        let modalHtml = `
          <div class="modal fade" id="photosModal" tabindex="-1" role="dialog" aria-labelledby="photosModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg" role="document">
              <div class="modal-content">
                <div class="modal-header">
                  <h5 class="modal-title" id="photosModalLabel">Fotos</h5>
                  <button type="button" class="close" data-bs-dismiss="modal" aria-label="Fechar">
                    <span aria-hidden="true">&times;</span>
                  </button>
                </div>
                <div class="modal-body">
                  <div class="row">
        `;

        data.forEach((photo) => {
          modalHtml += `
            <div class="col-md-6 col-9">
              <img src="${photo}" class="img-fluid mb-3" alt="Foto" style="max-width:100%; max-height:500px;">
            </div>
          `;
        });

        modalHtml += `
                  </div>
                </div>
                <div class="modal-footer">
                  <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
                </div>
              </div>
            </div>
          </div>
        `;

        const existingModal = document.getElementById("photosModal");
        if (existingModal) {
          existingModal.parentNode.removeChild(existingModal);
        }
        document.body.insertAdjacentHTML("beforeend", modalHtml);

        $("#photosModal").modal("show");
      } else {
        toastr.info("Nenhuma foto disponível para este comentário.");
      }
    })
    .catch((error) => {
      console.error("Erro ao carregar as fotos:", error);
    });
}
