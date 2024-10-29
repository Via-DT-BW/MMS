function formatDateTime(dateTimeString) {
  const options = {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false, // false para 24 horas
  };
  const date = new Date(dateTimeString);
  return date.toLocaleString("pt-BR", options);
}
