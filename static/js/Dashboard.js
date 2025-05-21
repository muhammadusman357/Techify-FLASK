const sideMenu = document.querySelector("aside");
const menuBtn = document.querySelector("#menu-btn");
const closeBtn = document.querySelector("#close-btn");
let subMenu =   document.getElementById("subMenu");
// Elements
const themeToggler = document.querySelector(".theme-toggler");

// Check and apply saved theme preference on page load
const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'dark') {
    document.body.classList.add('dark-theme-variables');
    themeToggler.querySelector('span:nth-child(1)').classList.remove('active');
    themeToggler.querySelector('span:nth-child(2)').classList.add('active');
} else {
    document.body.classList.remove('dark-theme-variables');
    themeToggler.querySelector('span:nth-child(1)').classList.add('active');
    themeToggler.querySelector('span:nth-child(2)').classList.remove('active');
}

// Toggle theme
const toggleTheme = () => {
    const isDarkTheme = document.body.classList.toggle('dark-theme-variables');
    themeToggler.querySelector('span:nth-child(1)').classList.toggle('active');
    themeToggler.querySelector('span:nth-child(2)').classList.toggle('active');

    // Save the theme preference to localStorage
    localStorage.setItem('theme', isDarkTheme ? 'dark' : 'light');
};

// Event listener for theme toggling
themeToggler.addEventListener('click', toggleTheme);



function toggleMenu() {
    const subMenu = document.getElementById('subMenu');
    subMenu.classList.toggle('show');
}


// Show sidebar
menuBtn.addEventListener('click', () => {
    sideMenu.style.display = 'block';
});

// Close sidebar
closeBtn.addEventListener('click', () => {
    sideMenu.style.display = 'none';
});


// Chart options
const commonChartOptions = {
    scales: {
        x: { display: false },
        y: { display: false }
    },
    plugins: {
        legend: { display: false }
    }
};

// Initialize line chart
const lineChartElement = document.getElementById('myChart');
if (lineChartElement) {
    const myChart = new Chart(lineChartElement.getContext('2d'), {
        type: 'line',
        data: {
            labels: ['Point 1', 'Point 2', 'Point 3', 'Point 4', 'Point 5', 'Point 6'],
            datasets: [{
                label: 'Sample Data',
                data: [12, 19, 3, 5, 2, 3],
                borderColor: '#4285f4', // Blue line color
                borderWidth: 2,
                fill: false
            }]
        },
        options: {
            ...commonChartOptions,
            elements: {
                point: { radius: 0 } // Remove points on the line
            }
        }
    });
}

// Initialize bar chart
const barChartElement = document.getElementById('barChart');
if (barChartElement) {
    const barChart = new Chart(barChartElement.getContext('2d'), {
        type: 'bar',
        data: {
            labels: Array(30).fill(''), // Empty labels
            datasets: [{
                label: 'Sample Data',
                data: [12, 19, 3, 5, 2, 3, 10, 15, 7, 8, 6, 13, 9, 4, 18, 14, 11, 16, 8, 9, 7, 12, 10, 13, 9, 11, 15, 7, 8, 5],
                backgroundColor: '#4285f4', // Blue color for the bars
                borderWidth: 0,
                barPercentage: 0.8,
                categoryPercentage: 1.0
            }]
        },
        options: commonChartOptions
    });
}

function previewImages(event) {
    const files = event.target.files;
    const imagePreview = document.getElementById('imagePreview');

    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const reader = new FileReader();
        reader.onload = function(e) {
            const div = document.createElement('div');
            const img = document.createElement('img');
            img.src = e.target.result;
            img.alt = file.name;
            const span = document.createElement('span');
            span.className = 'remove-image';
            span.innerHTML = '×';
            span.onclick = function() {
                div.remove();
            };
            div.appendChild(img);
            div.appendChild(span);
            imagePreview.appendChild(div);
        };
        reader.readAsDataURL(file);
    }
}




    // Ensure the DOM is fully loaded before running this script
    window.onload = function() {
        // Function to show the popup
        function showPopup(description) {
            document.getElementById('full-description').innerText = description;
            document.querySelector('.popup').style.display = 'block';
            document.querySelector('.overlay').style.display = 'block';
        }

        // Function to close the popup
        function closePopup() {
            document.querySelector('.popup').style.display = 'none';
            document.querySelector('.overlay').style.display = 'none';
        }

        // Add event listener to the overlay to close the popup when clicked
        document.querySelector('.overlay').addEventListener('click', closePopup);

        // Add event listener to the close button to close the popup
        document.querySelector('.close-btn').addEventListener('click', closePopup);

        // Add event listeners to all "show more" buttons to display the popup with the correct description
        document.querySelectorAll('.show-more').forEach(function(element) {
            element.addEventListener('click', function() {
                const description = this.getAttribute('data-description');
                showPopup(description);
            });
        });
    };

    function toggleDropdown(event) {
        // Find the dropdown menu element
        const dropdownMenu = event.target.closest('.dropdown').querySelector('.dropdown-menu');
        dropdownMenu.classList.toggle('show'); // Toggle the "show" class
      }
      
      // Close dropdown if clicked outside
      window.onclick = function(event) {
        if (!event.target.matches('.material-symbols-outlined')) {
          var dropdowns = document.getElementsByClassName('dropdown-menu');
          for (var i = 0; i < dropdowns.length; i++) {
            var openDropdown = dropdowns[i];
            if (openDropdown.classList.contains('show')) {
              openDropdown.classList.remove('show');
            }
          }
        }
      };


      document.querySelector('.search-products input').addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const rows = document.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const productName = row.querySelector('td:nth-child(3)').textContent.toLowerCase();
            row.style.display = productName.includes(searchTerm) ? '' : 'none';
        });
    });

    document.querySelectorAll('.dropdown-item.delete').forEach(item => {
        item.addEventListener('click', function(event) {
            event.preventDefault();
            if (confirm("Are you sure you want to delete this product?")) {
                // Proceed with deletion logic
            }
        });
    });  
    

    function removeImage(imageId, checkbox) {
        var imageDiv = document.getElementById('image-' + imageId);
    
        if (imageDiv) {
            // Hide the image div
            imageDiv.style.display = 'none';
    
            // If the checkbox is checked, create a hidden input to remove the image
            if (checkbox.checked) {
                var input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'remove_image[]';
                input.value = imageId;
                document.querySelector('form').appendChild(input);
            }
        }
    }


    function handleImageClick(imageUrl) {
         // Replace with your base URL

    
        document.getElementById('popupImage').src = imageUrl; // Set the image source
        document.getElementById('imagePopup').style.display = 'block'; // Show the popup
        document.getElementById('overlay2').style.display = 'block'; // Show the overlay
    }
    
    function closeMyPopup() {
        document.getElementById('imagePopup').style.display = 'none'; // Hide the popup
        document.getElementById('overlay2').style.display = 'none'; // Hide the overlay
    }

    // JavaScript code for pagination
