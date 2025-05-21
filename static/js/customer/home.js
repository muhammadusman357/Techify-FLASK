document.addEventListener('DOMContentLoaded', () => {
    // Theme toggler script
    const themeToggler = document.querySelector(".theme-toggler");
    if (themeToggler) {
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

        themeToggler.addEventListener('click', () => {
            const isDarkTheme = document.body.classList.toggle('dark-theme-variables');
            themeToggler.querySelector('span:nth-child(1)').classList.toggle('active');
            themeToggler.querySelector('span:nth-child(2)').classList.toggle('active');
            localStorage.setItem('theme', isDarkTheme ? 'dark' : 'light');
        });
    }

    // Product image interaction script
    const productImageContainer = document.querySelector('.product-image');
    if (productImageContainer) {
        const productImage = productImageContainer.querySelector('img');
        if (productImage) {
            productImageContainer.addEventListener('mousemove', (event) => {
                const rect = productImageContainer.getBoundingClientRect();
                const x = event.clientX - rect.left;
                const y = event.clientY - rect.top;
                const moveX = (x - rect.width / 2) * 0.05;
                const moveY = (y - rect.height / 2) * 0.05;
                productImage.style.transform = `translate(${moveX}px, ${moveY}px)`;
            });

            productImageContainer.addEventListener('mouseleave', () => {
                productImage.style.transform = 'translate(0, 0)';
            });
        }
    }

    /*// Active category script
    function setActiveCategory(category) {
        const categories = document.querySelectorAll('.nav a');
        categories.forEach(cat => {
            if (cat.textContent.trim() === category) {
                cat.classList.add('active');
            } else {
                cat.classList.remove('active');
            }
        });
    }*/


    let nextButton = document.getElementById('next');
    let prevButton = document.getElementById('prev');
    let carousel = document.querySelector('.carousel');
    let listHTML = document.querySelector('.carousel .list');
    let seeMoreButtons = document.querySelectorAll('.seeMore');
    let backButton = document.getElementById('back');
    
    nextButton.onclick = function() {
        showSlider('next');
    };
    
    prevButton.onclick = function() {
        showSlider('prev');
    };
    
    let unAcceppClick;
    
    const showSlider = (type) => {
        nextButton.style.pointerEvents = 'none';
        prevButton.style.pointerEvents = 'none';
    
        carousel.classList.remove('next', 'prev');
        let items = document.querySelectorAll('.carousel .list .item');
        if(type === 'next') {
            listHTML.appendChild(items[0]);
            carousel.classList.add('next');
        } else {
            listHTML.prepend(items[items.length - 1]);
            carousel.classList.add('prev');
        }
    
        clearTimeout(unAcceppClick);
        unAcceppClick = setTimeout(() => {
            nextButton.style.pointerEvents = 'auto';
            prevButton.style.pointerEvents = 'auto';
        }, 2000);
    };
    
    seeMoreButtons.forEach((button) => {
        button.onclick = function() {
            carousel.classList.remove('next', 'prev');
            carousel.classList.add('showDetail');
        };
    });
    
    backButton.onclick = function() {
        carousel.classList.remove('showDetail');
    };

    

    

    // Form submission validation
    document.getElementById("forms").addEventListener("submit", function(event) {
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




document.addEventListener('DOMContentLoaded', () => {
    const addToCartButtons = document.querySelectorAll('.add-to-cart');
    const confirmButtons = document.querySelectorAll('.confirm-btn');

    addToCartButtons.forEach(button => {
        button.addEventListener('click', () => {
            const productId = button.getAttribute('data-id');
            const popup = document.getElementById(`popup-${productId}`);
            popup.style.display = 'block';
        });
    });

    confirmButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const productId = button.getAttribute('data-id');
            const quantityInput = document.getElementById(`quantity-input-${productId}`);
            const quantity = parseInt(quantityInput.value) || 1;

            // Hide the popup
            const popup = document.getElementById(`popup-${productId}`);
            popup.style.display = 'none';

            // Perform the AJAX call to add the product to the cart
            try {
                const response = await fetch('/add_to_cart', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ product_id: productId, quantity })
                });

                const result = await response.json();
                if (response.ok) {
                    //alert(result.message || 'Product added to cart successfully!');
                    // Optionally update the cart UI dynamically
                    updateCartUI(result.items, result.subtotal);
                    fetchCartData();
                    toggleCart();
                } else {
                    alert(result.message || 'Failed to add product to cart.');
                }
            } catch (error) {
                console.error('Error adding to cart:', error);
                alert('An error occurred while adding the product to the cart.');
            }
        });
    });

    // Quantity controls
    document.querySelectorAll('.decrease-btn').forEach(button => {
        button.addEventListener('click', () => {
            const productId = button.getAttribute('data-id');
            const quantityInput = document.getElementById(`quantity-input-${productId}`);
            const currentQuantity = parseInt(quantityInput.value) || 1;
            if (currentQuantity > 1) {
                quantityInput.value = currentQuantity - 1;
            }
        });
    });

    document.querySelectorAll('.increase-btn').forEach(button => {
        button.addEventListener('click', () => {
            const productId = button.getAttribute('data-id');
            const quantityInput = document.getElementById(`quantity-input-${productId}`);
            const currentQuantity = parseInt(quantityInput.value) || 1;
            quantityInput.value = currentQuantity + 1;
        });
    });
});



function toggleCart() {
    const cart = document.querySelector('.cart-container');
    const overlay = document.querySelector('.cart-overlay');
    const submenus = document.querySelectorAll('.cart-submenu');

    // Toggle cart visibility
    cart.classList.toggle('active');
    overlay.classList.toggle('active');

    // If the cart is being closed, also close all submenus
    if (!cart.classList.contains('active')) {
        submenus.forEach(submenu => submenu.classList.remove('active'));
    }
}




