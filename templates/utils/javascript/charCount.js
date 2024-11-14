function updateCharCount(textareaId, countId, buttonId, n) {
  const textarea = document.getElementById(textareaId);
  const countDisplay = document.getElementById(countId);
  const submitButton = document.getElementById(buttonId);
  const charCount = textarea.value.length;

  countDisplay.textContent = `${charCount}/${n}`;

  if (charCount >= n) {
    countDisplay.style.color = "red";
    submitButton.disabled = true;
  } else {
    countDisplay.style.color = "black";
    submitButton.disabled = false;
  }
}
