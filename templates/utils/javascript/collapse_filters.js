document.addEventListener("DOMContentLoaded", function () {
  const filterCollapse = document.getElementById("filterCollapse");
  const filterToggleBtn = document.getElementById("filterToggleBtn");
  const filterIcon = document.getElementById("filterIcon");

  if (window.innerWidth < 768) {
    filterCollapse.classList.remove("show");
  }
  function updateButtonState() {
    if (filterCollapse.classList.contains("show")) {
      filterToggleBtn.classList.remove("btn-outline-success");
      filterToggleBtn.classList.add("btn-outline-danger");
      filterIcon.classList.remove("a-angle-down");
      filterIcon.classList.add("fa-angle-up");
    } else {
      filterToggleBtn.classList.remove("btn-outline-danger");
      filterToggleBtn.classList.add("btn-outline-success");
      filterIcon.classList.remove("fa-angle-up");
      filterIcon.classList.add("fa-angle-down");
    }
  }

  filterCollapse.addEventListener("shown.bs.collapse", updateButtonState);
  filterCollapse.addEventListener("hidden.bs.collapse", updateButtonState);

  updateButtonState();
});
