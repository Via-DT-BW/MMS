function showLines() {
  fetch(`/api/lines_per_area`)
    .then((response) => response.json())
    .then((data) => {
      const content = document.getElementById("linesOffcanvasContent");

      if (!content) {
        console.error("Elemento 'linesOffcanvasContent' não encontrado.");
        return;
      }

      if (data.length === 0) {
        content.innerHTML =
          "<p class='text-muted'>Nenhuma linha encontrada.</p>";
      } else {
        content.innerHTML = "";

        data.forEach((area, index) => {
          const areaContainer = document.createElement("div");
          areaContainer.className = "list-group-item";

          const areaTitle = document.createElement("p");
          areaTitle.textContent = `${area.area} - ${area.PL}`;
          areaTitle.className = "mb-0 fw-bold";
          areaTitle.style.cursor = "pointer";
          areaTitle.dataset.target = `dropdown-${index}`;

          const linhasDropdown = document.createElement("ul");
          linhasDropdown.className = "dropdown-menu mt-2 collapse";
          linhasDropdown.id = `dropdown-${index}`;

          const linhasArray = area.linhas.split(", ");
          linhasArray.forEach((linha) => {
            const linhaItem = document.createElement("li");
            const linhaLink = document.createElement("a");
            linhaLink.className = "dropdown-item";
            linhaLink.href = "#";
            linhaLink.textContent = linha;
            linhaItem.appendChild(linhaLink);
            linhasDropdown.appendChild(linhaItem);
          });

          areaTitle.addEventListener("click", () => {
            const allDropdowns = document.querySelectorAll(".dropdown-menu");
            allDropdowns.forEach((dropdown) => {
              if (dropdown !== linhasDropdown) {
                dropdown.classList.remove("show");
                dropdown.classList.add("collapse");
              }
            });

            linhasDropdown.classList.toggle("collapse");
            linhasDropdown.classList.toggle("show");
          });

          areaContainer.appendChild(areaTitle);
          areaContainer.appendChild(linhasDropdown);

          content.appendChild(areaContainer);
        });
      }

      const offcanvasElement = document.getElementById("linesOffcanvas");
      const bsOffcanvas = new bootstrap.Offcanvas(offcanvasElement);
      bsOffcanvas.show();
    })
    .catch((error) => {
      console.error("Erro ao procurar linhas:", error);
      const content = document.getElementById("linesOffcanvasContent");

      if (content) {
        content.innerHTML =
          "<p class='text-danger'>Erro ao carregar linhas.</p>";
      }

      const offcanvasElement = document.getElementById("linesOffcanvas");
      const bsOffcanvas = new bootstrap.Offcanvas(offcanvasElement);
      bsOffcanvas.show();
    });
}
