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
                              <td>${comment.n_tecnico}</td>
                              <td>${comment.tecnico_nome}</td>
                              <td>${comment.maintenance_comment}</td>
                              <td>${comment.tipo_avaria}</td>
                              <td>${comment.duracao_intervencao} minutos</td>
                              <td>${formatDateTime(comment.data_inicio)}</td>
                              <td>${formatDateTime(comment.data_fim)}</td>
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