function toggleSubmenu(submenuId) {
    const submenu = document.getElementById(submenuId);
    submenu.classList.toggle('active');
}

function closeAll() {
    document.querySelector('.cart-container').classList.remove('active');
    document.querySelectorAll('.cart-submenu').forEach(submenu => submenu.classList.remove('active'));
    document.querySelector('.cart-overlay').classList.remove('active');
}

/*function updateQuantity(button, change) {
    const quantitySpan = button.parentElement.querySelector('span');
    let quantity = parseInt(quantitySpan.textContent);
    quantity = Math.max(1, quantity + change); // Prevent quantity from going below 1
    quantitySpan.textContent = quantity;
}*/

let profileDropdownList = document.querySelector(".profile-dropdown-list");
let btn = document.querySelector(".profile-dropdown-btn");

let classList = profileDropdownList.classList;

const toggle = () => classList.toggle("active");

window.addEventListener("click", function (e) {
  if (!btn.contains(e.target)) classList.remove("active");
});


        // Select all toggle icons
const togglePasswordIcons = document.querySelectorAll('.password-icon');

// Add an event listener to each toggle icon
togglePasswordIcons.forEach(icon => {
    icon.addEventListener('click', function () {
        // Find the associated password input using sibling traversal
        const passwordInput = this.previousElementSibling;
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);

        // Toggle the eye slash icon
        this.classList.toggle('fa-eye-slash');
    });
});


    const passwordInput2 = document.getElementById('password');
        const confpasswordInput2 = document.getElementById('confpassword');


        

        // Password confirmation validation
        confpasswordInput2.addEventListener('input', () => {
            const confirmMessage = document.getElementById('confirmMessage');
            if (passwordInput2.value !== confpasswordInput2.value) {
                confirmMessage.textContent = "* Passwords do not match.";
                confirmMessage.style.color = 'red';
                confpasswordInput2.classList.add('invalid');
            } else {
                confirmMessage.textContent = "✔ Passwords match.";
                confirmMessage.style.color = 'green';
                confpasswordInput2.classList.remove('invalid');
            }
        });


/*document.addEventListener('DOMContentLoaded', function () {
    // Function to fetch and display products
    async function fetchBestSellers(categoryName) {
        try {
            // Fetch best-selling products from the backend
            const response = await fetch(`/best_sellers/${categoryName}`);
            const data = await response.json();

            if (data.success) {
                displayProducts(data.products);
            } else {
                console.error(data.message);
            }
        } catch (error) {
            console.error("Error fetching best-selling products:", error);
        }
    }

    // Function to display products
    function displayProducts(products) {
        const productsDisplay = document.querySelector('.products-display');
        productsDisplay.innerHTML = ''; // Clear current products

        if (products.length === 0) {
            productsDisplay.innerHTML = '<div>No products found for this category.</div>';
            return;
        }

        products.forEach(product => {
            const productCard = `
                <div class="product">
                    <div class="product-header">
                        <h2>BEST SELLER</h2>
                        <div class="icons">
                            <button><span class="material-symbols-outlined gr">favorite</span></button>
                            <button><span class="material-symbols-outlined">cached</span></button>
                            <button><a href="/product_details/${product.id}">
                                <span class="material-symbols-outlined gr">fullscreen</span></a></button>
                        </div>
                    </div>
                    <div class="image-container">
                        <a href="/product_details/${product.id}">
                            <img alt="image-1" class="main-img" src="${product.image_urls[0]}" />
                            ${product.image_urls[1] ? `<img alt="image-2" class="hover-img" src="${product.image_urls[1]}" />` : ''}
                        </a>
                    </div>
                    <div class="discount">SAVE 58%</div>
                    <a href="/product_details/${product.id}">
                        <h3>${product.name}</h3>
                    </a>
                    <div class="reviews">
                        ${renderRating(product.avg_rating)}
                    </div>
                    <div class="price-stock">
                        <div class="price">PKR ${product.price}</div>
                        ${product.stock > 0 ? `
                            <div class="stock-in">In Stock</div>
                            <a href="javascript:void(0);">
                                <div class="stock-add add-to-cart" data-id="${product.id}">Add To Cart</div>
                            </a>` : `
                            <div class="stock-out">Out Of Stock</div>`}
                    </div>
                </div>
            `;
            productsDisplay.innerHTML += productCard;
        });
    }

    // Function to render rating stars
    function renderRating(avgRating) {
        if (!avgRating) return `<span>No Reviews</span>`;

        const fullStars = Math.floor(avgRating);
        const halfStar = avgRating - fullStars >= 0.5 ? 1 : 0;
        const emptyStars = 5 - fullStars - halfStar;

        return `
            ${'&#9733;'.repeat(fullStars)}
            ${halfStar ? '&#9732;' : ''}
            ${'&#9734;'.repeat(emptyStars)}
            <span>(${avgRating} / 5)</span>
        `;
    }

    // Attach click event listeners to navbar links
    const navLinks = document.querySelectorAll('.nav a');
    navLinks.forEach(link => {
        link.addEventListener('click', function () {
            const categoryName = this.textContent.trim().toLowerCase();
            setActiveCategory(categoryName); // Highlight active category
            fetchBestSellers(categoryName); // Fetch and display products
        });
    });

    // Highlight active category
    function setActiveCategory(categoryName) {
        navLinks.forEach(link => link.classList.remove('active'));
        const activeLink = Array.from(navLinks).find(link => link.textContent.trim().toLowerCase() === categoryName);
        if (activeLink) activeLink.classList.add('active');
    }

});*/



            
  
            
        