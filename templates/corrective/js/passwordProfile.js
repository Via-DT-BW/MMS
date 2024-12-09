document
  .getElementById("toggle-sap-password")
  .addEventListener("click", function () {
    var sapPasswordField = document.getElementById("sap_pass");
    var eyeIconSap = document.getElementById("eye-icon-sap");

    if (sapPasswordField.type === "password") {
      sapPasswordField.type = "text";
      eyeIconSap.classList.remove("fa-eye");
      eyeIconSap.classList.add("fa-eye-slash");
    } else {
      sapPasswordField.type = "password";
      eyeIconSap.classList.remove("fa-eye-slash");
      eyeIconSap.classList.add("fa-eye");
    }
  });

document
  .getElementById("toggle-password")
  .addEventListener("click", function () {
    var passwordField = document.getElementById("password");
    var eyeIcon = document.getElementById("eye-icon");

    if (passwordField.type === "password") {
      passwordField.type = "text";
      eyeIcon.classList.remove("fa-eye");
      eyeIcon.classList.add("fa-eye-slash");
    } else {
      passwordField.type = "password";
      eyeIcon.classList.remove("fa-eye-slash");
      eyeIcon.classList.add("fa-eye");
    }
  });
