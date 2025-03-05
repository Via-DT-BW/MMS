document.addEventListener("DOMContentLoaded", function () {
  var newWIForm = document.getElementById("newWIForm");
  var gamaCards = document.getElementById("gamaCards");

  if (newWIForm && gamaCards) {
    newWIForm.addEventListener("show.bs.collapse", function () {
      gamaCards.style.display = "none";
    });
    newWIForm.addEventListener("hide.bs.collapse", function () {
      gamaCards.style.display = "flex";
    });
  }

  const gamaId = "{{ selected_gama_id }}" || null;

  if (gamaId && gamaId !== "None") {
    fetch(`/get_unassigned_tasks/${gamaId}`)
      .then((response) => response.json())
      .then((tasks) => {
        const select = document.getElementById("task_id");
        if (!select) return;

        select.innerHTML =
          '<option value="" disabled selected>Selecione uma tarefa...</option>';

        if (tasks.length > 0) {
          tasks.forEach((task) => {
            const option = document.createElement("option");
            option.value = task.id;
            option.textContent = task.descricao;
            select.appendChild(option);
          });
        } else {
          select.innerHTML =
            '<option value="" disabled selected>Nenhuma tarefa disponível</option>';
        }
      })
      .catch((error) => console.error("Erro ao buscar tarefas:", error));
  }

  const form = document.getElementById("addTaskForm");

  if (form) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();

      let taskId = document.getElementById("task_id").value;
      let gamaId = "{{ selected_gama_id }}" || null;

      if (!gamaId || gamaId === "None") {
        alert("Erro: Nenhuma gama selecionada.");
        return;
      }

      fetch(`/add_task_to_gama`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ tarefa_id: taskId, gama_id: gamaId }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            location.reload();
          } else {
            alert("Erro ao adicionar a tarefa.");
          }
        })
        .catch((error) => console.error("Erro:", error));
    });
  }

  const gamaSelect = document.getElementById("gama_id");
  const associatedTasksList = document.getElementById("associatedTasks");

  if (gamaSelect) {
    gamaSelect.addEventListener("change", function () {
      const gamaId = this.value;

      if (gamaId) {
        fetch(`/get_tasks_for_gama/${gamaId}`)
          .then((response) => response.json())
          .then((tasks) => {
            associatedTasksList.innerHTML = "";

            if (tasks.length > 0) {
              tasks.forEach((task) => {
                let listItem = document.createElement("li");
                listItem.className = "list-group-item";
                listItem.textContent = `${task.id} - ${task.descricao}`;
                associatedTasksList.appendChild(listItem);
              });
            } else {
              associatedTasksList.innerHTML =
                '<li class="list-group-item text-muted">Nenhuma tarefa associada</li>';
            }
          })
          .catch((error) => console.error("Erro ao buscar tarefas:", error));
      } else {
        associatedTasksList.innerHTML =
          '<li class="list-group-item text-muted">Selecione uma gama para visualizar</li>';
      }
    });
  }
});
