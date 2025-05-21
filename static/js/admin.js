document.addEventListener("DOMContentLoaded", function() {
    // Function to toggle password visibility
    function togglePasswordVisibility(passwordField) {
        if (passwordField.type === "password") {
            passwordField.type = "text"; // Change to text
            passwordField.nextElementSibling.querySelector("i").classList.replace("fa-eye", "fa-eye-slash"); // Change icon to eye-slash
        } else {
            passwordField.type = "password"; // Change back to password
            passwordField.nextElementSibling.querySelector("i").classList.replace("fa-eye-slash", "fa-eye"); // Change icon back to eye
        }
    }

    // Add event listeners for password fields (assuming IDs are the same in both templates)
    const currentPasswordField = document.getElementById("currentpassword");
    const newPasswordField = document.getElementById("password");
    const confPasswordField = document.getElementById("confpassword");

    if (currentPasswordField) {
        currentPasswordField.nextElementSibling.addEventListener("click", function() {
            togglePasswordVisibility(currentPasswordField);
        });
    }

    if (newPasswordField) {
        newPasswordField.nextElementSibling.addEventListener("click", function() {
            togglePasswordVisibility(newPasswordField);
        });
    }

    if (confPasswordField) {
        confPasswordField.nextElementSibling.addEventListener("click", function() {
            togglePasswordVisibility(confPasswordField);
        });
    }

    // Function to compare passwords
    function comparePasswords() {
        const confirmMessage = document.getElementById("confirmMessage");
        if (newPasswordField && confPasswordField) {
            if (newPasswordField.value !== confPasswordField.value) {
                confirmMessage.textContent = "Passwords do not match.";
                confirmMessage.classList.add("danger");
            } else {
                confirmMessage.textContent = "";
                confirmMessage.classList.remove("danger");
            }
        }
    }

    // Add event listener for password comparison
    if (confPasswordField) {
        confPasswordField.addEventListener("input", comparePasswords);
    }

    // Form submission validation
    document.getElementById("adminForm").addEventListener("submit", function(event) {
        const requiredFields = document.querySelectorAll("[required]");
        let isEmpty = false;
        let errorMessage = "";

        requiredFields.forEach(function(field) {
            if (field.value.trim() === "") {
                isEmpty = true;
                field.style.border = "1px solid red";
                errorMessage += field.name + " is required.\n";
            } else {
                field.style.border = "";
            }
        });

        if (isEmpty) {
            event.preventDefault();
            document.getElementById("error-message").style.display = "block";
            document.getElementById("error-message").innerText = errorMessage;
        } else {
            document.getElementById("error-message").style.display = "none";
        }
    });
});
