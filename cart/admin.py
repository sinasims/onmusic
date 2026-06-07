from django.contrib import admin
from .models import Cart, CartItem, Order, Coupon


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['title', 'artist', 'price', 'quantity']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_items', 'total', 'updated_at']
    inlines = [CartItemInline]
    search_fields = ['user__phone']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total', 'status', 'created_at']
    list_editable = ['status']
    list_filter = ['status']
    search_fields = ['user__phone', 'user__email']


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'value', 'max_uses', 'used_count', 'is_active', 'expires_at']
    list_editable = ['is_active']
