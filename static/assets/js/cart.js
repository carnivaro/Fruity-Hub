/* ===================================================
   FRUITY HUB
   CART — instant quantity / remove / badge updates
   Talks to the real Django session cart via fetch()
=================================================== */

function getCookie(name) {
    let value = null;
    if (document.cookie) {
        document.cookie.split(';').forEach(function (part) {
            part = part.trim();
            if (part.startsWith(name + '=')) {
                value = decodeURIComponent(part.substring(name.length + 1));
            }
        });
    }
    return value;
}

const csrftoken = getCookie('csrftoken');

/* ==========================
   TOAST (matches base.html markup)
========================== */

function toastIconClass(type) {
    if (type === 'error') return 'fa-circle-exclamation';
    if (type === 'warning') return 'fa-triangle-exclamation';
    return 'fa-circle-check';
}

function getToastContainer() {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        container.setAttribute('aria-live', 'polite');
        container.setAttribute('aria-atomic', 'true');
        document.body.insertBefore(container, document.body.firstChild);
    }
    return container;
}

function dismissToast(toast) {
    if (!toast || !toast.isConnected) return;
    toast.classList.add('toast-hide');
    setTimeout(function () {
        if (toast.isConnected) toast.remove();
    }, 250);
}

function showToast(message, type) {
    const container = getToastContainer();

    const toast = document.createElement('div');
    toast.className = 'toast ' + (type || 'success');

    toast.innerHTML =
        '<i class="toast-icon fa-solid ' + toastIconClass(type) + '"></i>' +
        '<span class="toast-text"></span>' +
        '<button class="toast-close" type="button" aria-label="Close notification">&times;</button>';

    toast.querySelector('.toast-text').textContent = message;
    container.appendChild(toast);

    toast.querySelector('.toast-close').addEventListener('click', function () {
        dismissToast(toast);
    });

    setTimeout(function () {
        dismissToast(toast);
    }, 4000);
}

/* ==========================
   BADGE
========================== */

function setCartBadge(count) {
    const badge = document.getElementById('cartCount');
    if (!badge) return;
    badge.textContent = count;
    badge.style.display = count > 0 ? 'inline-flex' : 'none';
}

function refreshCartBadge() {
    const badge = document.getElementById('cartCount');
    if (!badge || !badge.dataset.countUrl) return;

    fetch(badge.dataset.countUrl)
        .then(function (res) { return res.json(); })
        .then(function (data) { setCartBadge(data.cart_count); })
        .catch(function () {});
}

/* ==========================
   HELPERS
========================== */

function formatNaira(amount) {
    return '₦' + Number(amount).toLocaleString();
}

function updateGrandTotal(total) {
    document.querySelectorAll('.js-cart-total').forEach(function (el) {
        el.textContent = formatNaira(total);
    });
}

function setRowBusy(row, busy) {
    row.classList.toggle('cart-row-busy', busy);
    row.querySelectorAll('button').forEach(function (btn) {
        btn.disabled = busy;
    });
}

function showEmptyCart() {
    const layout = document.querySelector('.cart-layout');
    if (!layout) return;

    const shopUrl = document.body.dataset.shopUrl || '/shop/';

    layout.outerHTML =
        '<div class="empty-state">' +
        '<i class="fa-solid fa-basket-shopping"></i>' +
        '<h2>Your cart is empty</h2>' +
        '<p>Fresh fruits are waiting for you.</p>' +
        '<a class="btn btn-primary" href="' + shopUrl + '">Start Shopping</a>' +
        '</div>';
}

function removeRow(row, cartTotal, cartCount) {
    row.classList.add('cart-row-removing');
    setTimeout(function () {
        row.remove();
        updateGrandTotal(cartTotal);
        setCartBadge(cartCount);

        const cartList = document.querySelector('.cart-list');
        if (cartList && cartList.children.length === 0) {
            showEmptyCart();
        }
    }, 200);
}

/* ==========================
   CART ACTIONS
========================== */

function updateQuantity(row, newQuantity) {
    setRowBusy(row, true);

    fetch(row.dataset.updateUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrftoken,
        },
        body: 'quantity=' + encodeURIComponent(newQuantity),
    })
        .then(function (res) { return res.json(); })
        .then(function (data) {
            if (data.removed) {
                removeRow(row, data.cart_total, data.cart_count);
                return;
            }
            row.querySelector('.qty-value').textContent = data.quantity;
            row.querySelector('.cart-subtotal').textContent = formatNaira(data.subtotal);
            updateGrandTotal(data.cart_total);
            setCartBadge(data.cart_count);
            setRowBusy(row, false);
        })
        .catch(function () {
            showToast('Could not update quantity. Please try again.', 'error');
            setRowBusy(row, false);
        });
}

function removeItem(row) {
    setRowBusy(row, true);

    fetch(row.dataset.removeUrl, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrftoken,
        },
    })
        .then(function (res) { return res.json(); })
        .then(function (data) {
            removeRow(row, data.cart_total, data.cart_count);
            showToast('Item removed from your cart.', 'warning');
        })
        .catch(function () {
            showToast('Could not remove item. Please try again.', 'error');
            setRowBusy(row, false);
        });
}

/* ==========================
   INITIALIZE
========================== */

document.addEventListener('DOMContentLoaded', function () {

    refreshCartBadge();

    document.querySelectorAll('.cart-row').forEach(function (row) {
        const qtyValueEl = row.querySelector('.qty-value');
        const stock = parseInt(row.dataset.stock, 10);

        const increaseBtn = row.querySelector('.qty-increase');
        const decreaseBtn = row.querySelector('.qty-decrease');
        const removeBtn = row.querySelector('.remove-btn');

        if (increaseBtn) {
            increaseBtn.addEventListener('click', function () {
                const current = parseInt(qtyValueEl.textContent, 10);
                if (current >= stock) {
                    showToast('No more stock available for this item.', 'warning');
                    return;
                }
                updateQuantity(row, current + 1);
            });
        }

        if (decreaseBtn) {
            decreaseBtn.addEventListener('click', function () {
                const current = parseInt(qtyValueEl.textContent, 10);
                if (current <= 1) return;
                updateQuantity(row, current - 1);
            });
        }

        if (removeBtn) {
            removeBtn.addEventListener('click', function () {
                removeItem(row);
            });
        }
    });

});
