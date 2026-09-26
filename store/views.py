import re

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.cache import never_cache
from .models import Product, Cart, CartItem, Order, OrderItem, Profile, ContactMessage, ReturnRequest


def _is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


# --- Test-mode card payment helpers -----------------------------------------
# These simulate a payment gateway sandbox (e.g. Stripe/Paystack test mode).
# No real card data is transmitted or stored - only the last 4 digits are kept.

DECLINED_TEST_CARDS = {
    '4000000000000002': 'Your card was declined.',
    '4000000000009995': 'Your card has insufficient funds.',
    '4000000000000069': 'Your card has expired.',
}


def _luhn_valid(card_number):
    digits = [int(d) for d in card_number]
    checksum = 0
    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


def _simulate_card_charge(card_number, expiry, cvv):
    """Returns (success: bool, message: str). Never touches a real network/gateway."""
    card_number = re.sub(r'[^0-9]', '', card_number or '')
    expiry = (expiry or '').strip()
    cvv = re.sub(r'[^0-9]', '', cvv or '')

    if not card_number or len(card_number) not in (15, 16):
        return False, 'Enter a valid card number (15-16 digits).'
    if not _luhn_valid(card_number):
        return False, 'That card number does not look valid.'
    if not re.match(r'^\d{1,2}\s*[/\-]?\s*\d{2}$', expiry):
        return False, 'Enter the expiry as MM/YY.'
    if len(cvv) not in (3, 4):
        return False, 'Enter a valid CVV.'

    if card_number in DECLINED_TEST_CARDS:
        return False, DECLINED_TEST_CARDS[card_number]

    return True, 'Payment approved.'


def home(request):
    products = Product.objects.filter(available=True).order_by('-date_added')[:8]
    return render(request, 'index.html', {'products': products})


def shop(request):
    products = Product.objects.filter(available=True).order_by('-date_added')
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()

    if query:
        products = products.filter(name__icontains=query)
    if category:
        products = products.filter(category=category)

    categories = Product.objects.filter(available=True).values_list('category', flat=True).distinct()
    return render(request, 'shop.html', {
        'products': products,
        'categories': categories,
        'query': query,
        'selected_category': category,
    })


def about(request):
    return render(request, 'about.html')


def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        message_text = request.POST.get('message', '').strip()

        if not name or not phone or not message_text:
            messages.error(request, 'Please fill in your name, phone number and message.')
            return render(request, 'contact.html', {
                'default_name': name,
                'default_phone': phone,
                'default_message': message_text,
            })

        ContactMessage.objects.create(name=name, phone=phone, message=message_text)

        messages.success(request, 'Thank you for contacting Fruity Hub. We will get back to you soon.')
        return redirect('contact')
    return render(request, 'contact.html')


@never_cache
def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')

        messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')


def register(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not first_name or not last_name or not username or not email or not password:
            messages.error(request, 'Please complete all required fields.')
            return redirect('register')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return redirect('register')

        try:
            validate_password(password)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return redirect('register')

        User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        messages.success(request, 'Account created successfully. You can now log in.')
        return redirect('login')

    return render(request, 'register.html')


def _get_cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    return cart


def _get_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return profile


def _cart_items(request):
    cart = _get_cart(request)
    cart_items = cart.items.select_related('product').filter(product__available=True)
    items = []
    total = 0

    for cart_item in cart_items:
        subtotal = cart_item.subtotal
        total += subtotal
        items.append({'product': cart_item.product, 'quantity': cart_item.quantity, 'subtotal': subtotal})

    return items, total


@never_cache
@login_required(login_url='login')
def cart(request):
    items, total = _cart_items(request)
    return render(request, 'cart.html', {'items': items, 'total': total})


@never_cache
@login_required(login_url='login')
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk, available=True)
    if product.stock <= 0:
        messages.error(request, f'{product.name} is currently out of stock.')
        return redirect('product', pk=product.pk)

    user_cart = _get_cart(request)
    cart_item, created = CartItem.objects.get_or_create(cart=user_cart, product=product)
    if not created:
        cart_item.quantity = min(cart_item.quantity + 1, product.stock)
    else:
        cart_item.quantity = min(1, product.stock)
    cart_item.save()

    messages.success(request, f'{product.name} added to your cart.')
    return redirect(request.POST.get('next') or request.META.get('HTTP_REFERER') or 'shop')


@never_cache
@login_required(login_url='login')
def update_cart(request, pk):
    product = get_object_or_404(Product, pk=pk, available=True)
    quantity = max(0, int(request.POST.get('quantity', 1)))
    user_cart = _get_cart(request)

    removed = quantity == 0
    if removed:
        CartItem.objects.filter(cart=user_cart, product=product).delete()
    else:
        quantity = min(quantity, product.stock)
        CartItem.objects.update_or_create(
            cart=user_cart, product=product, defaults={'quantity': quantity}
        )

    if _is_ajax(request):
        items, total = _cart_items(request)
        return JsonResponse({
            'removed': removed,
            'quantity': 0 if removed else quantity,
            'subtotal': 0 if removed else product.price * quantity,
            'cart_total': total,
            'cart_count': user_cart.item_count,
        })

    return redirect('cart')


