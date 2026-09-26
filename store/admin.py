from django.contrib import admin
from .models import Product, Cart, CartItem, Order, OrderItem, Profile, ContactMessage, ReturnRequest


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'price', 'quantity')
    can_delete = False


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'item_count', 'total', 'updated_at')
    inlines = [CartItemInline]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'full_name', 'phone', 'short_address', 'status',
        'payment_method', 'payment_status', 'total', 'user', 'created_at',
    )
    list_display_links = ('id', 'full_name')
    list_editable = ('status',)  # change status right from the list, no need to open each order
    list_filter = ('status', 'payment_method', 'payment_status', 'created_at')
    search_fields = ('full_name', 'phone', 'address', 'user__username')
    date_hierarchy = 'created_at'  # adds a date drill-down at the top of the list
    ordering = ('-created_at',)
    readonly_fields = ('user', 'total', 'created_at', 'payment_status', 'card_last4')
    inlines = [OrderItemInline]
    actions = ['mark_as_pending', 'mark_as_placed', 'mark_as_delivered', 'mark_as_cancelled']

    fieldsets = (
        ('Customer', {'fields': ('user', 'full_name', 'phone', 'address')}),
        ('Order', {'fields': ('status', 'total', 'created_at')}),
        ('Payment', {'fields': ('payment_method', 'payment_status', 'card_last4')}),
    )

    @admin.display(description='Address')
    def short_address(self, obj):
        return (obj.address[:40] + '…') if len(obj.address) > 40 else obj.address

    @admin.action(description='Mark selected orders as Pending')
    def mark_as_pending(self, request, queryset):
        updated = queryset.update(status='pending')
        self.message_user(request, f'{updated} order(s) marked as Pending.')

    @admin.action(description='Mark selected orders as Placed')
    def mark_as_placed(self, request, queryset):
        updated = queryset.update(status='placed')
        self.message_user(request, f'{updated} order(s) marked as Placed.')

    @admin.action(description='Mark selected orders as Delivered')
    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status='delivered')
        self.message_user(request, f'{updated} order(s) marked as Delivered.')

    @admin.action(description='Mark selected orders as Cancelled')
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} order(s) marked as Cancelled.')


admin.site.register(Product)
admin.site.register(Profile, list_display=('user', 'phone', 'address', 'updated_at'), search_fields=('user__username', 'phone', 'address'))


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'short_message', 'is_read', 'created_at')
    list_display_links = ('name',)
    list_editable = ('is_read',)  # mark as read/unread right from the list
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'phone', 'message')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('name', 'phone', 'message', 'created_at')

    @admin.display(description='Message')
    def short_message(self, obj):
        return (obj.message[:60] + '…') if len(obj.message) > 60 else obj.message


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'user', 'reason', 'status', 'created_at')
    list_display_links = ('id', 'order')
    list_editable = ('status',)  # move a report through review right from the list
    list_filter = ('status', 'reason', 'created_at')
    search_fields = ('order__id', 'user__username', 'description')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('order', 'user', 'reason', 'description', 'photo', 'created_at')
    actions = ['mark_under_review', 'mark_approved', 'mark_rejected', 'mark_resolved']

    fieldsets = (
        ('Report', {'fields': ('order', 'user', 'reason', 'description', 'photo', 'created_at')}),
        ('Resolution', {'fields': ('status', 'admin_response')}),
    )

    @admin.action(description='Mark selected reports as Under review')
    def mark_under_review(self, request, queryset):
        updated = queryset.update(status='under_review')
        self.message_user(request, f'{updated} report(s) marked as Under review.')

    @admin.action(description='Mark selected reports as Approved')
    def mark_approved(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} report(s) marked as Approved.')

    @admin.action(description='Mark selected reports as Rejected')
    def mark_rejected(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} report(s) marked as Rejected.')

    @admin.action(description='Mark selected reports as Resolved')
    def mark_resolved(self, request, queryset):
        updated = queryset.update(status='resolved')
        self.message_user(request, f'{updated} report(s) marked as Resolved.')