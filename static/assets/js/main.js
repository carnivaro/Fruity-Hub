/* ===================================================
   FRUITY HUB
   MAIN JAVASCRIPT
=================================================== */

document.addEventListener("DOMContentLoaded", () => {

    displayProducts();

    loadProductDetails();

    updateCartCount();

    loadCart();

});


/* ===================================================
   DISPLAY PRODUCTS
=================================================== */

function displayProducts() {

    const container = document.getElementById("productContainer");

    if (!container) return;

    container.innerHTML = "";

    products.forEach(product => {

        container.innerHTML += `

        <div class="product-card">

            <img src="${product.image}" alt="${product.name}">

            <div class="product-info">

                <h3>${product.name}</h3>

                <p class="price">

                    ₦${product.price.toLocaleString()} / ${product.unit}

                </p>

                <p class="stock">

                    ${product.stock}

                </p>

                <p class="origin">

                    Jos North Fruit Market

                </p>

                <div class="product-buttons">

                    <button
                        class="details-btn"
                        onclick="viewProduct(${product.id})">

                        View Details

                    </button>

                    <button
                        class="add-btn"
                        onclick="addToCart(${product.id})">

                        Add to Cart

                    </button>

                </div>

            </div>

        </div>

        `;

    });

}

/* ===================================================
   SEARCH PRODUCTS
=================================================== */

const searchInput = document.getElementById("searchInput");

if(searchInput){

    searchInput.addEventListener("keyup", searchProducts);

}

function searchProducts(){

    const keyword =

    searchInput.value.toLowerCase();

    const cards =

    document.querySelectorAll(".product-card");

    cards.forEach(card=>{

        const name =

        card.querySelector("h3")

        .textContent

        .toLowerCase();

        if(name.includes(keyword)){

            card.style.display="block";

        }

        else{

            card.style.display="none";

        }

    });

}

/* ===================================================
   PRODUCT DETAILS PAGE
=================================================== */

function loadProductDetails(){

const container = document.getElementById("productDetails");

if(!container) return;

const id = Number(localStorage.getItem("selectedProduct"));

const product = products.find(item => item.id === id);

if(!product){

container.innerHTML="<h2>Product not found.</h2>";

return;

}

container.innerHTML=`

<div class="details-container">

<div class="details-image">

<img src="${product.image}" alt="${product.name}">

</div>

<div class="details-info">

<h2>${product.name}</h2>

<p class="details-price">

₦${product.price.toLocaleString()} / ${product.unit}

</p>

<p class="details-stock">

${product.stock}

</p>

<p class="details-description">

${product.description}

</p>

<button onclick="addToCart(${product.id})">

Add to Cart

</button>

</div>

</div>

`;

}

/* ==========================================
   DISPLAY LOGGED-IN USER
========================================== */

document.addEventListener("DOMContentLoaded", () => {

    const loginButton = document.querySelector(".login-btn");

    const loggedUser = localStorage.getItem("loggedUser");

    if (loginButton && loggedUser) {

        loginButton.textContent = "Hi, " + loggedUser;

        loginButton.href = "#";

    }

});