const pagination = document.querySelector('.pagination');
pagination.addEventListener('click', function(event) {
    event.preventDefault();
    const page = event.target.getAttribute('href').split('=')[1];
    if (page) {
        // Load products for the selected page
        loadProducts(page);
    }
});

function loadProducts(page) {
    // Make an AJAX request to load products for the selected page
    // Update the table with the new data
}

function goToPage(page) {

    window.location.href = `/products?page=${page}`; 

}
    
function showPopup1(imageUrl, name, type) {
    // Log the imageUrl and name to debug
    console.log("Image URL passed to showPopup: ", imageUrl);
    console.log("Name passed to showPopup: ", name);
    console.log("Type passed to showPopup: ", type);

    // Set the popup image source
    document.getElementById('popupImage').src = imageUrl; // Set the correct image source
    document.getElementById('popupUsername').textContent = name; // Set the name

    // Optionally change popup title or other content based on type
    if (type === 'product') {
        // Do something specific for products if needed
        console.log("Showing product popup");
    } else if (type === 'admin') {
        // Do something specific for admins if needed
        console.log("Showing admin popup");
    }

    document.getElementById('popup1').style.display = 'flex'; // Show the popup
    document.querySelector('.overlay').style.display = 'block'; // Show the overlay
}

function hidePopup() {
    document.getElementById('popup1').style.display = 'none'; // Hide the popup
    document.querySelector('.overlay').style.display = 'none'; // Hide the overlay
}



function checkPasswordStrength() {
    const password = document.getElementById("password").value;
    const strengthBar = document.getElementById("strengthBar");
    const strengthLabel = document.getElementById("strengthLabel");

    let strength = 0;

    // Check length conditions
    const minLength = 8;
    const maxLength = 16;

    const hasMinLength = password.length >= minLength;
    const hasMaxLength = password.length <= maxLength;
    const hasUpperCase = /[A-Z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
    const hasSpecialChar = /[\W_]/.test(password);

    // Evaluate strength
    if (hasMinLength) strength++;
    if (hasMaxLength) strength++;
    if (hasUpperCase) strength++;
    if (hasNumber) strength++;
    if (hasSpecialChar) strength++;

    // Reset the strength bar and label
    strengthBar.style.width = '0';
    strengthLabel.textContent = "";
    strengthBar.style.backgroundColor = ""; 

    // Determine strength and update UI
    // Ensure that all required conditions are met for maximum strength
    if (strength >= 4) {
        strengthBar.style.backgroundColor = "green";
        strengthLabel.textContent = "Strong Password";
    } else if (strength === 3) {
        strengthBar.style.backgroundColor = "yellow";
        strengthLabel.textContent = "Moderate Password";
    } else if (strength === 2) {
        strengthBar.style.backgroundColor = "orange";
        strengthLabel.textContent = "Normal Password";
    } else {
        strengthBar.style.backgroundColor = "red";
        strengthLabel.textContent = "Weak Password";
    }

    // Update the strength bar width based on calculated strength
    strengthBar.style.width = (strength * 25) + '%'; // Adjust percentage based on strength

    // Update visual indicators for individual requirements
    // Clear all indicators first
    const indicators = [
        { id: "capital", condition: hasUpperCase },
        { id: "special-char", condition: hasSpecialChar },
        { id: "number", condition: hasNumber },
        { id: "more-than-8", condition: hasMinLength }
    ];

    indicators.forEach(({ id, condition }) => {
        const tick = document.querySelector(`#${id} i:nth-child(2)`); // Tick icon
        const cross = document.querySelector(`#${id} i:nth-child(1)`); // Cross icon
        
        if (condition) {
            tick.style.opacity = "1";   // Show tick
            cross.style.opacity = "0";   // Hide cross
        } else {
            tick.style.opacity = "0";    // Hide tick
            cross.style.opacity = "1";    // Show cross
        }
    });
}




function comparePasswords() {
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confpassword").value;
    const confirmMessage = document.getElementById("confirmMessage");
    
    if (password === confirmPassword) {
        confirmMessage.textContent = "";
    } else {
        confirmMessage.textContent = "* Passwords do not match.";
    }
}








