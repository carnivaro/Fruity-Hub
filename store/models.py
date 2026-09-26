from django.conf import settings
from django.db import models


class Product(models.Model):
    CATEGORY_CHOICES = [
        ("Citrus", "Citrus"),
        ("Tropical", "Tropical"),
        ("Berry", "Berry"),
        ("Melon", "Melon"),
        ("Other", "Other"),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/")
    description = models.TextField(blank=True)
    available = models.BooleanField(default=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Cart(models.Model):
    """One persistent cart per user, replacing the old session-based cart."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    @property
    def total(self):
        return sum((item.subtotal for item in self.items.all()), 0)

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("cart", "product")

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def subtotal(self):
        return self.product.price * self.quantity


class Profile(models.Model):
    """Stores default delivery info so returning users don't retype it every order."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user.username}"


class ContactMessage(models.Model):
    """A message submitted through the public Contact Us page."""

    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.created_at:%Y-%m-%d})"


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("placed", "Placed"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("Cash on Delivery", "Cash on Delivery"),
        ("Card (Test Mode)", "Card (Test Mode)"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("cod", "Pay on delivery"),
        ("awaiting_payment", "Awaiting payment"),
        ("paid", "Paid"),
        ("failed", "Payment failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders"
    )
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30)
    address = models.TextField()
    payment_method = models.CharField(
        max_length=50, choices=PAYMENT_METHOD_CHOICES, default="Cash on Delivery"
    )
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="cod"
    )
    card_last4 = models.CharField(max_length=4, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="placed")
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    # Kept nullable + SET_NULL so an order stays intact even if a product is later deleted.
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

    @property
    def subtotal(self):
        return self.price * self.quantity


class ReturnRequest(models.Model):
    """A customer-reported issue with a delivered order (e.g. damage in transit)."""

    REASON_CHOICES = [
        ("damaged", "Damaged during delivery"),
        ("wrong_item", "Wrong item received"),
        ("missing_item", "Item(s) missing from order"),
        ("quality_issue", "Poor product quality"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("submitted", "Submitted"),
        ("under_review", "Under review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("resolved", "Resolved"),
    ]

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="return_requests"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="return_requests"
    )
    reason = models.CharField(max_length=20, choices=REASON_CHOICES, default="damaged")
    description = models.TextField()
    photo = models.ImageField(upload_to="returns/", blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="submitted")
    admin_response = models.TextField(
        blank=True, help_text="Visible to the customer once added."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Return #{self.pk} for Order #{self.order_id} ({self.get_status_display()})"