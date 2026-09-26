/* ===================================================
   CHECKOUT
=================================================== */

/* ==========================================
   LOGIN CHECK
========================================== */

if (localStorage.getItem("loggedIn") !== "true") {

    alert("Please login before proceeding to checkout.");

    window.location.href = "login.html";

}

const checkoutForm = document.getElementById("checkoutForm");

if (checkoutForm) {
    checkoutForm.addEventListener("submit", placeOrder);
}

/* ===========================================
   LOAD ORDER SUMMARY
=========================================== */

loadCheckoutSummary();

function loadCheckoutSummary(){

    const cart = JSON.parse(localStorage.getItem("cart")) || [];

    const container = document.getElementById("checkoutItems");

    const total = document.getElementById("checkoutTotal");

    if(!container || !total) return;

    let grandTotal = 0;

    container.innerHTML = "";

    cart.forEach(item=>{

        const subtotal = item.price * item.quantity;

        grandTotal += subtotal;

        container.innerHTML += `

        <div class="checkout-item">

            <span>

                ${item.name} × ${item.quantity}

            </span>

            <span>

                ₦${subtotal.toLocaleString()}

            </span>

        </div>

        `;

    });

    total.textContent =

    "₦" + grandTotal.toLocaleString();

}

function placeOrder(event) {

    event.preventDefault();

    const fullName = document.getElementById("fullname").value.trim();
    const phone = document.getElementById("phone").value.trim();
    const address = document.getElementById("address").value.trim();

    const cart = JSON.parse(localStorage.getItem("cart")) || [];

    if (cart.length === 0) {
        showToast("Your cart is empty.","warning");
        return;
    }

    const order = {
        customer: fullName,
        phone: phone,
        address: address,
        items: cart,
        date: new Date().toLocaleString()
    };

    localStorage.setItem("latestOrder", JSON.stringify(order));

    localStorage.removeItem("cart");

    showToast("Order placed successfully.","success");

setTimeout(()=>{

window.location.href="index.html";

},1500);

    window.location.href = "index.html";
}