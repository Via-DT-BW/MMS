function formatDateTime(dateTimeString) {
  const options = {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  };
  const date = new Date(dateTimeString);
  return date.toLocaleString("pt-BR", options);
}

function convertToValidDateFormat(dateString) {
  const [datePart, timePart] = dateString.split(",");
  const [day, month, year] = datePart.split("/");
  return new Date(`${year}-${month}-${day}T${timePart.trim()}`);
}

function getColorForDate(dateString) {
  const originalDate = convertToValidDateFormat(dateString);
  const now = new Date();

  if (isNaN(originalDate)) {
    console.error("Data inválida:", dateString);
    return {};
  }

  const dateOnly = new Date(originalDate);
  dateOnly.setHours(0, 0, 0, 0);

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  if (dateOnly < today) {
    return { backgroundColor: "#f8d2d2", className: "table-danger" };
  } else if (dateOnly.getTime() === today.getTime()) {
    const diffMinutes = (now - originalDate) / 60000;
    if (diffMinutes > 30) {
      return { backgroundColor: "#f8d2d2", className: "table-danger" };
    } else {
      return { backgroundColor: "#f8f8d2", className: "table-warning" };
    }
  } else if (dateOnly > today) {
    return { backgroundColor: "#d2f8d2", className: "table-success" };
  }
  return {};
}

document.addEventListener("DOMContentLoaded", () => {
  const dateCells = document.querySelectorAll(".data");
  const table = document.getElementById("notifications");

  dateCells.forEach((cell) => {
    cell.textContent = formatDateTime(cell.textContent);

    if (cell.closest("table") === table) {
      const row = cell.closest("tr");
      const color = getColorForDate(cell.textContent);

      if (color.backgroundColor && color.className) {
        row.style.backgroundColor = color.backgroundColor;
        row.classList.add(color.className);
      }
    }
  });
});