@never_cache
@login_required(login_url='login')
def remove_from_cart(request, pk):
    user_cart = _get_cart(request)
    CartItem.objects.filter(cart=user_cart, product_id=pk).delete()

    if _is_ajax(request):
        items, total = _cart_items(request)
        return JsonResponse({
            'cart_total': total,
            'cart_count': user_cart.item_count,
        })

    messages.success(request, 'Item removed from your cart.')
    return redirect('cart')


@never_cache
def cart_count(request):
    if not request.user.is_authenticated:
        return JsonResponse({'cart_count': 0})
    user_cart = _get_cart(request)
    return JsonResponse({'cart_count': user_cart.item_count})


@never_cache
@login_required(login_url='login')
def checkout(request):
    items, total = _cart_items(request)
    if not items:
        messages.warning(request, 'Your cart is empty. Add a fruit before checking out.')
        return redirect('shop')

    profile = _get_profile(request)

    if request.method == 'POST':
        name = request.POST.get('fullname', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        payment_method = request.POST.get('payment_method', 'Cash on Delivery')
        if payment_method not in dict(Order.PAYMENT_METHOD_CHOICES):
            payment_method = 'Cash on Delivery'

        if not name or not phone or not address:
            messages.error(request, 'Please complete your delivery information.')
            return render(request, 'checkout.html', {'items': items, 'total': total, 'profile': profile, 'default_name': name})

        paying_by_card = payment_method == 'Card (Test Mode)'

        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                full_name=name,
                phone=phone,
                address=address,
                payment_method=payment_method,
                payment_status='awaiting_payment' if paying_by_card else 'cod',
                status='pending' if paying_by_card else 'placed',
                total=total,
            )
            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    product_name=item['product'].name,
                    price=item['product'].price,
                    quantity=item['quantity'],
                )
            # Clear the user's cart now that the order has been placed.
            _get_cart(request).items.all().delete()

            # Remember this delivery info as the default for next time.
            profile.phone = phone
            profile.address = address
            profile.save()

        if paying_by_card:
            messages.success(request, 'Order created. Complete payment to confirm it.')
            return redirect('pay_order', pk=order.pk)

        messages.success(request, 'Your order has been placed successfully. Payment will be made on delivery.')
        return redirect('orders')

    default_name = f'{request.user.first_name} {request.user.last_name}'.strip() or request.user.username
    return render(request, 'checkout.html', {
        'items': items,
        'total': total,
        'profile': profile,
        'default_name': default_name,
    })


def product(request, pk):
    product_obj = get_object_or_404(Product, pk=pk, available=True)
    return render(request, 'product.html', {'product': product_obj})


@never_cache
@login_required(login_url='login')
def orders(request):
    user_orders = Order.objects.filter(user=request.user).prefetch_related('items', 'return_requests')
    return render(request, 'orders.html', {'orders': user_orders})


@never_cache
@login_required(login_url='login')
def profile(request):
    profile_obj = _get_profile(request)

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()

        if not first_name or not last_name:
            messages.error(request, 'First name and last name are required.')
            return redirect('profile')

        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.save()

        profile_obj.phone = phone
        profile_obj.address = address
        profile_obj.save()

        messages.success(request, 'Your profile has been updated.')
        return redirect('profile')

    return render(request, 'profile.html', {'profile': profile_obj})


@never_cache
@login_required(login_url='login')
def pay_order(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)

    if order.payment_status == 'paid':
        messages.info(request, 'This order has already been paid for.')
        return redirect('orders')

    if request.method == 'POST':
        card_number = request.POST.get('card_number', '').strip()
        expiry = request.POST.get('expiry', '').strip()
        cvv = request.POST.get('cvv', '').strip()

        success, note = _simulate_card_charge(card_number, expiry, cvv)

        if success:
            order.payment_status = 'paid'
            order.status = 'placed'
            order.card_last4 = re.sub(r'[^0-9]', '', card_number)[-4:]
            order.save()
            messages.success(request, 'Payment approved. Your order has been placed.')
            return redirect('orders')

        order.payment_status = 'failed'
        order.save()
        messages.error(request, note)

    return render(request, 'pay_order.html', {'order': order})


@never_cache
@login_required(login_url='login')
def request_return(request, order_pk):
    order = get_object_or_404(Order, pk=order_pk, user=request.user)

    if order.status != 'delivered':
        messages.error(request, 'You can only report an issue for a delivered order.')
        return redirect('orders')

    if request.method == 'POST':
        reason = request.POST.get('reason', 'damaged')
        description = request.POST.get('description', '').strip()
        photo = request.FILES.get('photo')

        if reason not in dict(ReturnRequest.REASON_CHOICES):
            reason = 'other'

        if not description:
            messages.error(request, 'Please describe the issue with your order.')
            return render(request, 'return_request.html', {'order': order})

        ReturnRequest.objects.create(
            order=order,
            user=request.user,
            reason=reason,
            description=description,
            photo=photo,
        )
        messages.success(request, 'Thanks for letting us know. Our team will review it shortly.')
        return redirect('orders')

    return render(request, 'return_request.html', {'order': order})


def logout_user(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')
