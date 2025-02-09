// Toggle menu function for burger icon
function toggleMenu(burger) {
  burger.classList.toggle("open");
  document.querySelector(".nav-links").classList.toggle("menu-active");
}

// Show/hide password functionality for both fields (check if elements exist)
const passwordField = document.getElementById('password');
const confirmPasswordField = document.getElementById('confirmPassword');
const togglePassword = document.getElementById('togglePassword');
const toggleConfirmPassword = document.getElementById('toggleConfirmPassword');

// Show the eye icon only when user starts typing in the password field
if (passwordField && togglePassword) {
  passwordField.addEventListener('input', () => {
    togglePassword.style.display = passwordField.value ? 'block' : 'none';
  });

  togglePassword.addEventListener('click', () => {
    const type = passwordField.type === 'password' ? 'text' : 'password';
    passwordField.type = type;
    togglePassword.classList.toggle('fa-eye');
    togglePassword.classList.toggle('fa-eye-slash');
  });
}

// Show the eye icon only when user starts typing in the confirm password field
if (confirmPasswordField && toggleConfirmPassword) {
  confirmPasswordField.addEventListener('input', () => {
    toggleConfirmPassword.style.display = confirmPasswordField.value ? 'block' : 'none';
  });

  toggleConfirmPassword.addEventListener('click', () => {
    const type = confirmPasswordField.type === 'password' ? 'text' : 'password';
    confirmPasswordField.type = type;
    toggleConfirmPassword.classList.toggle('fa-eye');
    toggleConfirmPassword.classList.toggle('fa-eye-slash');
  });
}


// Function to show code container when a card is clicked
function showCodeContainer() {
  const codeContainer = document.getElementById("code-container");

  // Show the code container
  codeContainer.classList.remove("hidden");
}



//Sidebar

// Toggle Sidebar on Mobile
function toggleSidebar() {
  document.querySelector('.sidebar').classList.toggle('active');
  document.querySelector('.burger').classList.toggle('active');
}

// Toggle Dropdown Menu on Click
const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
dropdownToggles.forEach(toggle => {
  toggle.addEventListener('click', function() {
    const dropdown = this.nextElementSibling;  // Get the next sibling (dropdown)
    dropdown.classList.toggle('active');  // Toggle the visibility of dropdown
  });
});

// Close dropdown if clicked outside
document.addEventListener('click', function(event) {
  const sidebar = document.getElementById('sidebar');
  if (!sidebar.contains(event.target)) {
    const openDropdowns = document.querySelectorAll('.dropdown.active');
    openDropdowns.forEach(dropdown => {
      dropdown.classList.remove('active');  // Close dropdowns if clicked outside
    });
  }
});


//Copy icon
document.addEventListener("DOMContentLoaded", () => {
  const copyIcon = document.querySelector(".copy .fa-copy"); // Select the copy icon
  const h3Element = document.querySelector(".copy h3"); // Select the <h3> element
  const copyMessage = document.getElementById("copyMessage"); // Select the message span

  if (copyIcon && h3Element && copyMessage) { // Check if elements exist
    copyIcon.addEventListener("click", () => {
      const textToCopy = h3Element.innerText; // Get text from the <h3> element

      // Use Clipboard API to copy text
      navigator.clipboard.writeText(textToCopy)
        .then(() => {
          // Show the "Text copied!" message
          copyMessage.style.display = "inline";
          
          // Hide the message after 2 seconds
          setTimeout(() => {
            copyMessage.style.display = "none";
          }, 2000);
        })
        .catch(err => {
          console.error("Error copying text: ", err);
        });
    });
  } else {
    console.warn("Copy icon, <h3> element, or copy message element not found.");
  }
});
